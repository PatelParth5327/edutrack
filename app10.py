from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import re, time

app = Flask(__name__)
CORS(app)

PORTAL_BASE = "http://202.129.240.148:8080/GIS"

def get_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

@app.route("/api/ping")
def ping():
    return jsonify({"status": "EduTrack backend running"})

@app.route("/api/login", methods=["POST"])
def login():
    body = request.get_json()
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    if not username or not password:
        return jsonify({"success": False, "error": "Missing credentials"}), 400

    print(f"\n{'='*50}")
    print(f"[APP] Login: {username}")

    driver = None
    try:
        driver = get_driver()
        wait = WebDriverWait(driver, 15)

        # ── LOGIN ──
        print("[LOGIN] Opening portal...")
        driver.get(f"{PORTAL_BASE}/StudentLogin.jsp")
        wait.until(EC.presence_of_element_located((By.NAME, "login_id")))

        driver.find_element(By.NAME, "login_id").send_keys(username)
        driver.find_element(By.NAME, "pass").send_keys(password)
        driver.find_element(By.XPATH, "//input[@type='submit']").click()

        # Wait for welcome page
        time.sleep(2)
        print(f"[LOGIN] Current URL: {driver.current_url}")

        if "StudentLogin" in driver.current_url:
            return jsonify({"success": False, "error": "Invalid credentials"}), 401

        print("[LOGIN] SUCCESS!")

        result = {
            "success": True,
            "profile": {"enrollment": username, "institute": "G H Patel College of Engineering & Technology"},
            "subjects": [], "attendance": [], "overall_pct": 0
        }

        # ── WELCOME PAGE — name + subjects ──
        print("[APP] Scraping welcome page...")
        soup = BeautifulSoup(driver.page_source, "html.parser")
        full_text = soup.get_text(separator="\n", strip=True)

        # Name from welcome page: "Name : PATEL PARTHKUMAR KALPESHBHAI"
        name_match = re.search(r"Name\s*[:\|]\s*([A-Z][A-Z\s]+)", full_text)
        if name_match:
            result["profile"]["name"] = name_match.group(1).strip()
            print(f"[PROFILE] Name: {result['profile']['name']}")

        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", full_text)
        if email_match:
            result["profile"]["email"] = email_match.group(0)

        # Subjects table
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2: continue
            headers = [c.get_text(strip=True) for c in rows[0].find_all(["th","td"])]
            if not any("course" in h.lower() for h in headers): continue
            print(f"[SUBJECTS] Headers: {headers}")
            for row in rows[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all("td")]
                if len(cells) < 3 or not cells[1]: continue
                code = cells[1]; name = cells[2]
                sem  = cells[5] if len(cells) > 5 else "II"
                if name and len(name) > 3:
                    result["subjects"].append({"code": code, "name": name, "type": "Theory", "semester": sem})
                    print(f"[SUBJECTS] {code} - {name}")
            if result["subjects"]:
                result["profile"]["semester"] = result["subjects"][0].get("semester","II")
                break

        # ── FIRST YEAR DATA ENTRY — full profile ──
        print("[APP] Fetching profile data...")
        driver.get(f"{PORTAL_BASE}/Student/FirstYear/FirstYearDataEntry.jsp?enrollment_no={username}")
        time.sleep(1)
        soup2 = BeautifulSoup(driver.page_source, "html.parser")
        print(f"[PROFILE] Page chars: {len(driver.page_source)}")

        # Extract all input values
        fields = {}
        for inp in soup2.find_all(["input","select","textarea"]):
            name2 = inp.get("name") or inp.get("id") or ""
            if inp.name == "select":
                selected = inp.find("option", selected=True)
                value = selected.get_text(strip=True) if selected else ""
            elif inp.name == "textarea":
                value = inp.get_text(strip=True)
            else:
                value = inp.get("value","").strip()
            skip = ["Submit","Reset","Save","Update","Edit","Cancel","Login","login_id","pass","login_type"]
            if name2 and value and value not in skip:
                fields[name2] = value

        # Also try to get values from actual rendered input elements via Selenium
        try:
            inputs = driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                n = inp.get_attribute("name") or inp.get_attribute("id") or ""
                v = inp.get_attribute("value") or ""
                if n and v and v not in ["Submit","Reset","Save","Update","Edit","Cancel","","login_id","pass"]:
                    fields[n] = v
                    print(f"[FIELD] {n} = {v}")
            selects = driver.find_elements(By.TAG_NAME, "select")
            for sel in selects:
                n = sel.get_attribute("name") or ""
                # ── FIX: get the VISIBLE TEXT of selected option, not raw value ──
                try:
                    from selenium.webdriver.support.ui import Select as SeleniumSelect
                    sel_obj = SeleniumSelect(sel)
                    v = sel_obj.first_selected_option.text.strip()
                except:
                    v = sel.get_attribute("value") or ""
                if n and v:
                    fields[n] = v
                    print(f"[SELECT] {n} = {v}")
        except: pass

        print(f"[PROFILE] Fields found: {fields}")

        def find_field(keys):
            for k in keys:
                for fk, fv in fields.items():
                    if k.lower() in fk.lower() and fv:
                        return fv
            return "N/A"

        result["profile"].update({
            "name":        result["profile"].get("name") or find_field(["student_name","studentname","sname","name","fname"]),
            "branch":      find_field(["branch","dept","program"]),
            "semester":    result["profile"].get("semester") or find_field(["semester","sem"]),
            "division":    find_field(["division","div","class"]),
            "roll_no":     find_field(["roll","rollno"]),
            "email":       result["profile"].get("email") or find_field(["email","mail"]),
            "mobile":      find_field(["mobile","phone","contact","mob"]),
            "dob":         find_field(["dob","birth"]),
            "father_name": find_field(["father","dad"]),
            "mother_name": find_field(["mother","mom"]),
        })

        # ── FIX GENDER: only set if it's actually a valid gender value ──
      #  raw_gender = find_field(["gender","sex"])
     #   if raw_gender and raw_gender.lower() in ["male", "female", "other", "m", "f"]:
            # Normalize to proper case
      #      gmap = {"m": "Male", "f": "Female", "male": "Male", "female": "Female", "other": "Other"}
      #      result["profile"]["gender"] = gmap.get(raw_gender.lower(), raw_gender.title())
        # else: don't add gender at all — avoids wrong "Female" for everyone 

        # ── ATTENDANCE ──
        print("[APP] Fetching attendance...")
        driver.get(f"{PORTAL_BASE}/Student/ViewMyAttendance.jsp")
        time.sleep(1)
        att = BeautifulSoup(driver.page_source, "html.parser")
        print(f"[ATT] Page chars: {len(driver.page_source)}")

        total_p = total_a = 0
        seen = set()
        for table in att.find_all("table"):
            rows = table.find_all("tr")
            if len(rows) < 2: continue
            headers = [c.get_text(strip=True) for c in rows[0].find_all(["th","td"])]
            if not any("course" in h.lower() or "present" in h.lower() for h in headers): continue
            print(f"[ATT] Headers: {headers}")
            for row in rows[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all("td")]
                if not any(cells) or len(cells) < 5: continue
                code      = cells[1] if len(cells) > 1 else ""
                sname     = cells[2] if len(cells) > 2 else ""
                stype_raw = cells[3] if len(cells) > 3 else "T"
                att_str   = cells[-1]
                stype     = "Theory" if stype_raw=="T" else "Practical" if stype_raw=="P" else "Lab"
                present = absent = pct = 0
                m = re.search(r"(\d+)/(\d+)\s*\((\d+\.?\d*)%\)", att_str)
                if m:
                    present=int(m.group(1)); total_cls=int(m.group(2))
                    absent=total_cls-present; pct=float(m.group(3))
                    total_p+=present; total_a+=absent
                if sname:
                    result["attendance"].append({"code":code,"name":sname,"type":stype,"_pct":pct,"_present":present,"_absent":absent})
                    print(f"[ATT] {sname}: {pct}%")
                if sname and f"{code}-{sname}" not in seen:
                    seen.add(f"{code}-{sname}")
                    existing = next((s for s in result["subjects"] if s["code"]==code and s["name"]==sname), None)
                    if existing: existing["type"] = stype
                    elif not result["subjects"]: result["subjects"].append({"code":code,"name":sname,"type":stype})

        if total_p+total_a > 0:
            result["overall_pct"]   = round((total_p/(total_p+total_a))*100, 1)
            result["total_present"] = total_p
            result["total_absent"]  = total_a
            result["total_classes"] = total_p+total_a
            print(f"[ATT] Overall: {result['overall_pct']}%")

        print(f"[APP] Done! Subjects:{len(result['subjects'])} Att:{len(result['attendance'])} Overall:{result['overall_pct']}%")
        return jsonify(result)

    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("\n EduTrack backend running on http://localhost:5000")
    app.run(debug=False, port=5000)
