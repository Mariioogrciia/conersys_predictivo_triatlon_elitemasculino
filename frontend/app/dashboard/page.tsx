'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Dashboard() {
  const router = useRouter();
  const [ranking, setRanking] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [offset, setOffset] = useState(0);
  const [simulated, setSimulated] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [simModalOpen, setSimModalOpen] = useState(false);
  const [error, setError] = useState('');

  // Sim Form
  const [races, setRaces] = useState<any[]>([]);
  const [selRace, setSelRace] = useState('');
  const [simCity, setSimCity] = useState('');
  const [simTemp, setSimTemp] = useState('');
  const [simAlt, setSimAlt] = useState('');
  const [simHum, setSimHum] = useState('');
  const [simLat, setSimLat] = useState('');
  const [simLng, setSimLng] = useState('');

  useEffect(() => {
    loadRaces();
  }, [demoMode]);

  const loadRanking = async (loadMore = false) => {
    const limit = 10;
    const currentOffset = loadMore ? offset : 0;
    if(!loadMore) setLoading(true);

    const endpoint = demoMode 
      ? `/api/demo/ranking?limit=${limit}&offset=${currentOffset}` 
      : `/api/ranking?limit=${limit}&offset=${currentOffset}`;
    
    try {
      const res = await fetch(endpoint, { cache: 'no-store' });
      const data = await res.json();
      
      if (data.error || !data.ranking) {
        console.error("Error desde el API:", data.error);
        setError('Servicio no disponible temporalmente. Activa el Modo Demo para ver un ejemplo.');
        setLoading(false);
        return;
      }
      
      setError('');
      
      setRanking(prev => loadMore ? [...prev, ...data.ranking] : data.ranking);
      setOffset(currentOffset + data.ranking.length);
      setSimulated(data.simulated || false);
    } catch(e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadRaces = async () => {
    try {
      const res = await fetch('/api/races');
      const data = await res.json();
      if(data.races) setRaces(data.races);
    } catch(e) {}
  };

  const onRaceSelect = (e: any) => {
    const val = e.target.value;
    setSelRace(val);
    const r = races.find(x => x.nombre === val);
    if(r) {
      setSimCity(r.ciudad);
      setSimTemp(r.temperatura_max);
      setSimAlt(r.altitud);
      setSimHum(r.humedad_media);
      setSimLat(r.lat || '');
      setSimLng(r.lng || '');
    }
  };

  const runSimulation = async () => {
    setSimModalOpen(false);
    setLoading(true);
    setRanking([]); // Limpiar para asegurar que se muestre el spinner de carga
    try {
      const reqData = {
        race_city: simCity,
        race_temperature: simTemp,
        race_altitude_m: simAlt,
        race_humidity: simHum,
        race_lat: simLat,
        race_lng: simLng,
        limit: 15
      };
      const res = await fetch('/api/simulate_race', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(reqData)
      });
      const data = await res.json();
      setRanking(data.ranking);
      setSimulated(true);
    } catch(e) {
    } finally {
      setLoading(false);
    }
  };

  const maxRaw = Math.max(...ranking.map(a => a.prediccion_raw || 60), 1);

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div style={{display:'flex', justifyContent:'flex-end', gap:'10px', marginBottom:'20px'}}>
          <button onClick={() => setSimModalOpen(true)} style={{background:'var(--accent)',color:'#fff',border:'none',padding:'6px 12px',borderRadius:'6px',cursor:'pointer',fontSize:'0.85rem',fontWeight:600}}>Simular Carrera Futura</button>
          {simulated && (
            <button style={{background:'rgba(255,255,255,0.1)',color:'#fff',border:'1px solid var(--border-glass)',padding:'6px 12px',borderRadius:'6px',cursor:'pointer',fontSize:'0.85rem',fontWeight:600}} onClick={() => { setSimulated(false); setRanking([]); }}>← Limpiar Resultados</button>
          )}
          <input type="checkbox" id="demo-mode" checked={demoMode} onChange={e => setDemoMode(e.target.checked)} />
          <label htmlFor="demo-mode" style={{color:'#fff', fontSize:'0.85rem'}}>Modo Demo Offline</label>
        </div>
        <div className="glass-panel" style={{animationDelay: '0.1s'}}>
          <h2 className="section-title">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{color:'var(--accent)', marginRight:'10px'}}><path d="M12 20V10"></path><path d="M18 20V4"></path><path d="M6 20v-4"></path></svg>
            {simulated ? (
              <span>Simulación: <span style={{color: 'var(--gold)'}}>{selRace || 'Carrera Personalizada'}</span></span>
            ) : (
              'Simulador Predictivo FETRI'
            )}
          </h2>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Pos</th>
                  <th>Atleta</th>
                  <th>Club</th>
                  <th>Pred. Azure ML</th>
                  <th>Rendimiento</th>
                  <th>Info</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} style={{textAlign:'center', padding: '4rem 2rem'}}>
                      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px'}}>
                        {/* Premium Glowing Brain / AI animation */}
                        <div style={{position: 'relative', width: '60px', height: '60px'}}>
                          <div style={{position: 'absolute', inset: 0, border: '3px solid transparent', borderTopColor: 'var(--accent)', borderRightColor: 'var(--gold)', borderRadius: '50%', animation: 'spin 1.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite'}}></div>
                          <div style={{position: 'absolute', inset: '8px', border: '3px solid transparent', borderBottomColor: 'var(--gold)', borderLeftColor: 'var(--accent)', borderRadius: '50%', animation: 'spin-reverse 2s linear infinite'}}></div>
                          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', color: 'var(--gold)'}}>
                            <path d="M12 2a10 10 0 1 0 10 10H12V2z"></path>
                            <path d="M12 12 2.1 14.9"></path>
                            <path d="M12 12 21.9 9.1"></path>
                          </svg>
                        </div>
                        <div style={{animation: 'pulse 1.5s ease-in-out infinite'}}>
                          <div style={{color: 'var(--accent)', fontSize: '1.2rem', fontWeight: 600, letterSpacing: '1px'}}>Azure Machine Learning</div>
                          <div style={{color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '5px'}}>Computando predicciones para el ecosistema...</div>
                        </div>
                        
                        <style dangerouslySetInnerHTML={{__html: `
                          @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                          @keyframes spin-reverse { 0% { transform: rotate(360deg); } 100% { transform: rotate(0deg); } }
                          @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
                        `}} />
                      </div>
                    </td>
                  </tr>
                ) : error ? (
                  <tr><td colSpan={6} style={{textAlign:'center', padding: '2rem', color:'var(--red)'}}>⚠️ {error}</td></tr>
                ) : ranking.length === 0 ? (
                  <tr><td colSpan={6} style={{textAlign:'center', padding: '4rem 2rem', color:'var(--text-muted)'}}>
                    <div style={{fontSize: '1.2rem', marginBottom: '10px'}}>🎯 Simulador en reposo</div>
                    Haz clic en "Simular Carrera Futura" arriba a la derecha para configurar las condiciones y generar una predicción con IA.
                  </td></tr>
                ) : (
                  ranking.map((ath, idx) => {
                    const rawVal = ath.prediccion_raw || 0;
                    const barWidth = Math.max(5, 100 - ((rawVal || 50) / maxRaw) * 80);
                      const badge = (() => {
                        if (rawVal <= 30.5) return { label: 'Excelente', color: '#10b981', bg: 'rgba(16, 185, 129, 0.14)' };
                        if (rawVal <= 33) return { label: 'Muy alto', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.14)' };
                        if (rawVal <= 36) return { label: 'Competitivo', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.16)' };
                        return { label: 'Riesgo', color: '#ef4444', bg: 'rgba(239, 68, 68, 0.16)' };
                      })();
                    const color = simulated ? 'var(--gold)' : 'var(--accent)';
                    return (
                      <tr key={idx} onClick={() => router.push(`/dashboard/athlete/${encodeURIComponent(ath.documento || ath.nombre)}`)} style={{cursor: 'pointer'}}>
                        <td className="rank-pos">#{Math.round(ath.posicion_predicha)}</td>
                        <td style={{fontWeight:600}}>{ath.nombre}</td>
                        <td style={{color:'var(--text-muted)'}}>{ath.club || 'Independiente'}</td>
                        <td>
                          <div style={{display:'flex', alignItems:'center', gap:'8px'}}>
                            <span style={{fontWeight:700, color, fontSize:'0.95rem'}}>{rawVal}</span>
                            <span style={{fontSize:'0.72rem', fontWeight:800, padding:'3px 8px', borderRadius:'999px', background: badge.bg, color: badge.color, textTransform:'uppercase', letterSpacing:'0.04em', border: `1px solid ${badge.color}55`, boxShadow: '0 0 0 1px rgba(0,0,0,0.08) inset'}}>{badge.label}</span>
                          </div>
                        </td>
                        <td>
                          <div style={{width:'100%', height:'6px', background:'rgba(255,255,255,0.1)', borderRadius:'3px'}}>
                            <div style={{width:`${barWidth}%`, height:'100%', background:color, borderRadius:'3px', transition:'width 0.8s ease-out'}}></div>
                          </div>
                        </td>
                        <td>
                          {ath.anomalia && <span className="anomaly-icon" title={ath.anomalia_motivo || 'Rendimiento atípico'} style={{marginRight: '8px'}}>⚠</span>}
                          {ath.explicacion && <span title={ath.explicacion} style={{cursor: 'help', fontSize: '1.1rem'}}>ℹ️</span>}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
          {!simulated && !loading && ranking.length >= 10 && (
            <button className="btn-ver-mas" onClick={() => loadRanking(true)}>Cargar resto del ranking</button>
          )}
        </div>
      </div>

      <div className="container" style={{paddingTop:0}}>
        <div className="glass-panel" style={{animationDelay: '0.3s'}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'1rem'}}>
            <h3 style={{fontSize:'1.1rem', fontWeight:600}}>Acerca del Modelo TFM</h3>
            <Link href="/dashboard/metrics" style={{background:'var(--accent)',color:'#fff',textDecoration:'none',padding:'6px 12px',borderRadius:'6px',fontSize:'0.85rem',fontWeight:600}}>
              Ver Evaluación y Métricas 📊
            </Link>
          </div>
          <details className="explainer-content-wrap">
            <summary className="explainer-toggle" style={{listStyle:'none'}}>
              🧠 ¿Cómo funciona nuestro pipeline predictivo? <span className="arrow">▼</span>
            </summary>
            <div className="explainer-content" style={{display:'block'}}>
              <p style={{color:'var(--text-muted)', fontSize:'0.95rem', lineHeight:1.7, marginBottom:'1.5rem'}}>
                Nuestro sistema analiza el rendimiento de cada triatleta y predice su posición en futuras carreras.
                No es magia: se basa en <strong style={{color:'var(--text-main)'}}>datos reales</strong> de competiciones pasadas de la FETRI
                y utiliza un modelo de inteligencia artificial desplegado en <strong style={{color:'var(--accent)'}}>Microsoft Azure</strong>.
              </p>

              <h3 style={{fontSize:'1.1rem', fontWeight:700, marginBottom:'1rem'}}>El proceso paso a paso</h3>
              <div className="pipeline">
                <div className="pipe-step"><div className="step-num">1</div><div className="step-icon">🗄️</div><h4>Recopilación</h4><p>Resultados oficiales.</p></div>
                <div className="pipe-step"><div className="step-num">2</div><div className="step-icon">📊</div><h4>Perfil</h4><p>Historial y evolución.</p></div>
                <div className="pipe-step"><div className="step-num">3</div><div className="step-icon">🤖</div><h4>IA Azure</h4><p>Estimación de posición.</p></div>
                <div className="pipe-step"><div className="step-num">4</div><div className="step-icon">🔍</div><h4>SHAP</h4><p>Explicación visual.</p></div>
              </div>
            </div>
          </details>
        </div>
      </div>

      {simModalOpen && (
        <div className="modal-overlay open" id="sim-modal">
          <div className="modal-content">
            <h2 className="section-title">Simular Carrera</h2>
            
            <div className="form-group">
              <label>Selecciona una Carrera</label>
              <select value={selRace} onChange={onRaceSelect} style={{width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.05)', color: '#fff', marginBottom:'10px'}}>
                <option value="" style={{color: '#fff', background: '#16192b'}}>-- Elige carrera real futura --</option>
                {races.map((r, i) => <option key={i} value={r.nombre} style={{color: '#fff', background: '#16192b'}}>{r.nombre}</option>)}
              </select>
            </div>

            <div className="form-group"><label>Ciudad</label><input type="text" readOnly value={simCity} /></div>
            <div className="form-group"><label>Temperatura (°C)</label><input type="number" readOnly value={simTemp} /></div>
            <div className="form-group"><label>Altitud (m)</label><input type="number" readOnly value={simAlt} /></div>
            <div className="form-group"><label>Humedad (%)</label><input type="number" readOnly value={simHum} /></div>
            
            <button className="btn-primary" onClick={runSimulation}>Predecir Ranking</button>
            <button style={{background:'transparent', color:'var(--text-muted)', border:'none', width:'100%', padding:'10px', marginTop:'5px', cursor:'pointer'}} onClick={() => setSimModalOpen(false)}>Cancelar</button>
          </div>
        </div>
      )}
    </div>
  );
}
