"""
Interactive Web Dashboard for Cold-Chain Produce Spoilage Service.
Provides an intuitive UI for students and instructors to explore live telemetry,
simulate temperature breaches, view active alerts, and test API endpoints.
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cold-Chain Produce Spoilage Alert Service</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --primary: #38bdf8;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
    body { background-color: var(--bg); color: var(--text); min-height: 100vh; padding: 2rem 1rem; }
    .container { max-width: 1200px; margin: 0 auto; }
    header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }
    .badge { display: inline-flex; align-items: center; gap: 0.5rem; background: #064e3b; color: #34d399; padding: 0.4rem 0.8rem; border-radius: 9999px; font-size: 0.85rem; font-weight: 600; }
    .badge .dot { width: 8px; height: 8px; background: #34d399; border-radius: 50%; box-shadow: 0 0 8px #34d399; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
    .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3); }
    .card h3 { font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; display: flex; align-items: center; gap: 0.5rem; }
    .btn { cursor: pointer; border: none; padding: 0.65rem 1.2rem; border-radius: 8px; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; }
    .btn-primary { background: #0284c7; color: white; }
    .btn-primary:hover { background: #0369a1; }
    .btn-warning { background: #b45309; color: white; }
    .btn-warning:hover { background: #92400e; }
    .btn-danger { background: #b91c1c; color: white; }
    .btn-danger:hover { background: #991b1b; }
    .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
    .btn-outline:hover { background: #334155; }
    .btn-sm { padding: 0.35rem 0.75rem; font-size: 0.8rem; }
    .sim-buttons { display: flex; flex-direction: column; gap: 0.75rem; }
    .produce-pill { display: flex; justify-content: space-between; align-items: center; background: #0f172a; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 0.6rem; border: 1px solid var(--border); }
    .rule-item { padding: 0.75rem; background: #0f172a; border-radius: 8px; margin-bottom: 0.6rem; font-size: 0.88rem; line-height: 1.4; border-left: 4px solid var(--primary); }
    .rule-ok { border-left-color: var(--success); }
    .rule-warn { border-left-color: var(--warning); }
    .rule-crit { border-left-color: var(--danger); }
    .table-wrap { overflow-x: auto; margin-top: 1rem; }
    table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.88rem; }
    th { background: #0f172a; color: var(--muted); padding: 0.75rem 1rem; font-weight: 600; border-bottom: 1px solid var(--border); }
    td { padding: 0.75rem 1rem; border-bottom: 1px solid var(--border); }
    .status-badge { padding: 0.25rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; }
    .status-ok { background: rgba(34, 197, 94, 0.2); color: #4ade80; border: 1px solid #22c55e; }
    .status-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .status-critical { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; }
    .nav-links { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 1rem; }
    .nav-link { color: var(--primary); text-decoration: none; font-weight: 600; display: inline-flex; align-items: center; gap: 0.35rem; }
    .nav-link:hover { text-decoration: underline; }
    #logBox { background: #020617; border: 1px solid var(--border); border-radius: 8px; padding: 1rem; font-family: monospace; font-size: 0.85rem; height: 180px; overflow-y: auto; color: #38bdf8; margin-top: 1rem; }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1 style="font-size: 1.8rem; font-weight: 800; color: #f8fafc;">Cold-Chain Produce Spoilage Alert Service</h1>
        <p style="color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem;">ISE2501 CA3: Software Testing & QA (Method 1) | Student Showcase Portal</p>
      </div>
      <div>
        <div class="badge"><div class="dot"></div> SERVICE ONLINE (127.0.0.1:8000)</div>
      </div>
    </header>

    <div class="grid">
      <!-- Card 1: Produce Assumptions -->
      <div class="card">
        <h3>🥬 Preloaded Produce Types</h3>
        <p style="color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem;">Configured safe temperature ranges (readings exactly on limit are safe):</p>
        <div class="produce-pill">
          <div><strong>Tomato</strong><div style="font-size: 0.75rem; color: var(--muted);">Solanum lycopersicum</div></div>
          <span style="color: var(--primary); font-weight: 700;">10.0°C – 15.0°C</span>
        </div>
        <div class="produce-pill">
          <div><strong>Leafy Greens</strong><div style="font-size: 0.75rem; color: var(--muted);">Spinach, Lettuce</div></div>
          <span style="color: var(--primary); font-weight: 700;">0.0°C – 4.0°C</span>
        </div>
        <div class="produce-pill">
          <div><strong>Mango</strong><div style="font-size: 0.75rem; color: var(--muted);">Mangifera indica</div></div>
          <span style="color: var(--primary); font-weight: 700;">10.0°C – 13.0°C</span>
        </div>
        <div style="margin-top: 1rem;">
          <a class="nav-link" href="/docs#/Produce/register_produce_produce_post" target="_blank">Register Custom Produce Type &rarr;</a>
        </div>
      </div>

      <!-- Card 2: Risk Scoring Rules -->
      <div class="card">
        <h3>⚖️ Spoilage Risk Calculation Engine</h3>
        <p style="color: var(--muted); font-size: 0.85rem; margin-bottom: 0.75rem;">Cumulative duration spent outside safe biological limits:</p>
        <div class="rule-item rule-ok">
          <strong>Level: OK (&lt; 30 min)</strong>
          <p style="color: var(--muted); font-size: 0.8rem;">Batch remains in nominal fresh condition. Zero alerts generated.</p>
        </div>
        <div class="rule-item rule-warn">
          <strong>Level: WARNING (30 to 119.9 min)</strong>
          <p style="color: var(--muted); font-size: 0.8rem;">Accelerated bacterial decay. SMS Alert dispatched to facility operator.</p>
        </div>
        <div class="rule-item rule-crit">
          <strong>Level: CRITICAL (&ge; 120 min)</strong>
          <p style="color: var(--muted); font-size: 0.8rem;">Severe thermal breach. Urgent spoilage notification dispatched.</p>
        </div>
      </div>

      <!-- Card 3: 1-Click Interactive Telemetry Simulator -->
      <div class="card">
        <h3>⚡ 1-Click Telemetry Simulation</h3>
        <p style="color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem;">Click any scenario to inject telemetry and evaluate live response:</p>
        <div class="sim-buttons">
          <button class="btn btn-primary" onclick="simulateBatch('normal')">
            <span>🍏</span> Simulate Safe Batch (Tomato, 12.5°C) &rarr; OK
          </button>
          <button class="btn btn-warning" onclick="simulateBatch('warning')">
            <span>⚠️</span> Simulate Thermal Breach (Tomato, 22°C, 45m) &rarr; WARNING
          </button>
          <button class="btn btn-danger" onclick="simulateBatch('critical')">
            <span>🚨</span> Simulate Critical Spoilage (Greens, 18°C, 150m) &rarr; CRITICAL
          </button>
        </div>
      </div>
    </div>

    <!-- Live Alerts Console -->
    <div class="card" style="margin-bottom: 2rem;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <h3>🔔 Active Spoilage Alerts Console</h3>
        <button class="btn btn-outline btn-sm" onclick="fetchAlerts()">↻ Refresh Alerts</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Alert ID</th>
              <th>Batch ID</th>
              <th>Produce</th>
              <th>Breach Duration</th>
              <th>Risk Level</th>
              <th>Status</th>
              <th>Created At</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="alertsBody">
            <tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 2rem;">Loading alerts...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Live Telemetry Log & Documentation Hub -->
    <div class="card">
      <h3>📡 Live Activity Terminal & API Documentation Hub</h3>
      <div id="logBox">System initialized. Ready to receive sensor telemetry readings...</div>
      <div class="nav-links">
        <a class="nav-link" href="/docs" target="_blank">📘 Interactive Swagger UI (/docs)</a>
        <a class="nav-link" href="/redoc" target="_blank">📑 OpenAPI ReDoc (/redoc)</a>
        <a class="nav-link" href="/openapi.json" target="_blank">🔌 OpenAPI JSON Schema</a>
        <a class="nav-link" href="https://github.com" target="_blank">💻 View on GitHub</a>
      </div>
    </div>
  </div>

  <script>
    let token = null;

    function log(msg) {
      const box = document.getElementById('logBox');
      const time = new Date().toLocaleTimeString();
      box.innerHTML = `[${time}] ${msg}<br>` + box.innerHTML;
    }

    async function login() {
      if (token) return token;
      try {
        const res = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: 'operator_alice', password: 'securepass123' })
        });
        const data = await res.json();
        token = data.access_token;
        log('Authenticated as operator_alice. JWT token acquired.');
        return token;
      } catch (e) {
        log('Auth error: ' + e);
      }
    }

    async function simulateBatch(type) {
      await login();
      const now = new Date();
      const batchId = 'DEMO-' + Math.floor(1000 + Math.random() * 9000);
      
      try {
        if (type === 'normal') {
          // Normal tomato reading
          const ts = new Date(now.getTime() - 10 * 60000).toISOString();
          const res = await fetch('/readings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({
              batch_id: batchId,
              produce_type: 'tomato',
              temperature_c: 12.5,
              humidity_pct: 65.0,
              timestamp: ts
            })
          });
          const d = await res.json();
          log(`[POST /readings] ${batchId} (Tomato @ 12.5°C) -> Status: ${d.risk_level} (Score: ${d.risk_score} min)`);
        } else if (type === 'warning') {
          // 2 readings: t0 safe, t1 (+45m) outside range -> WARNING
          const t0 = new Date(now.getTime() - 60 * 60000).toISOString();
          const t1 = new Date(now.getTime() - 15 * 60000).toISOString();
          await fetch('/readings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ batch_id: batchId, produce_type: 'tomato', temperature_c: 12.0, humidity_pct: 60.0, timestamp: t0 })
          });
          const res = await fetch('/readings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ batch_id: batchId, produce_type: 'tomato', temperature_c: 22.0, humidity_pct: 60.0, timestamp: t1 })
          });
          const d = await res.json();
          log(`⚠️ [WARNING ALERT TRIGGERED] ${batchId} (Tomato breach: 22.0°C for 45 min) -> SMS Sent!`);
        } else if (type === 'critical') {
          // Leafy greens (0-4C), 150 min at 18C -> CRITICAL
          const t0 = new Date(now.getTime() - 160 * 60000).toISOString();
          const t1 = new Date(now.getTime() - 10 * 60000).toISOString();
          await fetch('/readings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ batch_id: batchId, produce_type: 'leafy_greens', temperature_c: 2.0, humidity_pct: 85.0, timestamp: t0 })
          });
          const res = await fetch('/readings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ batch_id: batchId, produce_type: 'leafy_greens', temperature_c: 18.0, humidity_pct: 85.0, timestamp: t1 })
          });
          const d = await res.json();
          log(`🚨 [CRITICAL ALERT TRIGGERED] ${batchId} (Greens breach: 18.0°C for 150 min) -> Urgent SMS Escalation!`);
        }
        await fetchAlerts();
      } catch (e) {
        log('Simulation error: ' + e);
      }
    }

    async function fetchAlerts() {
      await login();
      try {
        const res = await fetch('/alerts', {
          headers: { 'Authorization': 'Bearer ' + token }
        });
        const data = await res.json();
        const tbody = document.getElementById('alertsBody');
        if (!data.alerts || data.alerts.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 1.5rem;">No active alerts. All produce batches within safe temperature ranges.</td></tr>';
          return;
        }
        tbody.innerHTML = data.alerts.map(a => `
          <tr>
            <td><code>${a.alert_id}</code></td>
            <td><strong>${a.batch_id}</strong></td>
            <td>${a.produce_type}</td>
            <td>${a.risk_score} min</td>
            <td><span class="status-badge status-${a.risk_level.toLowerCase()}">${a.risk_level}</span></td>
            <td><span style="font-size: 0.8rem; font-weight: 600; color: ${a.status === 'ACTIVE' ? 'var(--warning)' : 'var(--success)'}">${a.status}</span></td>
            <td style="font-size: 0.8rem; color: var(--muted);">${new Date(a.created_at).toLocaleTimeString()}</td>
            <td>
              ${a.status === 'ACTIVE' 
                ? `<button class="btn btn-outline btn-sm" onclick="ackAlert('${a.alert_id}')">Acknowledge</button>` 
                : `<span style="color: var(--success); font-size: 0.8rem;">✓ Resolved</span>`}
            </td>
          </tr>
        `).join('');
      } catch (e) {
        log('Failed to fetch alerts: ' + e);
      }
    }

    async function ackAlert(id) {
      await login();
      try {
        const res = await fetch(`/alerts/${id}/ack`, {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + token }
        });
        const d = await res.json();
        log(`[ACKNOWLEDGED] Alert ${id} was acknowledged by operator.`);
        await fetchAlerts();
      } catch (e) {
        log('Error acknowledging alert: ' + e);
      }
    }

    // Auto-fetch on initial page load
    window.onload = () => {
      fetchAlerts();
    };
  </script>
</body>
</html>
"""
