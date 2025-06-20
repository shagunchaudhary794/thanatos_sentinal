let cpuLabels = [], cpuData = [];
let memLabels = [], memData = [];
let netLabels = [], netUpData = [], netDownData = [];

const cpuChart = new Chart(document.getElementById("cpuChart"), {
    type: "line",
    data: {
        labels: cpuLabels,
        datasets: [{
            label: "CPU %",
            borderColor: "#ff0055",
            backgroundColor: "rgba(255, 0, 85, 0.1)",
            data: cpuData,
            tension: 0.3,
            fill: true
        }]
    },
    options: { responsive: true, animation: false }
});

const memChart = new Chart(document.getElementById("memChart"), {
    type: "line",
    data: {
        labels: memLabels,
        datasets: [{
            label: "Memory %",
            borderColor: "#00ffff",
            backgroundColor: "rgba(0,255,255,0.1)",
            data: memData,
            tension: 0.3,
            fill: true
        }]
    },
    options: { responsive: true, animation: false }
});

const netChart = new Chart(document.getElementById("netChart"), {
    type: "line",
    data: {
        labels: netLabels,
        datasets: [
            {
                label: "Net Upload MB",
                borderColor: "#ffaa00",
                backgroundColor: "rgba(255,170,0,0.1)",
                data: netUpData,
                tension: 0.3,
                fill: true
            },
            {
                label: "Net Download MB",
                borderColor: "#00ff88",
                backgroundColor: "rgba(0,255,136,0.1)",
                data: netDownData,
                tension: 0.3,
                fill: true
            }
        ]
    },
    options: { responsive: true, animation: false }
});


// === Real-Time Stats Fetch ===
async function fetchStats() {
    try {
        const res = await fetch('/stats');
        const data = await res.json();

        // Update dashboard meters
        document.getElementById('cpu-meter').innerText = data.cpu + '%';
        document.getElementById('mem-meter').innerText = data.memory + '%';
        document.getElementById('net-up').innerText = data.net_sent + ' MB';
        document.getElementById('net-down').innerText = data.net_recv + ' MB';
        document.getElementById("threat-level").innerText = data.threat;

        // Threat color logic
        const threat = document.getElementById("threat-level");
        if (data.threat === "Critical") {
            threat.style.color = "#ff0033";
            threat.style.textShadow = "0 0 15px #ff0033";
        } else if (data.threat === "High") {
            threat.style.color = "#ffaa00";
            threat.style.textShadow = "0 0 10px #ffaa00";
        } else if (data.threat === "Medium") {
            threat.style.color = "#00ffff";
            threat.style.textShadow = "0 0 10px #00ffff";
        } else {
            threat.style.color = "#00ff99";
            threat.style.textShadow = "0 0 8px #00ff99";
        }

        // Update silent mode
        const silentBtn = document.getElementById('silent-toggle');
        if (data.silent) {
            silentBtn.classList.add('active');
            silentBtn.textContent = 'Silent Mode: ON';
        } else {
            silentBtn.classList.remove('active');
            silentBtn.textContent = 'Silent Mode: OFF';
        }

        // 🧠 === GRAPH DATA LOGIC ===
        const time = new Date().toLocaleTimeString();

        if (cpuLabels.length >= 20) {
            cpuLabels.shift(); cpuData.shift();
            memLabels.shift(); memData.shift();
            netLabels.shift(); netUpData.shift(); netDownData.shift();
        }

        cpuLabels.push(time);
        cpuData.push(data.cpu);

        memLabels.push(time);
        memData.push(data.memory);

        netLabels.push(time);
        netUpData.push(data.net_sent);
        netDownData.push(data.net_recv);

        cpuChart.update();
        memChart.update();
        netChart.update();

    } catch (err) {
        console.error("Stats error:", err);
    }
}


// === Real-Time Log Fetch ===
async function fetchLogs() {
    const level = document.getElementById("threat-filter").value;
    const keyword = document.getElementById("log-search").value.trim();

    const res = await fetch(`/logs?level=${level}&keyword=${encodeURIComponent(keyword)}`);
    const data = await res.json();

    const logBox = document.getElementById("log-box");
    logBox.innerHTML = '';

    data.logs.forEach(line => {
        const div = document.createElement('div');
        div.classList.add('log-line');
        div.textContent = line.trim();
        logBox.appendChild(div);
    });

    logBox.scrollTop = logBox.scrollHeight;
}


// === Silent Mode Toggle ===
async function toggleSilent() {
    try {
        const res = await fetch('/silent', { method: 'POST' });
        const data = await res.json();
        fetchStats(); // Immediately refresh button status
    } catch (err) {
        console.error("Silent toggle error:", err);
    }
}

// === Trigger Report Download ===
function downloadReport() {
    window.open('/report', '_blank');
}

// === Auto Refresh Stats & Logs ===
setInterval(() => {
    fetchStats();
    fetchLogs();
}, 3000);

// === On Load ===
window.onload = () => {
    fetchStats();
    fetchLogs();
};
function archiveNow() {
    fetch("/archive_now", { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.status === "success") {
                alert("🗃️ Logs archived successfully!");
            } else {
                alert("⚠️ Archive failed: " + data.message);
            }
        })
        .catch(err => {
            alert("🔥 Unexpected error: " + err);
        });
}

async function fetchProcesses() {
    const res = await fetch('/process_list');
    const data = await res.json();
    const tableBody = document.querySelector("#process-table tbody");
    tableBody.innerHTML = "";

    data.forEach(proc => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${proc.pid}</td>
            <td>${proc.name}</td>
            <td>${proc.cpu}</td>
            <td>${proc.mem}</td>
            <td><button onclick="killProcess(${proc.pid})">Kill</button></td>
        `;
        tableBody.appendChild(row);
    });
}

function killProcess(pid) {
    fetch(`/kill/${pid}`, { method: "POST" })
        .then(res => res.json())
        .then(data => {
            if (data.status === "killed") {
                alert(`☠️ Killed: ${data.name} (PID ${pid})`);
                fetchProcesses(); // Refresh table
            } else {
                alert(`⚠️ Failed to kill PID ${pid}: ${data.message}`);
            }
        });
}

// Auto-refresh processes every 5 seconds
setInterval(fetchProcesses, 5000);
window.onload = () => {
    fetchStats();
    fetchLogs();
    fetchProcesses();
    fetchThreatDNA();
    setInterval(fetchThreatDNA, 5000);
    setInterval(fetchQuarantined, 3000);


};
async function fetchThreatDNA() {
    const res = await fetch("/threats");
    const data = await res.json();
    const tableBody = document.querySelector("#threat-dna-table tbody");
    tableBody.innerHTML = "";

    data.slice(-25).reverse().forEach(t => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${t.timestamp}</td>
            <td>${t.name}</td>
            <td>${t.pid}</td>
            <td>${t.parent}</td>
            <td>${t.path}</td>
            <td>${t.spawn_rate}</td>
            <td style="color: ${t.threat_level === 'Critical' ? '#ff0033' : t.threat_level === 'High' ? '#ffaa00' : '#00ffff'}">${t.threat_level}</td>
            <td>${t.action}</td>
        `;
        tableBody.appendChild(row);
    });
}
function downloadReport() {
    fetch('/generate_report')
        .then(res => {
            if (!res.ok) throw new Error("Failed to generate report");
            return res.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "Thanatos_Threat_Report.pdf";
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(err => alert("⚠️ " + err.message));
}
document.getElementById("decrypt-form").addEventListener("submit", async function(e) {
    e.preventDefault();

    const file = document.getElementById("enc-file").files[0];
    const key = document.getElementById("decrypt-key").value;

    if (!file || !key) return alert("Select file and enter key");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("key", key);

    const res = await fetch("/decrypt", { method: "POST", body: formData });
    const result = await res.json();

    const output = document.getElementById("decrypted-output");

    if (result.success) {
        output.textContent = result.content;
        output.style.color = "#0f0";
    } else {
        output.textContent = "❌ Decryption failed: " + result.error;
        output.style.color = "#f33";
    }
});
async function fetchQuarantined() {
    const res = await fetch("/quarantined");
    const data = await res.json();

    const tbody = document.querySelector("#isolation-table tbody");
    tbody.innerHTML = "";

    Object.entries(data).forEach(([pid, proc]) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${pid}</td>
            <td>${proc.name}</td>
            <td>${proc.path}</td>
            <td>
                <button onclick="handleProcess(${pid}, 'resume')">Resume</button>
                <button onclick="handleProcess(${pid}, 'kill')">Kill</button>
                <button onclick="handleProcess(${pid}, 'ignore')">Ignore</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function handleProcess(pid, action) {
    const res = await fetch(`/quarantined/${pid}/${action}`, { method: "POST" });
    const result = await res.json();
    if (!result.success) {
        alert("Error: " + result.error);
    }
    fetchQuarantined();
}
function applyTheme(theme) {
    document.body.className = theme;
    localStorage.setItem("thanatos_theme", theme);
}

document.getElementById("theme-select").addEventListener("change", function () {
    applyTheme(this.value);
});

// On load — apply saved theme
window.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("thanatos_theme") || "dark";
    document.getElementById("theme-select").value = savedTheme;
    applyTheme(savedTheme);
});
