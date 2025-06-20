from flask import Flask, render_template, jsonify, request, send_file
import psutil
import os
import time
from datetime import datetime
import wmi
import pythoncom
import threading
from collections import defaultdict
import shutil
from cryptography.fernet import Fernet
import json
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import hashlib
from flask import request, render_template, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
from plyer import notification
quarantined_processes = {}


app = Flask(__name__)

LOG_FILE = "logs/sentinel_logs.log"
SILENT_MODE = False
current_threat_level = "Low"
process_spawn_tracker = defaultdict(list)
QUARANTINE_DIR = "quarantine"
FERNET_KEY = b'your fertnet key'
fernet = Fernet(FERNET_KEY)
dna_file = "threat_dna.log"
filepath = os.path.join("threat_reports")



# Create necessary folders
os.makedirs("logs", exist_ok=True)
os.makedirs("quarantine", exist_ok=True)
os.makedirs("archive", exist_ok=True)
os.makedirs(QUARANTINE_DIR, exist_ok=True)
os.makedirs("threat_reports", exist_ok=True)



# === Utils ===

def log_event(message):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}\n"
    with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
        f.write(line)
    return line
    


# === Routes ===
@app.route("/quarantined")
def get_quarantined():
    return jsonify(quarantined_processes)

@app.route("/quarantined/<int:pid>/<action>", methods=["POST"])
def control_process(pid, action):
    try:
        p = psutil.Process(pid)
        if action == "resume":
            p.resume()
            log_event(f"✅ Resumed PID {pid}")
        elif action == "kill":
            p.terminate()
            p.wait(timeout=3)
            log_event(f"☠ Killed PID {pid}")
            quarantine_file(quarantined_processes[pid]["path"])
        elif action == "ignore":
            log_event(f"⚠ Ignored PID {pid}")
        quarantined_processes.pop(pid, None)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/decrypt", methods=["POST"])
def decrypt_log():
    file = request.files.get("file")
    key = request.form.get("key")

    if not file or not key:
        return jsonify({"success": False, "error": "Missing file or key"})

    try:
        data = file.read()
        key_bytes = key.encode('utf-8')
        key_bytes = key_bytes[:32].ljust(32, b'\0')  # Ensure 32 bytes

        iv = data[:16]
        ciphertext = data[16:]

        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        text = decrypted.decode("utf-8")

        return jsonify({"success": True, "content": text})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/generate_report")
def generate_pdfreport():
    log_path = "logs/threat_dna.log"  # keep this path to your logs
    if not os.path.exists(log_path):
        return "Threat DNA log not found", 404

    # Load threat entries
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            entries = [json.loads(l.strip()) for l in f if l.strip()]
    except Exception as e:
        return f"Failed to read log file: {str(e)}", 500

    # ✅ Use your specified directory here
    report_dir = r"logs/threat_dna.log"
    os.makedirs(report_dir, exist_ok=True)

    filename = f"threat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = os.path.join(report_dir, filename)

    # Generate PDF
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Thanatos Sentinel — Threat DNA Report")

    c.setFont("Helvetica", 10)
    y = height - 80
    for t in entries:
        line = f"[{t['timestamp']}] {t['name']} | PID {t['pid']} | Parent: {t['parent']} | Threat: {t['threat_level']} | Action: {t['action']}"
        c.drawString(50, y, line[:110])
        y -= 15
        if y < 50:
            c.showPage()
            y = height - 50

    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 30, f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()

    return send_file(filepath, as_attachment=True)



@app.route("/threats")
def get_threat_dna():
    dna_file = "logs/threat_dna.log"
    if not os.path.exists(dna_file):
        return jsonify([])

    with open(dna_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    try:
        return jsonify([json.loads(l) for l in lines if l.strip()])
    except Exception:
        return jsonify([])


@app.route("/")
def index():
    return render_template("index.html")
@app.route("/process_list")
def process_list():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            processes.append({
                "pid": info['pid'],
                "name": info['name'],
                "cpu": round(info['cpu_percent'], 1),
                "mem": round(info['memory_percent'], 1)
            })
        except:
            continue
    return jsonify(processes)

@app.route("/kill/<int:pid>", methods=["POST"])
def kill_pid(pid):
    try:
        p = psutil.Process(pid)
        name = p.name()
        p.terminate()
        p.wait(timeout=3)
        log_event(f"Process manually killed: {name} (PID {pid})")
        return jsonify({"status": "killed", "name": name})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/stats")
def stats():
    net = psutil.net_io_counters()
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent

    # TEMPORARY: Inject artificial log
    log_event(f"System: CPU={cpu}%, Mem={mem}%, Net={net.bytes_sent // (1024*1024)}MB Sent")


    return jsonify({
    "cpu": cpu,
    "memory": mem,
    "net_sent": net.bytes_sent // (1024 * 1024),
    "net_recv": net.bytes_recv // (1024 * 1024),
    "silent": SILENT_MODE,
    "threat": current_threat_level
})

@app.route("/archive_now", methods=["POST"])
def manual_archive():
    try:
        encrypt_and_archive_log()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/logs")
def get_logs():
    level = request.args.get("level")
    keyword = request.args.get("keyword", "").lower()

    if not os.path.exists(LOG_FILE):
        return jsonify({"logs": []})

    with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    filtered = []

    for line in lines:
        line_lower = line.lower()

        # Apply filters
        if level and level.lower() not in line_lower:
            continue
        if keyword and keyword not in line_lower:
            continue

        filtered.append(line)

    return jsonify({"logs": filtered[-50:]})


@app.route("/silent", methods=["POST"])
def toggle_silent():
    global SILENT_MODE
    SILENT_MODE = not SILENT_MODE
    status = "enabled" if SILENT_MODE else "disabled"
    log_event(f"Silent Mode {status}.")
    return jsonify({"silent": SILENT_MODE})

@app.route("/report")
def generate_report():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = f"logs/report_{timestamp}.txt"
    with open(report_path, "w", encoding="utf-8") as report:
        report.write("=== Thanatos Sentinel Threat Report ===\n")
        report.write("Generated at: " + datetime.now().isoformat() + "\n\n")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as log:
                report.writelines(log.readlines())

    return send_file(report_path, as_attachment=True)

def classify_threat(proc_name, parent_name, spawn_rate, path):
    score = 0
    proc = proc_name.lower()
    parent = parent_name.lower()

    # Score based on known suspicious processes
    if proc in ["unknown.exe", "payload.exe", "rat.exe", "cmd.exe", "powershell.exe"]:
        score += 3
    if parent in ["cmd.exe", "powershell.exe", "wmiprvse.exe"]:
        score += 2
    if spawn_rate > 5:
        score += 4
    if "temp" in path.lower() or path.lower().startswith("c:\\users\\"):
        score += 2

    if score >= 7:
        return "Critical"
    elif score >= 5:
        return "High"
    elif score >= 3:
        return "Medium"
    else:
        return "Low"
    
def monitor_processes():
    global current_threat_level
    pythoncom.CoInitialize()
    c = wmi.WMI()
    watcher = c.Win32_Process.watch_for("creation")

    while True:
        try:
            proc = watcher()
            name = proc.Caption or "Unknown"
            parent = proc.GetOwner()[0] if proc.GetOwner() else "Unknown"
            path = proc.ExecutablePath or "Unknown"
            pid = proc.ProcessId

            now = time.time()
            process_spawn_tracker[name].append(now)
            process_spawn_tracker[name] = [
                t for t in process_spawn_tracker[name] if now - t < 10
            ]
            spawn_rate = len(process_spawn_tracker[name])

            level = classify_threat(name, parent, spawn_rate, path)
            log_event(f"{name} | PID: {pid} | Parent: {parent} | Path: {path} | Threat: {level}")

            # Update global threat level
            if level == "Critical":
                current_threat_level = "Critical"
            elif level == "High" and current_threat_level != "Critical":
                current_threat_level = "High"
            elif level == "Medium" and current_threat_level not in ["High", "Critical"]:
                current_threat_level = "Medium"

            # Save to Threat DNA log
            if level in ["High", "Critical"]:
                save_threat_dna({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "name": name,
                    "pid": pid,
                    "parent": parent,
                    "path": path,
                    "threat_level": level,
                    "spawn_rate": spawn_rate,
                    "action": "Suspended (awaiting manual action)" if level == "Critical" else "Monitored"
                })

            # 🧊 SUSPEND instead of kill
            if level == "Critical" and path != "Unknown":
                try:
                    p = psutil.Process(pid)
                    p.suspend()
                    log_event(f"☠ Suspended: {name} | PID {pid}")
                    quarantined_processes[pid] = {
                        "name": name,
                        "path": path
                    }
                except Exception as e:
                    log_event(f"Failed to suspend process {pid}: {e}")

        except Exception:
            continue

            
def kill_process(pid, name):
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        log_event(f"Terminated process: {name} (PID {pid})")
    except Exception as e:
        log_event(f"Failed to terminate {name} (PID {pid}): {e}")

def quarantine_file(file_path):
    try:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            dest = os.path.join(QUARANTINE_DIR, filename)
            shutil.move(file_path, dest)
            log_event(f"Quarantined file: {filename}")
        else:
            log_event(f"Quarantine failed: File not found at {file_path}")
    except Exception as e:
        log_event(f"Error during quarantine: {e}")

    """whitelist = ["python.exe", "explorer.exe", "chrome.exe"]
    if name.lower() not in whitelist:
        kill_process(...)"""

def encrypt_and_archive_log():
    try:
        if not os.path.exists(LOG_FILE):
            log_event("No log file found to archive.")
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        with open(LOG_FILE, "rb") as file:
            original = file.read()

        encrypted = fernet.encrypt(original)
        archive_path = os.path.join("archive", f"log_{timestamp}.enc")

        with open(archive_path, "wb") as enc_file:
            enc_file.write(encrypted)

        log_event(f"Log archived to {archive_path}")
        open(LOG_FILE, "w").close()  # Clear original log
    except Exception as e:
        log_event(f"Archive failed: {e}")

def save_threat_dna(threat_data):
    with open("logs/threat_dna.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(threat_data) + "\n")


def auto_archive_logs():
    while True:
        now = datetime.now()
        if now.weekday() == 6 and now.hour == 23 and now.minute == 59:  # Sunday 11:59 PM
            encrypt_and_archive_log()
            time.sleep(60)  # avoid re-archiving multiple times that minute
        time.sleep(30)

important_files = [
    "app.py",
    "logs/threat_dna.log",
    "logs/sentinel_logs.log"
]

file_hashes = {}

def get_file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except:
        return None

"""def monitor_files_for_tamper():
    global file_hashes
    while True:
        for f in important_files:
            current_hash = get_file_hash(f)
            if f not in file_hashes:
                file_hashes[f] = current_hash
            elif file_hashes[f] != current_hash:
                log_event(f"⚠️ Tamper detected in {f}")
                notification.notify(
                    title="Thanatos Anti-Tamper Alert",
                    message=f"File altered: {f}",
                    timeout=100
                )
                file_hashes[f] = current_hash  # Update to avoid spamming
        time.sleep(0) """       
"""def self_pid_guard():
    self_pid = os.getpid()
    while True:
        try:
            p = psutil.Process(self_pid)
            if p.status() == psutil.STATUS_ZOMBIE:
                log_event("⚠️ Tamper attempt: Thanatos process turned zombie")
        except psutil.NoSuchProcess:
            log_event("⚠️ Tamper attempt: Thanatos process killed")
            # optional: relaunch self
        time.sleep(5)"""

# === Launch ===
if __name__ == "__main__":
    threading.Thread(target=monitor_processes, daemon=True).start()
    threading.Thread(target=auto_archive_logs, daemon=True).start()
    #threading.Thread(target=monitor_files_for_tamper, daemon=True).start()
    #threading.Thread(target=self_pid_guard, daemon=True).start()

    app.run(debug=True)

