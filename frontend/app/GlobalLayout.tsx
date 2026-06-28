'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function GlobalLayout({ children }: { children: React.ReactNode }) {
  const [chatOpen, setChatOpen] = useState(false);
  const [messages, setMessages] = useState<{role: 'u'|'b', html: string, id: number}[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState({ ia: {ok:null}, model: {ok:null}, db: {ok:null} });
  const [sid] = useState('s' + Math.random().toString(36).slice(2));
  const msgsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (chatOpen && messages.length === 0) {
      greet();
      loadStatus();
    }
  }, [chatOpen]);

  useEffect(() => {
    msgsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const loadStatus = async () => {
    try {
      const r = await fetch('/api/status');
      const d = await r.json();
      setStatus(d);
    } catch(e) {}
  };

  const fmt = (t: string) => {
    let html = t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    html = html.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
    html = html.replace(/`([^`]+)`/g,'<code>$1</code>');
    html = html.replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
    html = html.replace(/&#x25B2;|▲/g,'<span class="pos">&#x25B2;</span>');
    html = html.replace(/&#x25BC;|▼/g,'<span class="neg">&#x25BC;</span>');
    html = html.replace(/\n/g,'<br>');
    return html;
  };

  const typeText = async (role: 'b', fullText: string, speed = 15) => {
    const id = Date.now();
    setMessages(prev => [...prev, { role, html: '<span class="cursor"></span>', id }]);
    
    let currentText = '';
    const chars = Array.from(fullText);
    
    for (let i = 0; i < chars.length; i++) {
      currentText += chars[i];
      setMessages(prev => prev.map(m => m.id === id ? { ...m, html: fmt(currentText) + '<span class="cursor"></span>' } : m));
      await new Promise(r => setTimeout(r, speed));
    }
    setMessages(prev => prev.map(m => m.id === id ? { ...m, html: fmt(fullText) } : m));
  };

  const greet = async () => {
    const msg = '¡Hola! Soy **Coach FETRI**, tu analista predictivo 🧠\n\n' +
    'Me baso en el historial de nuestros triatletas y en nuestro modelo de inteligencia artificial **Azure ML** para predecir posiciones, detectar anomalías de rendimiento y explicarte las causas.\n\n' +
    '¿De quién quieres conocer la predicción hoy? Cuéntame sobre un atleta, o usa uno de los ejemplos de abajo.';
    await typeText('b', msg, 20);
  };

  const sendMsg = async () => {
    if(!inputValue.trim() || busy) return;
    const txt = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'u', html: fmt(txt), id: Date.now() }]);
    setBusy(true);
    setIsTyping(true);
    
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ message: txt, session_id: sid })
      });
      const d = await r.json();
      setIsTyping(false);
      setMessages(prev => [...prev, { role: 'b', html: fmt(d.response || 'Sin respuesta.'), id: Date.now() }]);
    } catch(e) {
      setIsTyping(false);
      setMessages(prev => [...prev, { role: 'b', html: '<span class="neg">Error de conexión.</span>', id: Date.now() }]);
    } finally {
      setBusy(false);
    }
  };

  const pathname = usePathname();

  return (
    <div className="landing-page" style={{minHeight: '100vh', display: 'flex', flexDirection: 'column'}}>
      {/* Top Bar Fixa */}
      <div className="topbar">
        <div className="in">
          <b>FEDERACIÓN ESPAÑOLA DE TRIATLÓN</b>
          <div className="sp">
            <Link href="/" style={{textDecoration:'none', color:'inherit'}}>Noticias</Link>
            <Link href="/dashboard/diccionario" style={{textDecoration:'none', color:'inherit'}}>Reglamento</Link>
            <Link href="/clubes" style={{textDecoration:'none', color:'inherit'}}>Federarse</Link>
          </div>
        </div>
      </div>
      
      {/* Nav Fixa */}
      <div className="nav" style={{position:'sticky', top:0, zIndex:999}}>
        <div className="in">
          <Link href="/" style={{textDecoration:'none', color:'inherit'}}>
            <div className="logo">
              <div className="mk">&#x25B2;</div>
              <div>
                <b>FETRI</b>
                <small>FEDERACIÓN ESPAÑOLA DE TRIATLÓN</small>
              </div>
            </div>
          </Link>
          <div className="menu">
            <Link href="/competiciones" style={{
              color: pathname === '/competiciones' ? 'var(--red)' : 'inherit', 
              borderBottom: pathname === '/competiciones' ? '2px solid var(--red)' : 'none',
              textDecoration:'none', fontWeight:600}}>COMPETICIONES</Link>
            <Link href="/clubes" style={{
              color: pathname === '/clubes' ? 'var(--red)' : 'inherit', 
              borderBottom: pathname === '/clubes' ? '2px solid var(--red)' : 'none',
              textDecoration:'none', fontWeight:600}}>CLUBES</Link>
            <Link href="/atletas" style={{
              color: pathname === '/atletas' ? 'var(--red)' : 'inherit', 
              borderBottom: pathname === '/atletas' ? '2px solid var(--red)' : 'none',
              textDecoration:'none', fontWeight:600}}>ATLETAS</Link>
            <Link href="/dashboard" style={{
              color: pathname?.startsWith('/dashboard') ? 'var(--red)' : 'inherit', 
              borderBottom: pathname?.startsWith('/dashboard') ? '2px solid var(--red)' : 'none',
              textDecoration:'none', fontWeight:600}}>DASHBOARD IA</Link>
          </div>
        </div>
      </div>

      {/* Contenido Cambiante */}
      <div style={{flex: 1, paddingBottom: chatOpen ? '120px' : '0', transition: 'padding 0.3s'}}>
        {(status.db?.ok === false || status.model?.ok === false) && (
          <div style={{background: '#fee2e2', color: '#991b1b', padding: '12px 20px', textAlign: 'center', fontWeight: 600, borderBottom: '1px solid #f87171', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '8px'}}>
            <span>⚠️</span>
            <span>Aviso: El motor predictivo o la base de datos están inactivos. Algunas funciones del Dashboard pueden no estar disponibles temporalmente.</span>
          </div>
        )}
        {children}
      </div>

      {/* Footer Global */}
      <footer style={{marginTop:'auto'}}>
        <div className="in">
          <div>
            <b>FEDERACIÓN ESPAÑOLA DE TRIATLÓN</b>
            <p>C/ Ferraz 16, 3º Izq<br/>28008 Madrid, España<br/>contacto@triatlon.org</p>
          </div>
          <div>
            <b>LEGAL</b>
            <Link href="/competiciones" style={{textDecoration:'none', color:'inherit'}}>Aviso Legal</Link>
            <Link href="/dashboard/metrics" style={{textDecoration:'none', color:'inherit'}}>Política de Privacidad</Link>
            <Link href="/dashboard/diccionario" style={{textDecoration:'none', color:'inherit'}}>Cookies</Link>
          </div>
          <div>
            <b>ENLACES ÚTILES</b>
            <Link href="/atletas" style={{textDecoration:'none', color:'inherit'}}>Portal del Atleta</Link>
            <Link href="/clubes" style={{textDecoration:'none', color:'inherit'}}>Licencias</Link>
            <Link href="/dashboard" style={{textDecoration:'none', color:'inherit'}}>Transparencia</Link>
          </div>
        </div>
      </footer>

      {/* Chat Widget Global */}
      {!chatOpen && (
        <button className="fab" onClick={() => setChatOpen(true)}>
          💬
        </button>
      )}

      {chatOpen && (
        <div className="panel open" style={{zIndex: 9999}}>
          <div className="ph-head">
            <div className="ava">&#x1F3CA;</div>
            <div className="ti">
              <b>Coach FETRI</b>
              <small>Asistente Predictivo IA</small>
            </div>
            <button className="x" onClick={() => setChatOpen(false)}>&times;</button>
          </div>
          <div className="statusbar">
            <div className="st">
              <div className={`led ${status.ia?.ok === true ? 'ok' : status.ia?.ok === false ? 'bad' : 'wait'}`}></div>
              IA
            </div>
            <div className="st">
              <div className={`led ${status.model?.ok === true ? 'ok' : status.model?.ok === false ? 'bad' : 'wait'}`}></div>
              Modelo
            </div>
            <div className="st">
              <div className={`led ${status.db?.ok === true ? 'ok' : status.db?.ok === false ? 'bad' : 'wait'}`}></div>
              BBDD
            </div>
          </div>
          <div className="msgs">
            {messages.map(m => (
              <div key={m.id} className={`m ${m.role}`}>
                <div className="av">{m.role === 'b' ? '🏊' : '👤'}</div>
                <div className="bx" dangerouslySetInnerHTML={{__html: m.html}}></div>
              </div>
            ))}
            {isTyping && (
              <div className="m b">
                <div className="av">🏊</div>
                <div className="bx">
                  <div className="typing"><i></i><i></i><i></i></div>
                </div>
              </div>
            )}
            <div ref={msgsEndRef} />
          </div>
          {messages.length < 3 && (
            <div className="chips2">
              <div className="chip2" onClick={() => { setInputValue('¿Cómo crees que quedará Mario Mola en Madrid a 25ºC?'); }}>Predicción M. Mola</div>
              <div className="chip2" onClick={() => { setInputValue('¿Qué tal le irá a Antonio Serrat?'); }}>Serrat</div>
              <div className="chip2" onClick={() => { setInputValue('Explícame los factores SHAP de Roberto Sánchez.'); }}>SHAP de Roberto</div>
            </div>
          )}
          <div className="composer">
            <textarea 
              id="inp" 
              placeholder="Pregúntame sobre un atleta..." 
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => { if(e.key==='Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } }}
              disabled={busy}
            />
            <button className="snd" disabled={busy || !inputValue.trim()} onClick={sendMsg}>
              <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
