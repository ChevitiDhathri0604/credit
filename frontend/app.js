// --- 📊 INITIALIZATION AND APP VARIABLES ---
let gaugeChartInstance = null;
let importanceChartInstance = null;
let activeRiskScore = 0;
let activePayload = {};

// --- 🔐 SESSION MANAGEMENT CONTROLS ---
let sessionToken = localStorage.getItem("riskshield_token") || "";
let userRole = localStorage.getItem("riskshield_role") || "";
let userName = localStorage.getItem("riskshield_name") || "";

// Automatically restore user session if a token exists
if (sessionToken) {
    unlockDashboard();
}

// --- 🎛️ SLIDER RANGE INTERACTION CONTROLLERS ---
const linkedSliders = ['v10', 'v12', 'v14', 'v17'];
linkedSliders.forEach(id => {
    const slider = document.getElementById(id);
    const textTracker = document.getElementById(`${id}_val`);
    if (slider && textTracker) {
        textTracker.innerText = parseFloat(slider.value).toFixed(1);
        slider.addEventListener('input', (e) => {
            textTracker.innerText = parseFloat(e.target.value).toFixed(1);
        });
    }
});

// --- 🔑 AUTHENTICATION LOGIN OVERLAYS (PORT 8000 ALIGNED) ---
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    const formBody = new URLSearchParams();
    formBody.append("username", email);
    formBody.append("password", password);

    try {
        const response = await fetch('/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formBody
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "Invalid operational pipeline access credentials.");
        }

        const data = await response.json();

        sessionToken = data.access_token;
        userRole = data.role;
        userName = data.name;

        localStorage.setItem("riskshield_token", sessionToken);
        localStorage.setItem("riskshield_role", userRole);
        localStorage.setItem("riskshield_name", userName);

        unlockDashboard();
    } catch (err) {
        alert("Authentication Engine Blockage: " + err.message);
    }
});

// --- 🚪 LOGOUT PIPELINE TERMINATION PROTOCOLS ---
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.clear();
    location.reload();
});

function unlockDashboard() {
    document.getElementById('authScreen').classList.add('hidden');
    const dashboard = document.getElementById('mainDashboard');
    dashboard.classList.remove('opacity-30', 'pointer-events-none');

    document.getElementById('usrBadgeName').innerText = userName;
    document.getElementById('usrBadgeRole').innerText = `CLEARANCE: ${userRole}`;

    const submitBtn = document.getElementById('submitBtn');
    if (userRole === 'Auditor' && submitBtn) {
        submitBtn.innerText = "VIEW-ONLY AUDITOR READ ONLY";
        submitBtn.disabled = true;
        submitBtn.className = "w-full py-4 bg-slate-800 text-slate-500 font-bold uppercase rounded-xl tracking-widest text-sm cursor-not-allowed";
    }
}

// --- 🛡️ TRANSMIT SECURED ML PAYLOAD PACKETS (PORT 8000 ALIGNED) ---
document.getElementById('fraudForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    activePayload = {
        amount: parseFloat(document.getElementById('amount').value),
        time: parseFloat(document.getElementById('time').value),
        v10: parseFloat(document.getElementById('v10').value),
        v12: parseFloat(document.getElementById('v12').value),
        v14: parseFloat(document.getElementById('v14').value),
        v17: parseFloat(document.getElementById('v17').value)
    };

    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionToken}`
            },
            body: JSON.stringify(activePayload)
        });

        if (response.status === 403) throw new Error("Forbidden: Clearance limits blocked ML indexing execution paths.");

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Server error code: ${response.status}`);
        }

        const data = await response.json();

        document.getElementById('placeholderView').classList.add('hidden');
        document.getElementById('resultsView').classList.remove('hidden');

        activeRiskScore = data.risk_score;
        renderGauge(activeRiskScore);
        renderImportanceChart(activePayload);

        const dialogueBox = document.getElementById('chatDialogueBox');
        dialogueBox.innerHTML = `<p class="text-cyan-400">🤖 [Agent]: Operational channel connected. Security context parsed at ${activeRiskScore}%. Ask a question below to trace calculation matrices.</p>`;

        const alertBox = document.getElementById('statusAlert');
        if (activeRiskScore >= 50) {
            alertBox.innerText = `🚨 ALERT: ${data.prediction}`;
            alertBox.className = "p-3 rounded-xl text-center font-mono font-bold text-xs border border-rose-800 text-rose-400 bg-rose-950/30";
        } else {
            alertBox.innerText = `✅ APPROVED: ${data.prediction}`;
            alertBox.className = "p-3 rounded-xl text-center font-mono font-bold text-xs border border-emerald-800 text-emerald-400 bg-emerald-950/30";
        }

        appendToHistoryLog(data.transaction_id, activePayload.amount, activeRiskScore, data.prediction);
    } catch (err) {
        alert("Execution Scanning Failure: " + err.message);
    }
});

// --- 🤖 SECURED AI AGENT COMMUNICATION INTERFACE (PORT 8000 ALIGNED) ---
document.getElementById('agentChatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const inputArea = document.getElementById('chatUserInput');
    const queryText = inputArea.value.trim();
    if (!queryText) return;

    const dialogueBox = document.getElementById('chatDialogueBox');
    dialogueBox.innerHTML += `<p class="text-slate-400 mt-2">👤 [You]: ${queryText}</p>`;
    inputArea.value = "";

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${sessionToken}`
            },
            body: JSON.stringify({
                user_question: queryText,
                amount: activePayload.amount || 0,
                risk_score: activeRiskScore,
                v14: activePayload.v14 || 0,
                v17: activePayload.v17 || 0
            })
        });

        if (!response.ok) throw new Error();
        const data = await response.json();
        dialogueBox.innerHTML += `<p class="text-cyan-300 mt-1">${data.response}</p>`;
        dialogueBox.scrollTop = dialogueBox.scrollHeight;
    } catch (err) {
        dialogueBox.innerHTML += `<p class="text-rose-400 mt-1">❌ Connection error tracking trace token authorization vectors.</p>`;
    }
});

// --- 📊 APEXCHARTS VISUALIZATION BUILDERS ---
function renderGauge(riskScore) {
    const color = riskScore >= 50 ? '#f43f5e' : '#10b981';
    const config = {
        series: [riskScore],
        chart: { type: 'radialBar', height: 160, sparkline: { enabled: true } },
        plotOptions: {
            radialBar: {
                startAngle: -90, endAngle: 90,
                track: { background: "#1e293b", strokeWidth: '95%' },
                dataLabels: { value: { offsetY: -2, fontSize: '24px', fontFamily: 'monospace', fontWeight: 'bold', color: '#f8fafc' } }
            }
        },
        fill: { colors: [color] }
    };
    if (gaugeChartInstance) gaugeChartInstance.updateOptions(config);
    else { gaugeChartInstance = new ApexCharts(document.querySelector("#gaugeChart"), config); gaugeChartInstance.render(); }
}

function renderImportanceChart(payload) {
    const data = [Math.abs(payload.v14) * 2.5, Math.abs(payload.v17) * 2.1, Math.abs(payload.v12) * 1.4, Math.abs(payload.v10) * 0.9];
    const config = {
        series: [{ name: 'Impact Factor', data: data }],
        chart: { type: 'bar', height: 120, sparkline: { enabled: true } },
        plotOptions: { bar: { horizontal: true, barHeight: '50%', distributed: true } },
        colors: ['#f43f5e', '#fb7185', '#38bdf8', '#0284c7'],
        xaxis: { categories: ['V14', 'V17', 'V12', 'V10'] }
    };
    if (importanceChartInstance) importanceChartInstance.updateOptions(config);
    else { importanceChartInstance = new ApexCharts(document.querySelector("#importanceChart"), config); importanceChartInstance.render(); }
}

// --- 📋 AUDIT LEDGER LOG LOGGER ---
function appendToHistoryLog(id, amount, score, prediction) {
    const emptyRow = document.getElementById('emptyHistoryRow');
    if (emptyRow) emptyRow.remove();
    const tbody = document.getElementById('historyLogBody');
    const tr = document.createElement('tr');
    tr.className = "border-b border-slate-900 bg-slate-950/10";
    const badge = score >= 50 ? "text-rose-400 bg-rose-950/40 border border-rose-900/40" : "text-emerald-400 bg-emerald-950/40 border border-emerald-900/40";
    tr.innerHTML = `
        <td class="py-3 px-4 text-slate-400">#${id}</td>
        <td class="py-3 px-4 text-emerald-400 font-medium">$${amount.toFixed(2)}</td>
        <td class="py-3 px-4 font-bold ${score >= 50 ? 'text-rose-400' : 'text-slate-200'}">${score}%</td>
        <td class="py-3 px-4 text-right"><span class="px-2 py-0.5 text-[9px] rounded-full font-bold uppercase ${badge}">${prediction}</span></td>
    `;
    tbody.insertBefore(tr, tbody.firstChild);
}