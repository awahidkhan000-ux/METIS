import gemini_brief
from flask import Flask, render_template_string, jsonify
import threading

app = Flask(__name__)
cache = {"data": None, "loading": False}

HTML = """<!DOCTYPE html>
<html>
<head>
<title>METIS — Metals Intelligence</title>
<meta charset="utf-8">
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#0a0a0f; color:#e8e8e8; font-family:'Courier New',monospace; padding:2rem; }
h1 { font-size:1.6rem; letter-spacing:0.4em; color:#fff; margin-bottom:0.2rem; }
.sub { color:#444; font-size:0.75rem; letter-spacing:0.3em; margin-bottom:2.5rem; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:1rem; margin-bottom:2rem; }
.card { border:1px solid #1a1a2e; padding:1.2rem; cursor:pointer; transition:all 0.2s; }
.card:hover { border-color:#444; }
.card.HIGH { border-top:3px solid #e74c3c; }
.card.MEDIUM { border-top:3px solid #f39c12; }
.card.LOW { border-top:3px solid #27ae60; }
.card-name { font-size:0.65rem; letter-spacing:0.3em; color:#555; margin-bottom:0.5rem; }
.card-price { font-size:1.8rem; color:#fff; font-weight:bold; }
.card-unit { font-size:0.65rem; color:#444; margin-bottom:0.8rem; }
.badge { font-size:0.65rem; padding:3px 10px; letter-spacing:0.15em; display:inline-block; }
.badge.HIGH { background:#2d0a0a; color:#e74c3c; }
.badge.MEDIUM { background:#2d1a00; color:#f39c12; }
.badge.LOW { background:#0a2d0a; color:#27ae60; }
.detail { display:none; border:1px solid #1a1a2e; padding:1.5rem; margin-bottom:1.5rem; }
.detail.active { display:block; }
.detail-title { font-size:0.7rem; letter-spacing:0.3em; color:#555; margin-bottom:1.5rem; }
.route { border-left:2px solid #1a1a2e; padding-left:1rem; margin-bottom:1.5rem; }
.route-name { font-size:0.8rem; color:#888; margin-bottom:0.3rem; }
.route-choke { font-size:0.7rem; color:#444; margin-bottom:0.8rem; }
.brief { font-size:0.82rem; line-height:1.8; color:#aaa; white-space:pre-wrap; }
.close { font-size:0.7rem; color:#333; cursor:pointer; letter-spacing:0.2em; margin-top:1rem; display:inline-block; }
.close:hover { color:#888; }
footer { color:#222; font-size:0.65rem; letter-spacing:0.15em; margin-top:3rem; border-top:1px solid #111; padding-top:1rem; }
.status { color:#444; font-size:0.75rem; letter-spacing:0.2em; margin-bottom:1rem; }
.status.live { color:#27ae60; }
</style>
</head>
<body>
<h1>METIS</h1>
<p class="sub">METALS SUPPLY CHAIN DISRUPTION INTELLIGENCE</p>
<p class="status" id="status">[ LOADING LIVE DATA... ]</p>
<div class="grid" id="grid"></div>
<div id="details"></div>
<footer>METIS v1 &nbsp;|&nbsp; LIVE DATA: YAHOO FINANCE · OPEN.ER-API · GOOGLE NEWS &nbsp;|&nbsp; AI: OPENROUTER</footer>
<script>
function toggle(name) {
  document.querySelectorAll('.detail').forEach(d => d.classList.remove('active'));
  document.getElementById('d-' + name).classList.toggle('active');
}
function render(metals) {
  const grid = document.getElementById('grid');
  const details = document.getElementById('details');
  grid.innerHTML = '';
  details.innerHTML = '';
  metals.forEach(m => {
    grid.innerHTML += `<div class="card ${m.risk}" onclick="toggle('${m.name}')">
      <div class="card-name">${m.name.toUpperCase()}</div>
      <div class="card-price">${m.price}</div>
      <div class="card-unit">${m.unit}</div>
      <div class="badge ${m.risk}">${m.risk} RISK</div>
    </div>`;
    let routeHtml = m.routes.map(r => `<div class="route">
      <div class="route-name">${r.name}</div>
      <div class="route-choke">${r.choke}</div>
      <div class="brief">${r.brief}</div>
    </div>`).join('');
    details.innerHTML += `<div class="detail" id="d-${m.name}">
      <div class="detail-title">${m.name.toUpperCase()} — ROUTE INTELLIGENCE | ${m.fx}</div>
      ${routeHtml}
      <span class="close" onclick="toggle('${m.name}')">[ CLOSE ]</span>
    </div>`;
  });
  document.getElementById('status').textContent = '[ LIVE — ' + new Date().toUTCString() + ' ]';
  document.getElementById('status').className = 'status live';
}
function poll() {
  fetch('/data').then(r => r.json()).then(data => {
    if (data.ready) { render(data.metals); }
    else { setTimeout(poll, 3000); }
  }).catch(() => setTimeout(poll, 5000));
}
poll();
</script>
</body>
</html>"""

def get_risk(results):
    for brief in results.values():
        if "RISK: HIGH" in brief:
            return "HIGH"
    for brief in results.values():
        if "RISK: MEDIUM" in brief:
            return "MEDIUM"
    return "LOW"

def load_data():
    cache["loading"] = True
    metals = []
    for name, config in gemini_brief.METALS.items():
        price, fx_rate, results = gemini_brief.process_metal(name, config)
        base, target = config["currency_pair"]
        routes = []
        for r in config["routes"]:
            routes.append({
                "name": r["name"],
                "choke": ", ".join(r["chokepoints"]),
                "brief": results.get(r["name"], "Unavailable.")
            })
        metals.append({
            "name": name,
            "price": str(price or "—"),
            "unit": config["unit"],
            "fx": f"{base}/{target}: {fx_rate}",
            "risk": get_risk(results),
            "routes": routes
        })
    cache["data"] = metals
    cache["loading"] = False

@app.route("/")
def index():
    if not cache["loading"] and cache["data"] is None:
        t = threading.Thread(target=load_data)
        t.daemon = True
        t.start()
    return render_template_string(HTML)

@app.route("/data")
def data():
    if cache["data"]:
        return jsonify({"ready": True, "metals": cache["data"]})
    return jsonify({"ready": False})

if __name__ == "__main__":
    app.run(debug=True)