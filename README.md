
# Thanatos Sentinel 🛡️🧬

**Real-Time Threat Detection, Isolation, and Analysis System**  
Built by: **Shagun**  
Completion Date: **June 20, 2025**

Thanatos Sentinel is a handcrafted real-time process monitoring system for Windows designed to detect, suspend, and analyze potentially malicious activities. It includes CPU/Memory/Network monitoring, encrypted log storage, theme customization, and full manual control over suspicious processes.

---

## 🔥 Features

- ✅ Real-Time Process Monitoring
- ✅ Threat Classification (Low → Critical)
- ✅ Critical Threat Isolation (Suspend instead of Kill)
- ✅ Quarantine System
- ✅ CPU, Memory, Network Spike Detection
- ✅ Threat DNA Log Storage + Encrypted Archives
- ✅ Encrypted Log Decryption UI Panel
- ✅ System Tray Integration
- ✅ Fully Themed UI (Neon Blue, Blood Red, Matrix Green, Tactical)
- ✅ Theme Persistence (via localStorage)
- ✅ Anti-Tamper (File Change & Process Kill Detection)
- ✅ Manual Threat Controls (Resume / Kill / Ignore)
- ✅ Log System & UI Log Feed
- ✅ Silent Mode Support (No Notifications)

---

## 🚀 Technologies Used

| Layer        | Tech Stack                           |
|--------------|---------------------------------------|
| Frontend     | HTML, CSS (Neon), JS                 |
| Backend      | Python (Flask)                       |
| Monitoring   | psutil, WMI, threading               |
| Notifications| plyer                                |
| Encryption   | pycryptodome (AES)                   |
| UI Themes    | CSS switch + localStorage            |

---

## 🧠 Setup & Usage

### Installation:

```bash
git clone https://github.com/yourname/thanatos_sentinal
cd thanatos_sentinal
pip install -r requirements.txt
python app.py
```

### Access the Dashboard:

Open `http://localhost:5000` in your browser.

---

## 🗂 Folder Structure

```
thanatos_sentinel/
├── app.py                          # Flask backend
├── logs/                           # All system and threat logs
│   ├── sentinel_logs.log
│   └── threat_dna.log
├── threat_reports/                # PDF or .enc archives
├── static/
│   ├── css/style.css              # UI themes
│   └── js/main.js                 # Frontend logic
├── templates/
│   └── index.html                 # Main UI
```

---

## 🎯 How It Works

- System processes are monitored using WMI.
- Suspicious behavior (spawn rate, parent, path, name) is scored.
- Critical processes are suspended, not killed.
- User can manually kill/resume from UI.
- All data is logged and optionally encrypted.
- Themes can be toggled live in the UI.

---

## ✨ Future Enhancements

- 📁 PDF/HTML Report Export
- 💌 Email Alert System
- 🕵️ Red Team Logging Mode (silent)
- 🧠 Live Memory Dump / Inspection
- ☁ Cloud-Synced Logs & Report Dashboard

---

## Author Note
It is just a prototype still working to get it better.


