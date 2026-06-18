"""
Servidor Flask del chatbot de prediccion de Triatlon Elite Masculino.

Landing estilo FETRI (contenido de relleno) con un widget de chat flotante
abajo a la derecha. El chat usa Azure AI Foundry + modelo SHAP.

Verificadores de estado integrados en la cabecera del widget:
  - Modelo IA (Azure AI Foundry)
  - Modelo predictivo (SHAP / XGBoost)
  - Base de datos (Azure SQL)

Rutas:
  GET  /           -> landing FETRI + widget de chat
  POST /api/chat   -> procesa un mensaje
  POST /api/reset  -> reinicia la sesion
  GET  /api/status -> estado de los 3 componentes
  GET  /health     -> healthcheck simple
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

from flask import Flask, request, jsonify, Response
from chatbot.shap_explainer import get_explainer, FEATURE_LABELS, FEATURE_COLS
from chatbot.chat_logic import get_session, reset_session
from chatbot import ai_foundry, db_check

app = Flask(__name__)
app.config["JSON_ENSURE_ASCII"] = False

_foundry_histories: dict[str, list[dict]] = {}


def _model_status() -> dict:
    try:
        explainer = get_explainer()
        explainer.predict({"HIST_COUNT_PRUEBAS": 10, "RECENT_AVG_PUNTOS": 1000, "CHAMPIONSHIP_LEVEL": 2})
        kind = type(explainer.model).__name__
        return {"ok": True, "detail": f"Cargado ({kind})", "model": kind}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:120], "model": "—"}


# ===========================================================================
# UI — Landing FETRI (relleno) + widget de chat flotante
# ===========================================================================

CHAT_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Federacion Espanola de Triatlon</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --navy:#002b5c;--navy2:#013a73;--red:#e2001a;--gold:#f4b223;
  --gray:#f2f4f7;--line:#e2e6ec;--text:#1b2733;--muted:#6b7785;
  --ok:#34a853;--bad:#e2001a;--wait:#f4b223;
}
html,body{height:100%}
body{font-family:'Segoe UI',-apple-system,system-ui,Arial,sans-serif;background:#fff;
  color:var(--text);line-height:1.55}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}

/* ---------- Top utility bar ---------- */
.topbar{background:var(--navy);color:#fff;font-size:12.5px}
.topbar .in{max-width:1180px;margin:0 auto;padding:7px 20px;display:flex;align-items:center;gap:16px}
.topbar .sp{margin-left:auto;display:flex;gap:13px;font-size:14px}
.topbar .sp span{opacity:.85;cursor:pointer;transition:opacity .2s}
.topbar .sp span:hover{opacity:1}

/* ---------- Navbar ---------- */
.nav{background:#fff;border-bottom:3px solid var(--navy);position:sticky;top:0;z-index:50;
  box-shadow:0 2px 10px rgba(0,0,0,.05)}
.nav .in{max-width:1180px;margin:0 auto;padding:0 20px;display:flex;align-items:center;height:70px;gap:30px}
.logo{display:flex;align-items:center;gap:12px}
.logo .mk{width:46px;height:46px;background:var(--navy);border-radius:50%;display:flex;
  align-items:center;justify-content:center;font-size:24px;color:#fff;position:relative}
.logo .mk::after{content:"";position:absolute;inset:3px;border:2px solid var(--gold);border-radius:50%}
.logo b{font-size:15px;color:var(--navy);font-weight:800;letter-spacing:.3px;line-height:1.15}
.logo b small{display:block;font-size:10.5px;color:var(--muted);font-weight:600;letter-spacing:1px}
.menu{display:flex;gap:22px;margin-left:auto;font-size:13.5px;font-weight:600}
.menu a{color:var(--navy);padding:6px 0;border-bottom:2px solid transparent;transition:border-color .2s}
.menu a:hover{border-bottom-color:var(--red)}
@media(max-width:980px){.menu{display:none}}

/* ---------- Hero ---------- */
.hero{position:relative;height:440px;background:
  linear-gradient(120deg,rgba(0,43,92,.92) 0%,rgba(0,43,92,.55) 55%,rgba(1,58,115,.3) 100%),
  linear-gradient(60deg,#013a73,#0a5ca8 60%,#3aa0d8);overflow:hidden}
.hero::before{content:"\1F3CA  \1F6B4  \1F3C3";position:absolute;right:-10px;bottom:-30px;
  font-size:200px;opacity:.10;letter-spacing:20px;white-space:nowrap}
.hero .in{max-width:1180px;margin:0 auto;padding:0 20px;height:100%;display:flex;
  flex-direction:column;justify-content:center;position:relative;z-index:2}
.hero .tag{display:inline-block;background:var(--red);color:#fff;font-size:12px;font-weight:700;
  padding:5px 13px;border-radius:3px;letter-spacing:1px;width:fit-content;margin-bottom:16px}
.hero h1{color:#fff;font-size:42px;font-weight:800;max-width:680px;line-height:1.12;letter-spacing:-.5px}
.hero p{color:#dce6f2;font-size:17px;max-width:560px;margin-top:16px}
.hero .btn{margin-top:26px;background:var(--gold);color:var(--navy);font-weight:700;font-size:14px;
  padding:13px 28px;border-radius:4px;width:fit-content;cursor:pointer;transition:transform .15s}
.hero .btn:hover{transform:translateY(-2px)}
@media(max-width:680px){.hero h1{font-size:30px}.hero{height:380px}}

/* ---------- Sections ---------- */
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}
.sec{padding:56px 0}
.sec h2{font-size:13px;font-weight:800;color:var(--red);letter-spacing:2px;text-transform:uppercase;
  margin-bottom:6px}
.sec .h3{font-size:28px;font-weight:800;color:var(--navy);margin-bottom:30px;letter-spacing:-.4px}

/* News cards */
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:24px}
@media(max-width:880px){.grid{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.grid{grid-template-columns:1fr}}
.card{border:1px solid var(--line);border-radius:9px;overflow:hidden;background:#fff;
  transition:transform .18s,box-shadow .18s;cursor:pointer}
.card:hover{transform:translateY(-4px);box-shadow:0 12px 28px rgba(0,43,92,.13)}
.card .ph{height:165px;display:flex;align-items:center;justify-content:center;font-size:54px;color:#fff}
.c1{background:linear-gradient(135deg,#013a73,#0a5ca8)}
.c2{background:linear-gradient(135deg,#7a1018,#e2001a)}
.c3{background:linear-gradient(135deg,#b07d10,#f4b223)}
.c4{background:linear-gradient(135deg,#0a5ca8,#3aa0d8)}
.c5{background:linear-gradient(135deg,#1b2733,#46566a)}
.c6{background:linear-gradient(135deg,#0e6b4f,#2bb486)}
.card .bd{padding:17px 18px 22px}
.card .dt{font-size:11.5px;color:var(--red);font-weight:700;letter-spacing:.5px;text-transform:uppercase}
.card h4{font-size:16.5px;color:var(--navy);margin:8px 0 7px;font-weight:700;line-height:1.3}
.card p{font-size:13.5px;color:var(--muted)}

/* Stats band */
.band{background:var(--navy);color:#fff}
.band .in{max-width:1180px;margin:0 auto;padding:42px 20px;display:grid;
  grid-template-columns:repeat(4,1fr);gap:20px;text-align:center}
@media(max-width:680px){.band .in{grid-template-columns:1fr 1fr}}
.band .n{font-size:38px;font-weight:800;color:var(--gold)}
.band .l{font-size:13px;color:#bcd0e6;margin-top:4px;letter-spacing:.5px}

/* Sponsors */
.sponsors{background:var(--gray);padding:40px 0}
.sponsors .row{display:flex;flex-wrap:wrap;gap:18px;justify-content:center;align-items:center}
.sponsors .sp{background:#fff;border:1px solid var(--line);border-radius:7px;padding:16px 30px;
  font-weight:800;color:var(--navy);font-size:15px;opacity:.8}

/* Footer */
footer{background:#001a38;color:#9fb3c8;font-size:13px}
footer .in{max-width:1180px;margin:0 auto;padding:36px 20px;display:flex;justify-content:space-between;
  flex-wrap:wrap;gap:20px}
footer b{color:#fff;display:block;margin-bottom:8px;font-size:14px}
footer a{display:block;padding:3px 0;opacity:.85}

/* =================== CHAT WIDGET =================== */
.fab{position:fixed;right:24px;bottom:24px;width:64px;height:64px;border-radius:50%;
  background:var(--navy);color:#fff;border:none;cursor:pointer;z-index:200;
  box-shadow:0 8px 24px rgba(0,43,92,.4);display:flex;align-items:center;justify-content:center;
  font-size:28px;transition:transform .2s,background .2s}
.fab:hover{transform:scale(1.07);background:var(--navy2)}
.fab .badge{position:absolute;top:-2px;right:-2px;width:18px;height:18px;background:var(--red);
  border-radius:50%;border:2px solid #fff;font-size:10px;display:flex;align-items:center;justify-content:center}
.fab.hide{display:none}

.panel{position:fixed;right:24px;bottom:24px;width:390px;height:600px;max-height:calc(100vh - 40px);
  background:#fff;border-radius:16px;z-index:201;display:none;flex-direction:column;overflow:hidden;
  box-shadow:0 18px 50px rgba(0,0,0,.3);animation:pop .22s ease}
@keyframes pop{from{opacity:0;transform:translateY(20px) scale(.97)}to{opacity:1;transform:none}}
.panel.open{display:flex}
@media(max-width:480px){.panel{right:0;bottom:0;width:100%;height:100%;max-height:100%;border-radius:0}}

.ph-head{background:var(--navy);color:#fff;padding:15px 16px;display:flex;align-items:center;gap:12px}
.ph-head .ava{width:42px;height:42px;border-radius:50%;background:var(--navy2);display:flex;
  align-items:center;justify-content:center;font-size:21px;position:relative;flex-shrink:0}
.ph-head .ava::after{content:"";position:absolute;inset:2px;border:2px solid var(--gold);border-radius:50%}
.ph-head .ti b{font-size:15px;display:block}
.ph-head .ti small{font-size:11.5px;color:#bcd0e6}
.ph-head .x{margin-left:auto;background:transparent;border:none;color:#fff;font-size:22px;
  cursor:pointer;opacity:.8;width:30px;height:30px;border-radius:6px;transition:background .2s}
.ph-head .x:hover{background:rgba(255,255,255,.15);opacity:1}

.statusbar{display:flex;gap:6px;padding:8px 12px;background:#f7f9fb;border-bottom:1px solid var(--line);
  font-size:11px}
.st{display:flex;align-items:center;gap:5px;padding:3px 9px;background:#fff;border:1px solid var(--line);
  border-radius:20px;color:var(--muted)}
.st .led{width:7px;height:7px;border-radius:50%;background:var(--wait)}
.st .led.ok{background:var(--ok)}.st .led.bad{background:var(--bad)}
.st .led.wait{background:var(--wait);animation:pl 1.2s infinite}
@keyframes pl{0%,100%{opacity:.4}50%{opacity:1}}

.msgs{flex:1;overflow-y:auto;padding:18px 14px;background:#fbfcfd;display:flex;flex-direction:column;gap:14px}
.msgs::-webkit-scrollbar{width:6px}.msgs::-webkit-scrollbar-thumb{background:var(--line);border-radius:3px}
.m{display:flex;gap:9px;animation:fade .22s ease}
@keyframes fade{from{opacity:0;transform:translateY(5px)}to{opacity:1}}
.m .av{width:28px;height:28px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;
  justify-content:center;font-size:14px;margin-top:2px}
.m.b .av{background:var(--navy);color:#fff}
.m.u{flex-direction:row-reverse}
.m.u .av{background:var(--gray);border:1px solid var(--line)}
.m .bx{max-width:78%;padding:10px 13px;border-radius:13px;font-size:14px;line-height:1.62}
.m.b .bx{background:#fff;border:1px solid var(--line);border-top-left-radius:4px}
.m.u .bx{background:var(--navy);color:#fff;border-top-right-radius:4px}
.m .bx strong{font-weight:700}
.m .bx em{color:var(--muted);font-style:normal}
.m .bx .pos{color:var(--ok);font-weight:700}.m .bx .neg{color:var(--bad);font-weight:700}
.m .bx code{background:var(--gray);padding:1px 5px;border-radius:4px;font-size:12.5px}

.typing{display:flex;gap:4px;padding:4px 2px}
.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted);animation:bd 1.2s infinite}
.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes bd{0%,60%,100%{opacity:.3}30%{opacity:1;transform:translateY(-4px)}}

.chips2{display:flex;gap:7px;flex-wrap:wrap;padding:0 14px 8px;background:#fbfcfd}
.chip2{font-size:11.5px;background:#fff;border:1px solid var(--line);color:var(--navy);
  padding:6px 11px;border-radius:14px;cursor:pointer;transition:all .2s}
.chip2:hover{border-color:var(--navy);background:var(--navy);color:#fff}

.composer{padding:11px 12px;background:#fff;border-top:1px solid var(--line);display:flex;gap:9px;align-items:flex-end}
#inp{flex:1;border:1px solid var(--line);border-radius:11px;padding:10px 12px;font-size:14px;
  font-family:inherit;resize:none;max-height:120px;outline:none;line-height:1.45;transition:border-color .2s}
#inp:focus{border-color:var(--navy)}
.snd{width:40px;height:40px;border:none;border-radius:11px;background:var(--navy);color:#fff;cursor:pointer;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .2s,transform .1s}
.snd:hover{background:var(--navy2)}.snd:active{transform:scale(.93)}.snd:disabled{opacity:.4;cursor:default}
.snd svg{width:18px;height:18px;fill:#fff}
</style>
</head>
<body>

<!-- TOP BAR -->
<div class="topbar"><div class="in">
  <span>Area privada</span><span>Licencias</span><span>Tienda oficial</span>
  <div class="sp">
    <span>&#x1F426;</span><span>&#x1F4F7;</span><span>&#x25B6;</span><span>&#x1F44D;</span>
  </div>
</div></div>

<!-- NAVBAR -->
<nav class="nav"><div class="in">
  <a class="logo" href="#">
    <span class="mk">&#x1F3CA;</span>
    <b>FETRI<small>FEDERACION ESPANOLA DE TRIATLON</small></b>
  </a>
  <div class="menu">
    <a href="#">Competiciones</a><a href="#">Atletas</a><a href="#">Clubes</a>
    <a href="#">Rankings</a><a href="#">Grupos de edad</a><a href="#">Documentacion</a>
  </div>
</div></nav>

<!-- HERO -->
<section class="hero"><div class="in">
  <span class="tag">CAMPEONATO DE ESPANA</span>
  <h1>El triatlon espanol corre hacia una nueva temporada</h1>
  <p>Sigue en directo las pruebas del circuito nacional, los rankings de la elite masculina y todas las novedades de la FETRI.</p>
  <div class="btn" onclick="openChat()">Predice el rendimiento de un atleta &#x2192;</div>
</div></section>

<!-- STATS BAND -->
<div class="band"><div class="in">
  <div><div class="n">128</div><div class="l">PRUEBAS 2025</div></div>
  <div><div class="n">1.028</div><div class="l">ATLETAS</div></div>
  <div><div class="n">476</div><div class="l">CLUBES</div></div>
  <div><div class="n">52</div><div class="l">PROVINCIAS</div></div>
</div></div>

<!-- NEWS -->
<section class="sec"><div class="wrap">
  <h2>Actualidad</h2>
  <div class="h3">Ultimas noticias</div>
  <div class="grid">
    <div class="card"><div class="ph c1">&#x1F3C6;</div><div class="bd">
      <div class="dt">07 JUN 2025</div><h4>Cuatro medallas para Espana en la Copa de Europa</h4>
      <p>El equipo nacional brilla en la primera cita continental de la temporada.</p></div></div>
    <div class="card"><div class="ph c2">&#x1F6B4;</div><div class="bd">
      <div class="dt">05 JUN 2025</div><h4>Arranca el Circuito Nacional de Triatlon</h4>
      <p>Mas de 600 deportistas se citan en la prueba inaugural del calendario.</p></div></div>
    <div class="card"><div class="ph c3">&#x1F3CA;</div><div class="bd">
      <div class="dt">02 JUN 2025</div><h4>Nuevos criterios de clasificacion elite</h4>
      <p>La FETRI actualiza el sistema de puntos para la temporada 2025.</p></div></div>
    <div class="card"><div class="ph c4">&#x23F1;</div><div class="bd">
      <div class="dt">28 MAY 2025</div><h4>Records en la prueba de Pontevedra</h4>
      <p>Marcas historicas en natacion y segmento de bici en Galicia.</p></div></div>
    <div class="card"><div class="ph c5">&#x1F4CA;</div><div class="bd">
      <div class="dt">24 MAY 2025</div><h4>Analisis predictivo de la temporada</h4>
      <p>Estrenamos herramienta de prediccion de rendimiento por atleta.</p></div></div>
    <div class="card"><div class="ph c6">&#x1F947;</div><div class="bd">
      <div class="dt">20 MAY 2025</div><h4>Convocatoria del equipo nacional</h4>
      <p>Los seleccionados para el Campeonato de Europa de media distancia.</p></div></div>
  </div>
</div></section>

<!-- SPONSORS -->
<div class="sponsors"><div class="wrap">
  <div class="row">
    <div class="sp">PATROCINADOR</div><div class="sp">PARTNER OFICIAL</div>
    <div class="sp">IBERDROLA</div><div class="sp">LOTERIAS</div><div class="sp">CSD</div>
  </div>
</div></div>

<!-- FOOTER -->
<footer><div class="in">
  <div><b>FETRI</b><a href="#">Quienes somos</a><a href="#">Junta directiva</a><a href="#">Contacto</a></div>
  <div><b>Competir</b><a href="#">Calendario</a><a href="#">Rankings</a><a href="#">Resultados</a></div>
  <div><b>Recursos</b><a href="#">Normativa</a><a href="#">Documentacion</a><a href="#">Prensa</a></div>
  <div><b>Federacion Espanola de Triatlon</b><span style="opacity:.7">Pagina demostrativa &middot; TFM Conersys 2025</span></div>
</div></footer>

<!-- ====== CHAT WIDGET ====== -->
<button class="fab" id="fab" onclick="openChat()" title="Asistente de prediccion">
  &#x1F4AC;<span class="badge">1</span>
</button>

<div class="panel" id="panel">
  <div class="ph-head">
    <div class="ava">&#x1F3CA;</div>
    <div class="ti"><b>Coach Triatlon</b><small>Asistente de prediccion FETRI</small></div>
    <button class="x" onclick="closeChat()" title="Cerrar">&times;</button>
  </div>
  <div class="statusbar" id="statusbar">
    <div class="st" id="p-ia"><span class="led wait"></span>IA</div>
    <div class="st" id="p-model"><span class="led wait"></span>Modelo</div>
    <div class="st" id="p-db"><span class="led wait"></span>BBDD</div>
  </div>
  <div class="msgs" id="msgs"></div>
  <div class="chips2" id="chips">
    <span class="chip2" onclick="qs('Predice un atleta con 20 pruebas y media de 1400 puntos en un campeonato nacional')">Ejemplo de prediccion</span>
    <span class="chip2" onclick="qs('Como afecta el calor a una carrera?')">El calor en carrera</span>
  </div>
  <div class="composer">
    <textarea id="inp" rows="1" placeholder="Escribe tu mensaje..."
      oninput="autogrow(this)"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
    <button class="snd" id="sbtn" onclick="send()" title="Enviar">
      <svg viewBox="0 0 24 24"><path d="M3 20.5v-17L22 12 3 20.5zm2-3.1L16.85 12 5 6.6v3.9l6 1.5-6 1.5v3.9z"/></svg>
    </button>
  </div>
</div>

<script>
const fab=document.getElementById('fab');
const panel=document.getElementById('panel');
const msgsEl=document.getElementById('msgs');
const inp=document.getElementById('inp');
const sbtn=document.getElementById('sbtn');
const chips=document.getElementById('chips');
let sid='s'+Math.random().toString(36).slice(2);
let busy=false, started=false;

function openChat(){
  panel.classList.add('open');fab.classList.add('hide');
  if(!started){started=true;greet();loadStatus();setInterval(loadStatus,30000);}
  setTimeout(()=>inp.focus(),100);
}
function closeChat(){panel.classList.remove('open');fab.classList.remove('hide');}

function autogrow(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,120)+'px';}

function fmt(t){
  t=t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  t=t.replace(/`([^`]+)`/g,'<code>$1</code>');
  t=t.replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
  t=t.replace(/&#x25B2;|▲/g,'<span class="pos">&#x25B2;</span>');
  t=t.replace(/&#x25BC;|▼/g,'<span class="neg">&#x25BC;</span>');
  t=t.replace(/\n/g,'<br>');
  return t;
}
function add(role,html){
  const m=document.createElement('div');
  m.className='m '+(role==='b'?'b':'u');
  const av=role==='b'?'&#x1F3CA;':'&#x1F464;';
  m.innerHTML='<div class="av">'+av+'</div><div class="bx">'+html+'</div>';
  msgsEl.appendChild(m);msgsEl.scrollTop=msgsEl.scrollHeight;return m;
}
function typing(){
  const m=document.createElement('div');m.className='m b';m.id='typing';
  m.innerHTML='<div class="av">&#x1F3CA;</div><div class="bx"><div class="typing"><i></i><i></i><i></i></div></div>';
  msgsEl.appendChild(m);msgsEl.scrollTop=msgsEl.scrollHeight;
}
function stopTyping(){const t=document.getElementById('typing');if(t)t.remove();}

function greet(){
  add('b',fmt(
    'Hola, soy **Coach** &#x1F3CA;&#x1F6B4;&#x1F3C3;\n\n'+
    'Predigo el rendimiento de los atletas de triatlon y te explico por que. '+
    'Cuentame sobre un atleta o una prueba, o usa un ejemplo de abajo.'
  ));
}

async function send(){
  const txt=inp.value.trim();
  if(!txt||busy)return;
  busy=true;sbtn.disabled=true;
  if(chips)chips.style.display='none';
  inp.value='';autogrow(inp);
  add('u',txt.replace(/</g,'&lt;').replace(/\n/g,'<br>'));
  typing();
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:txt,session_id:sid})});
    const d=await r.json();
    stopTyping();add('b',fmt(d.response||'Sin respuesta.'));
  }catch(e){
    stopTyping();add('b','<span class="neg">Error de conexion.</span> Comprueba que el servidor esta arrancado.');
  }finally{busy=false;sbtn.disabled=false;inp.focus();}
}
function qs(t){inp.value=t;send();}

function setPill(id,ok,detail){
  const p=document.getElementById(id);
  p.querySelector('.led').className='led '+(ok===true?'ok':ok===false?'bad':'wait');
  if(detail)p.title=detail;
}
async function loadStatus(){
  try{
    const d=await(await fetch('/api/status')).json();
    setPill('p-ia',d.ia.ok,'IA: '+d.ia.detail);
    setPill('p-model',d.model.ok,'Modelo: '+d.model.detail);
    setPill('p-db',d.db.ok,'BBDD: '+d.db.detail);
  }catch(e){setPill('p-ia',false);setPill('p-model',false);setPill('p-db',false);}
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def index():
    resp = Response(CHAT_HTML, content_type="text/html; charset=utf-8")
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.route("/api/status", methods=["GET"])
def status():
    """Estado de los 3 componentes: IA, modelo predictivo y BBDD."""
    return jsonify({
        "ia":    ai_foundry.ping(),
        "model": _model_status(),
        "db":    db_check.ping(),
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    msg  = data.get("message", "").strip()
    sid  = data.get("session_id", "default")

    if not msg:
        return jsonify({"response": "No he recibido ningun mensaje."})

    if ai_foundry.is_configured():
        try:
            history = _foundry_histories.get(sid, [])
            history = history + [{"role": "user", "content": msg}]
            response_text, history = ai_foundry.chat(history)
            _foundry_histories[sid] = history
            return jsonify({"response": response_text, "mode": "ai_foundry"})
        except Exception:
            session  = get_session(sid)
            fallback = session.process(msg)
            note = "*(IA no disponible, usando modo local)*\n\n"
            return jsonify({"response": note + fallback, "mode": "error"})

    session  = get_session(sid)
    response = session.process(msg)
    return jsonify({"response": response, "mode": "rule_based"})


@app.route("/api/reset", methods=["POST"])
def reset():
    data = request.get_json(force=True, silent=True) or {}
    sid  = data.get("session_id", "default")
    reset_session(sid)
    _foundry_histories.pop(sid, None)
    return jsonify({"status": "ok"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "triathlon-shap-chatbot"})


@app.route("/features", methods=["GET"])
def features_info():
    return jsonify({
        "features": [
            {"name": col, "description": FEATURE_LABELS.get(col, col)}
            for col in FEATURE_COLS
        ],
    })


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True, silent=True)
    if data is None:
        return jsonify({"error": "Body JSON requerido"}), 400
    try:
        explainer = get_explainer()
        top_n = int(data.pop("top_n", 5))
        return jsonify(explainer.explain(data, top_n=top_n))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 55)
    print(" Chatbot Triatlon Predictor - Landing FETRI")
    print("=" * 55)
    print("Cargando modelo predictivo...")
    get_explainer()
    print("AI Foundry:", "configurado" if ai_foundry.is_configured() else "no configurado")
    print("-" * 55)
    print(" Abre:  http://localhost:5050")
    print("=" * 55)
    app.run(host="0.0.0.0", port=5050, debug=False)
