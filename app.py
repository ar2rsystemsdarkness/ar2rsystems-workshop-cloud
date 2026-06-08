
from flask import Flask, request, jsonify, send_from_directory, redirect
import os, json, datetime, uuid, html

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
TICKETS = os.path.join(DATA, "tickets")
QUOTES = os.path.join(DATA, "quotes")
for p in [DATA, TICKETS, QUOTES]:
    os.makedirs(p, exist_ok=True)

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def money(n):
    try:
        return "${:,.2f}".format(float(n))
    except Exception:
        return "$0.00"

def as_dict(value):
    return value if isinstance(value, dict) else {}

def as_list(value):
    return value if isinstance(value, list) else []

def safe_str(value):
    if value is None:
        return ""
    return str(value)

def read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def all_json(folder):
    rows = []
    if not os.path.isdir(folder):
        return rows
    for name in sorted(os.listdir(folder), reverse=True):
        if name.endswith(".json"):
            obj = read_json(os.path.join(folder, name))
            if obj:
                rows.append(obj)
    return rows

def save_ticket(obj):
    if not obj.get("ticket_id"):
        obj["ticket_id"] = "T-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + str(uuid.uuid4())[:5]
    obj.setdefault("status", "PENDIENTE_COTIZACION")
    obj.setdefault("created_at", now())
    obj["updated_at"] = now()
    write_json(os.path.join(TICKETS, obj["ticket_id"] + ".json"), obj)
    return obj

def save_quote(obj):
    if not obj.get("quote_id"):
        obj["quote_id"] = "Q-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + str(uuid.uuid4())[:5]
    obj["created_at"] = now()
    write_json(os.path.join(QUOTES, obj["quote_id"] + ".json"), obj)
    if obj.get("ticket_id"):
        t = get_ticket(obj["ticket_id"])
        if t:
            t["status"] = "COTIZADO"
            t["quote_id"] = obj["quote_id"]
            save_ticket(t)
    return obj

def get_ticket(tid):
    if not tid:
        return None
    return read_json(os.path.join(TICKETS, tid + ".json"))

STYLE = """
<style>
body{margin:0;font-family:Segoe UI,Arial;background:#080b12;color:#f7f7f7}
aside{position:fixed;left:0;top:0;bottom:0;width:245px;background:#0c111d;border-right:1px solid #2b3852;padding:18px}
.brand{text-align:center}.brand img{width:115px}.brand h2{color:#f5d76e;margin:8px 0 0}.brand span{color:#64ffd2;font-size:13px}
aside a{display:block;padding:13px 14px;border-radius:14px;color:#f7f7f7;text-decoration:none;margin:8px 0}
aside a:hover,.on{background:#1c2940;color:#f5d76e}
main{margin-left:245px;padding:26px}h1{color:#f5d76e;margin-top:0}
.card{background:#131a26;border:1px solid #2b3852;border-radius:22px;padding:18px;margin:16px 0;box-shadow:0 18px 45px rgba(0,0,0,.25)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}
.kpi{background:#0f1725;border:1px solid #2b3852;border-radius:18px;padding:16px}.kpi b{display:block;font-size:26px;color:#64ffd2}
table{width:100%;border-collapse:collapse;background:#131a26;border-radius:18px;overflow:hidden}
th,td{padding:11px;border-bottom:1px solid #2b3852;text-align:left;vertical-align:top}th{color:#f5d76e;background:#101827}
input,textarea{width:100%;box-sizing:border-box;background:#0f1725;color:white;border:1px solid #2b3852;border-radius:14px;padding:11px;margin:6px 0}
button,.btn{display:inline-block;background:#24324d;color:white;border:0;border-radius:14px;padding:10px 14px;margin:5px;text-decoration:none;font-weight:700;cursor:pointer}
.primary{background:#f5d76e;color:#080b12}.danger{background:#652032}
.badge{display:inline-block;padding:5px 9px;border-radius:999px;background:#0f1725;border:1px solid #2b3852;font-size:12px;margin:2px;color:#aeb7c8}
.small{color:#aeb7c8;font-size:13px}.total{font-size:28px;font-weight:900;color:#f5d76e;text-align:right}
@media(max-width:850px){aside{position:relative;width:auto}main{margin-left:0}}
</style>
"""

def layout(title, body, active="tickets"):
    def on(x): return "on" if active == x else ""
    nav = f"""
    <aside>
      <div class="brand"><img src="/static/ar2rsystems_logo.png"><h2>ar2rsystems</h2><span>workshop cloud</span></div>
      <a class="{on('tickets')}" href="/">Tickets</a>
      <a class="{on('quote')}" href="/quote">Nueva cotizacion</a>
      <a class="{on('dashboard')}" href="/dashboard">Dashboard</a>
      <a class="{on('settings')}" href="/settings">Scanner</a>
    </aside>
    """
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>{STYLE}</head><body>{nav}<main>{body}</main></body></html>'


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(BASE, "static"), "ar2rsystems_logo.png")

@app.route("/static/<path:name>")
def static_files(name):
    return send_from_directory(os.path.join(BASE, "static"), name)

@app.route("/api/tickets", methods=["GET", "POST"])
@app.route("/api/scans", methods=["GET", "POST"])
def api_tickets():
    if request.method == "GET":
        return jsonify(all_json(TICKETS))
    obj = request.get_json(force=True, silent=True) or {}
    return jsonify({"ok": True, "ticket": save_ticket(obj)})

@app.route("/api/quotes", methods=["GET", "POST"])
def api_quotes():
    if request.method == "GET":
        return jsonify(all_json(QUOTES))
    obj = request.get_json(force=True, silent=True) or {}
    return jsonify({"ok": True, "quote": save_quote(obj)})

@app.route("/")
def tickets_page():
    tickets = all_json(TICKETS)
    rows = ""
    for t in tickets:
        eq = as_dict(t.get("equipo"))
        rows += f"""
        <tr>
          <td><b>{html.escape(t.get('ticket_id',''))}</b><br><span class="small">{html.escape(t.get('created_at',''))}</span></td>
          <td>{html.escape(t.get('cliente','SIN CLIENTE'))}<br><span class="small">{html.escape(t.get('whatsapp',''))}</span></td>
          <td>{html.escape(eq.get('marca',''))} {html.escape(eq.get('modelo',''))}<br><span class="small">{html.escape(eq.get('serie',''))}</span></td>
          <td><span class="badge">Score {html.escape(str(t.get('score','')))}/100</span><span class="badge">Piezas: {'SI' if t.get('cotizar_piezas') else 'NO'}</span><span class="badge">Sistema: {'SI' if t.get('actualizacion_sistema') else 'NO'}</span></td>
          <td>{html.escape(t.get('status',''))}</td>
          <td><a class="btn primary" href="/quote?ticket={html.escape(t.get('ticket_id',''))}">Cotizar</a><a class="btn" href="/ticket/{html.escape(t.get('ticket_id',''))}">Ver</a></td>
        </tr>"""
    body = f"""
    <h1>Tickets de servicio para cotizacion</h1>
    <div class="grid">
      <div class="kpi"><span>Pendientes</span><b>{len([t for t in tickets if t.get('status')!='COTIZADO'])}</b></div>
      <div class="kpi"><span>Total tickets</span><b>{len(tickets)}</b></div>
      <div class="kpi"><span>Cloud</span><b>ONLINE</b><span class="small">internet</span></div>
    </div>
    <div class="card"><a class="btn primary" href="/quote">Cotizacion manual</a><button onclick="location.reload()">Actualizar</button></div>
    <table><tr><th>Ticket</th><th>Cliente</th><th>Equipo</th><th>Diagnostico</th><th>Estado</th><th>Acciones</th></tr>{rows}</table>
    <script>setTimeout(()=>location.reload(),10000)</script>
    """
    return layout("Tickets", body, "tickets")

@app.route("/ticket/<tid>")
def ticket_page(tid):
    t = get_ticket(tid)
    if not t:
        return layout("No encontrado", "<h1>No encontre el ticket</h1>")
    eq = as_dict(t.get("equipo"))
    disks = "".join([f"<tr><td>{html.escape(str(as_dict(d).get('modelo','')))}</td><td>{html.escape(str(as_dict(d).get('tipo','')))}</td><td>{html.escape(str(as_dict(d).get('gb','')))}</td></tr>" for d in as_list(t.get("discos"))])
    drivers = "".join([f"<tr><td>{html.escape(str(as_dict(d).get('dispositivo','')))}</td><td>{html.escape(str(as_dict(d).get('hardwareID','')))}</td></tr>" for d in as_list(t.get("drivers"))])
    recs = "".join([f"<li>{html.escape(str(r))}</li>" for r in as_list(t.get("recomendaciones"))])
    body = f"""
    <h1>Ticket {html.escape(tid)}</h1>
    <div class="card"><b>Equipo:</b> {html.escape(eq.get('marca',''))} {html.escape(eq.get('modelo',''))}<br><b>Serie:</b> {html.escape(eq.get('serie',''))}<br><b>CPU:</b> {html.escape(eq.get('cpu',''))}<br><b>RAM:</b> {html.escape(str(eq.get('ram_instalada','')))} GB<br><b>Score:</b> {html.escape(str(t.get('score','')))}/100</div>
    <div class="card"><h2>Recomendaciones</h2><ul>{recs}</ul></div>
    <div class="card"><h2>Discos</h2><table><tr><th>Modelo</th><th>Tipo</th><th>GB</th></tr>{disks}</table></div>
    <div class="card"><h2>Drivers</h2><table><tr><th>Dispositivo</th><th>Hardware ID</th></tr>{drivers}</table></div>
    <a class="btn primary" href="/quote?ticket={html.escape(tid)}">Cotizar este ticket</a>
    """
    return layout("Ticket", body, "tickets")

@app.route("/quote")
def quote_page():
    tid = request.args.get("ticket")
    t = get_ticket(tid) if tid else None
    eq = as_dict(t.get("equipo")) if t else {}
    cliente = t.get("cliente","") if t else ""
    whatsapp = t.get("whatsapp","") if t else ""
    equipo = (eq.get("marca","") + " " + eq.get("modelo","")).strip()
    falla = ""
    if t:
        falla = f"Ticket {t.get('ticket_id')} Score {t.get('score')}/100. " + " ".join([str(x) for x in as_list(t.get("recomendaciones"))])
    js_ticket = json.dumps(t, ensure_ascii=False) if t else "null"
    body = f"""
    <h1>{'Cotizar ticket' if t else 'Cotizacion manual'}</h1>
    <div class="card">
      <input id="ticket_id" type="hidden" value="{html.escape(tid or '')}">
      <div class="grid">
        <div><label>Cliente</label><input id="client" value="{html.escape(cliente)}"></div>
        <div><label>WhatsApp</label><input id="phone" value="{html.escape(whatsapp)}" placeholder="4771234567"></div>
        <div><label>Equipo</label><input id="device" value="{html.escape(equipo)}"></div>
      </div>
      <label>Falla / diagnostico</label><textarea id="problem">{html.escape(falla)}</textarea>
    </div>
    <div class="card">
      <h2>Agregar concepto</h2>
      <div class="grid"><input id="concept" value="SSD 480 GB"><input id="cost" value="400" type="number"><input id="profit" value="300" type="number"><input id="labor" value="500" type="number"></div>
      <button class="primary" onclick="addItem()">Agregar</button><button onclick="searchML()">Buscar Mercado Libre</button><button onclick="searchAmazon()">Buscar Amazon</button><button onclick="addSuggested()">Agregar sugeridos</button>
    </div>
    <div class="card"><h2>Conceptos</h2><div id="items"></div><div class="total" id="total">Total: $0.00</div><button class="primary" onclick="saveQuote()">Guardar cotizacion</button><button onclick="sendWhatsApp()">Enviar por WhatsApp</button><button onclick="clientPreview()">Vista cliente</button></div>
    <script>
      let ticket = {js_ticket}; let items = [];
      function money(n){{return new Intl.NumberFormat('es-MX',{{style:'currency',currency:'MXN'}}).format(n||0)}}
      function addItemObj(i){{i.client=(+i.cost||0)+(+i.profit||0)+(+i.labor||0);i.gain=(+i.profit||0)+(+i.labor||0);items.push(i);renderItems();}}
      function addItem(){{addItemObj({{name:concept.value||'Concepto',cost:+cost.value||0,profit:+profit.value||0,labor:+labor.value||0}})}}
      function addSuggested(){{if(!ticket)return;if(ticket.cotizar_piezas)addItemObj({{name:'Revision y cotizacion de piezas',cost:0,profit:0,labor:250}});if(ticket.actualizacion_sistema)addItemObj({{name:'Actualizacion / instalacion de sistema',cost:0,profit:0,labor:500}});(ticket.recomendaciones||[]).forEach(r=>{{if(r.includes('HDD'))addItemObj({{name:'Migracion a SSD',cost:0,profit:0,labor:500}});if(r.includes('Driver'))addItemObj({{name:'Instalacion de drivers',cost:0,profit:0,labor:300}});}});}}
      function renderItems(){{let total=items.reduce((a,b)=>a+b.client,0);document.getElementById('items').innerHTML=items.map((x,idx)=>`<div class="card"><b>${{x.name}}</b><br><span class="small">Cliente: ${{money(x.client)}} | Interno: costo ${{money(x.cost)}} utilidad ${{money(x.gain)}}</span><br><button class="danger" onclick="items.splice(${{idx}},1);renderItems()">Quitar</button></div>`).join('');document.getElementById('total').innerText='Total: '+money(total);}}
      function quoteObj(){{return {{ticket_id:ticket_id.value,client:client.value,phone:phone.value,device:device.value,problem:problem.value,items,totalClient:items.reduce((a,b)=>a+b.client,0),realCost:items.reduce((a,b)=>a+(+b.cost||0),0),internalGain:items.reduce((a,b)=>a+b.gain,0)}}}}
      async function saveQuote(){{const r=await fetch('/api/quotes',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(quoteObj())}});alert(r.ok?'Cotizacion guardada':'Error');}}
      function textQuote(){{let q=quoteObj();return `ar2rsystems\\nCotizacion\\n\\nCliente: ${{q.client}}\\nEquipo: ${{q.device}}\\nFalla: ${{q.problem}}\\n\\n${{items.map(i=>i.name+': '+money(i.client)).join('\\n')}}\\n\\nTotal: ${{money(q.totalClient)}}`;}}
      function sendWhatsApp(){{let p=phone.value.replace(/\\D/g,'');if(p.length==10)p='52'+p;window.open('https://wa.me/'+p+'?text='+encodeURIComponent(textQuote()),'_blank');}}
      function clientPreview(){{alert(textQuote())}}
      function searchML(){{window.open('https://listado.mercadolibre.com.mx/'+encodeURIComponent(concept.value),'_blank')}}
      function searchAmazon(){{window.open('https://www.amazon.com.mx/s?k='+encodeURIComponent(concept.value),'_blank')}}
    </script>
    """
    return layout("Cotizacion", body, "quote")

@app.route("/dashboard")
def dashboard_page():
    tickets = all_json(TICKETS)
    quotes = all_json(QUOTES)
    total = sum(float(q.get("totalClient",0) or 0) for q in quotes)
    gain = sum(float(q.get("internalGain",0) or 0) for q in quotes)
    body = f"<h1>Dashboard</h1><div class='grid'><div class='kpi'><span>Tickets</span><b>{len(tickets)}</b></div><div class='kpi'><span>Cotizaciones</span><b>{len(quotes)}</b></div><div class='kpi'><span>Ingresos cotizados</span><b>{money(total)}</b></div><div class='kpi'><span>Ganancia interna</span><b>{money(gain)}</b></div></div>"
    return layout("Dashboard", body, "dashboard")

@app.route("/settings")
def settings_page():
    body = """
    <h1>Scanner cloud</h1>
    <div class='card'>
      <p>Pon esta URL en el scanner:</p>
      <h2>https://ar2rsystems-workshop-cloud.onrender.com</h2>
      <p>Mientras pruebas local:</p>
      <h2>http://localhost:5050</h2>
    </div>
    """
    return layout("Scanner", body, "settings")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5050)))
