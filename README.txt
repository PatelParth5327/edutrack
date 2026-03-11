╔══════════════════════════════════════════════════╗
║         EduTrack — Setup Guide (5 mins)          ║
╚══════════════════════════════════════════════════╝

WHAT YOU NEED:
  - Python installed on your laptop
  - Your college portal credentials

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1 — Install Python (if not already)
  Download from: https://python.org/downloads
  ✅ Check "Add Python to PATH" during install

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2 — Install required libraries
  Open terminal / command prompt in this folder and run:

    pip install flask flask-cors requests beautifulsoup4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3 — Start the backend
  In the same terminal run:

    python app.py

  You should see:
    🚀 EduTrack backend → http://localhost:5000

  ⚠️ Keep this terminal OPEN while using the app

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4 — Open the app
  Just double-click index.html to open in browser
  OR open it manually in Chrome / Edge

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5 — Login
  Enter your college Enrollment No. + Portal Password
  Hit "Sign In & Fetch Data"

  The app will:
  ✅ Connect to your backend (localhost:5000)
  ✅ Backend logs into college portal
  ✅ Scrapes your profile, attendance, subjects
  ✅ Shows everything in the dashboard!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING

  ❌ "Backend not running"
     → Make sure you ran "python app.py" first

  ❌ "Cannot reach portal"
     → Make sure you're on the same network as the portal
     → Try opening http://202.129.240.148:8080 in browser first

  ❌ Data shows N/A or missing
     → Open Profile page in app → scroll down to "Raw Portal Data"
     → Check what was actually fetched
     → Tell Claude what URL the attendance/profile is on
       and I'll update app.py to scrape the right page

  ❌ Subjects not showing
     → Open your college portal manually
     → Find which page shows subjects
     → Tell Claude the URL → I'll add it to app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FILES IN THIS FOLDER:
  app.py          → Python backend (runs on your laptop)
  index.html      → The app (open in browser)
  requirements.txt → Libraries list
  README.txt      → This file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY NOTE:
  Your password is NEVER stored anywhere.
  It's only used to log into the portal for that session.
  The backend runs only on YOUR computer — nothing
  is sent to any external server.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
