'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function AthleteProfile({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { id } = use(params);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`/api/athlete/${id}`);
        const result = await res.json();
        setData(result);
      } catch(e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return (
      <div className="dashboard-page" style={{display:'flex', justifyContent:'center', alignItems:'center', height:'100vh'}}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  if (!data || data.error) {
    return (
      <div className="dashboard-page" style={{padding:'2rem', color:'var(--alert)'}}>
        <h2>Error: {data?.error || 'Atleta no encontrado'}</h2>
        <button onClick={() => router.back()} className="btn-back">Volver</button>
      </div>
    );
  }

  const { datos_basicos, tendencia_forma, prediccion_actual, historial = [] } = data;
  const historialReciente = Array.isArray(historial) ? historial.slice(0, 8) : [];

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div className="glass-panel">
          <button className="btn-back" onClick={() => router.back()}>&#x2190; Volver al Ranking</button>
          
          <div className="profile-grid">
            <div>
              <h2 className="section-title" style={{fontSize: '2rem'}}>{datos_basicos.nombre}</h2>
              <p style={{color:'var(--text-muted)', marginBottom:'20px'}}>{datos_basicos.club || 'Independiente'}</p>
              
              <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-glass)'}}>
                <div style={{fontSize: '0.9rem', color:'var(--text-muted)'}}>
                  Posición (Prueba Estándar) 
                  <span title="Predicción base calculada asumiendo condiciones estándar (Madrid, 25ºC) para evaluar el estado de forma puro del atleta." style={{cursor: 'help', marginLeft: '5px', color: 'var(--gold)'}}>ℹ️</span>
                </div>
                <div style={{fontSize: '3rem', fontWeight: 800, color:'var(--accent)'}}>
                  #{Math.round(prediccion_actual.prediction || 0)}
                </div>
                <div style={{marginTop: '10px', fontSize: '0.9rem'}}>
                  Tendencia: <span style={{color: tendencia_forma === 'mejorando' ? 'var(--ok)' : tendencia_forma === 'empeorando' ? 'var(--alert)' : 'var(--text-main)'}}>{tendencia_forma}</span>
                </div>
              </div>

              {/* Botón hacia Diccionario */}
              <div style={{marginTop: '20px'}}>
                <Link href="/dashboard/diccionario" style={{
                  display: 'inline-block', padding: '10px 16px', background: 'var(--bg-glass)', 
                  border: '1px solid var(--border-glass)', borderRadius: '8px', fontSize: '0.9rem',
                  textDecoration: 'none', color: 'var(--text-main)', transition: 'border 0.2s'
                }} className="btn-ver-mas">
                  &#x1F4D6; Consultar Diccionario de Variables
                </Link>
              </div>

              {/* Conclusión del Modelo */}
              {prediccion_actual.explanation_text && (
                <div style={{marginTop: '30px'}}>
                  <h3 style={{fontSize: '1.2rem', marginBottom: '15px', color: 'var(--accent)'}}>Análisis Exhaustivo del Modelo</h3>
                  <div style={{
                    background: 'rgba(59, 130, 246, 0.05)', borderLeft: '4px solid var(--accent)',
                    padding: '1.5rem', borderRadius: '0 8px 8px 0', fontSize: '0.95rem', lineHeight: 1.6,
                    color: 'var(--text-main)', whiteSpace: 'pre-wrap'
                  }}>
                    {/* Sustituyendo markdown basico */}
                    {prediccion_actual.explanation_text.split('\n').map((line: string, idx: number) => {
                      if (line.trim() === '') return <br key={idx} />;
                      const isBold = line.includes('**');
                      if (isBold) {
                        const parts = line.split('**');
                        return (
                          <div key={idx} style={{marginBottom: '8px'}}>
                            {parts.map((part, i) => i % 2 === 1 ? <strong key={i} style={{color: 'var(--gold)'}}>{part}</strong> : part)}
                          </div>
                        );
                      }
                      return <div key={idx} style={{marginBottom: '8px'}}>{line}</div>;
                    })}
                  </div>
                </div>
              )}

            </div>
            
            <div>
              <h2 className="section-title">Factores SHAP (Impacto de Variables)</h2>
              
              {prediccion_actual.base_value !== undefined && (
                <div style={{
                  background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-glass)',
                  padding: '12px 16px', borderRadius: '8px', marginBottom: '20px', fontSize: '0.9rem', color: 'var(--text-muted)'
                }}>
                  <span style={{color: 'var(--text-main)', fontWeight: 600}}>Predicción Base: </span>
                  El modelo parte de una predicción media estimada del puesto <strong style={{color: 'var(--accent)'}}>{prediccion_actual.base_value.toFixed(1)}</strong>. 
                  Los siguientes factores suman o restan posiciones hasta llegar a la predicción final de <strong style={{color: 'var(--accent)'}}>{prediccion_actual.prediction.toFixed(1)}</strong>.
                </div>
              )}

              <div>
                {prediccion_actual.top_factors && prediccion_actual.top_factors.length > 0 ? (
                  prediccion_actual.top_factors.map((f: any, i: number) => {
                    const isPos = f.shap_impact > 0;
                    const cColor = isPos ? 'var(--alert)' : 'var(--ok)'; // Positivo = más puestos = malo (rojo). Negativo = menos puestos = bueno (verde).
                    
                    // Normalizamos el ancho máximo de la barra (máximo impacto visible)
                    const maxImpact = Math.max(...prediccion_actual.top_factors.map((tf: any) => Math.abs(tf.shap_impact)), 10);
                    const cWidth = (Math.abs(f.shap_impact) / maxImpact) * 100;

                    // Diccionario de traducciones
                    const translations: Record<string, string> = {
                      "athlete_ranking_triatlon": "Ranking Nacional FETRI",
                      "form_score": "Estado de Forma (Últimas 3)",
                      "avg_ranking_opponents": "Nivel Promedio de Rivales",
                      "pct_opponents_ranked_higher": "% de Rivales con Mejor Ranking",
                      "n_participants_race": "Número de Participantes",
                      "avg_finish_pos_last_3": "Posición Media (Últimas 3)",
                      "win_rate": "Porcentaje de Victorias",
                      "podium_rate": "Porcentaje de Podios"
                    };
                    const humanLabel = translations[f.feature] || f.label || f.feature;
                    
                    return (
                      <div key={i} className="shap-row" style={{marginBottom:'16px'}}>
                        <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.85rem', marginBottom:'6px'}}>
                          <span style={{color:'var(--text-main)', fontWeight:600}}>{humanLabel}</span>
                          <span style={{color:cColor, fontWeight:600, fontSize:'0.9rem'}}>
                            {isPos ? '+' : ''}{f.shap_impact.toFixed(2)} puestos
                          </span>
                        </div>
                        <div style={{fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', justifyContent: 'space-between'}}>
                          <span>
                            Valor Real: <strong style={{color: '#fff', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px'}}>
                              {typeof f.value === 'number' ? f.value.toFixed(2) : f.value}
                            </strong>
                          </span>
                          <span>
                            {isPos ? 'Empeora predicción' : 'Mejora predicción'}
                          </span>
                        </div>
                        
                        {/* Eje Central Divergente */}
                        <div style={{
                          width:'100%', height:'12px', background:'rgba(255,255,255,0.05)', 
                          borderRadius:'6px', display:'flex', position: 'relative', overflow: 'hidden'
                        }}>
                          {/* Eje 0 */}
                          <div style={{position: 'absolute', left: '50%', top: 0, bottom: 0, width: '2px', background: 'var(--border-glass)', zIndex: 2}}></div>
                          
                          {/* Lado Izquierdo (Verde - Resta puestos) */}
                          <div style={{width: '50%', height: '100%', display: 'flex', justifyContent: 'flex-end', paddingRight: '2px'}}>
                            {!isPos && (
                              <div style={{width: `${cWidth}%`, height: '100%', background: 'linear-gradient(to left, var(--ok), #10b981)', borderRadius: '4px 0 0 4px'}}></div>
                            )}
                          </div>

                          {/* Lado Derecho (Rojo - Suma puestos) */}
                          <div style={{width: '50%', height: '100%', display: 'flex', justifyContent: 'flex-start', paddingLeft: '2px'}}>
                            {isPos && (
                              <div style={{width: `${cWidth}%`, height: '100%', background: 'linear-gradient(to right, var(--alert), #ef4444)', borderRadius: '0 4px 4px 0'}}></div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p style={{color:'var(--text-muted)'}}>No hay factores disponibles.</p>
                )}
              </div>

              <div style={{marginTop: '28px', background: 'rgba(0,0,0,0.18)', border: '1px solid var(--border-glass)', borderRadius: '12px', padding: '1.25rem'}}>
                <h3 style={{fontSize: '1.15rem', marginBottom: '12px', color: 'var(--accent)'}}>Historial reciente</h3>
                {historialReciente.length > 0 ? (
                  <div style={{overflowX: 'auto'}}>
                    <table style={{width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem'}}>
                      <thead>
                        <tr style={{textAlign: 'left', color: 'var(--text-muted)', borderBottom: '1px solid var(--border-glass)'}}>
                          <th style={{padding: '10px 8px'}}>Fecha</th>
                          <th style={{padding: '10px 8px'}}>Prueba</th>
                          <th style={{padding: '10px 8px'}}>Ciudad</th>
                          <th style={{padding: '10px 8px'}}>Puesto</th>
                          <th style={{padding: '10px 8px'}}>Puntos</th>
                        </tr>
                      </thead>
                      <tbody>
                        {historialReciente.map((item: any, idx: number) => (
                          <tr key={idx} style={{borderBottom: '1px solid rgba(255,255,255,0.06)'}}>
                            <td style={{padding: '10px 8px', color: 'var(--text-main)'}}>{String(item.fecha || '').slice(0, 10) || '—'}</td>
                            <td style={{padding: '10px 8px', color: 'var(--text-main)'}}>{item.nombre || '—'}</td>
                            <td style={{padding: '10px 8px', color: 'var(--text-main)'}}>{item.ciudad || '—'}</td>
                            <td style={{padding: '10px 8px', color: item.puesto <= 3 ? 'var(--gold)' : 'var(--text-main)', fontWeight: 700}}>{item.puesto ?? '—'}</td>
                            <td style={{padding: '10px 8px', color: 'var(--text-main)'}}>{item.puntos ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p style={{color: 'var(--text-muted)', margin: 0}}>No hay historial disponible para este atleta.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
