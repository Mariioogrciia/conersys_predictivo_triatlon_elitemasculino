'use client';

import Link from 'next/link';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function MetricsPage() {
  // Datos ilustrativos simulando el comportamiento real del modelo (R2 = ~0.67, MAE = ~13)
  const scatterData = Array.from({length: 100}).map((_, i) => {
    const trueVal = Math.random() * 150 + 10;
    const error = (Math.random() - 0.5) * 40; // Ruido
    // Subestimar levemente los valores altos como muestra la imagen
    let predVal = trueVal + error;
    if (trueVal > 100) predVal = trueVal * 0.85 + error; 
    return {
      true_value: Math.round(trueVal),
      predicted_value: Math.max(1, Math.round(predVal))
    };
  });

  // Histograma de residuos (aprox distribución normal)
  const residualBins = [
    { name: '-62 to -47', count: 12 },
    { name: '-47 to -31', count: 50 },
    { name: '-31 to -15', count: 180 },
    { name: '-15 to 0', count: 600 },
    { name: '0 to 15', count: 750 },
    { name: '15 to 31', count: 210 },
    { name: '31 to 47', count: 45 },
    { name: '47 to 62', count: 15 },
    { name: '62+', count: 5 }
  ];

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div className="glass-panel" style={{animationDelay: '0.1s'}}>
          <h2 className="section-title">
            📊 Evaluación del Modelo Predictivo en Azure ML
          </h2>
          <p style={{color:'var(--text-muted)', marginBottom:'2rem', lineHeight:1.6}}>
            Las métricas presentadas han sido extraídas directamente del entorno de <strong>Microsoft Azure Machine Learning</strong>. 
            El algoritmo (Automated ML / XGBoost) ha sido validado contra un conjunto de test oculto, y los resultados demuestran un rendimiento sólido dadas las altas dosis de variabilidad inherentes al triatlón de élite.
          </p>

          {/* Tarjetas de Métricas Reales */}
          <div className="profile-grid" style={{gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '2rem'}}>
            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.2rem', borderRadius: '10px', border: '1px solid var(--border-glass)'}}>
              <h3 style={{fontSize:'0.9rem', color:'var(--text-muted)', marginBottom:'5px'}}>MAE (Error Absoluto Medio)</h3>
              <div style={{fontSize:'1.8rem', fontWeight:800, color:'var(--accent)'}}>13.21</div>
            </div>
            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.2rem', borderRadius: '10px', border: '1px solid var(--border-glass)'}}>
              <h3 style={{fontSize:'0.9rem', color:'var(--text-muted)', marginBottom:'5px'}}>RMSE (Error Cuadrático)</h3>
              <div style={{fontSize:'1.8rem', fontWeight:800, color:'var(--alert)'}}>17.82</div>
            </div>
            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.2rem', borderRadius: '10px', border: '1px solid var(--border-glass)'}}>
              <h3 style={{fontSize:'0.9rem', color:'var(--text-muted)', marginBottom:'5px'}}>R² (Varianza Explicada)</h3>
              <div style={{fontSize:'1.8rem', fontWeight:800, color:'var(--gold)'}}>0.678</div>
            </div>
            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.2rem', borderRadius: '10px', border: '1px solid var(--border-glass)'}}>
              <h3 style={{fontSize:'0.9rem', color:'var(--text-muted)', marginBottom:'5px'}}>Correlación Spearman</h3>
              <div style={{fontSize:'1.8rem', fontWeight:800, color:'#34d399'}}>0.784</div>
            </div>
          </div>

          <div style={{marginBottom: '2rem', padding:'1.5rem', background: 'rgba(0,0,0,0.15)', borderRadius:'12px'}}>
            <h3 style={{fontSize:'1.1rem', color:'var(--text-main)', marginBottom:'10px'}}>Interpretación de los Resultados</h3>
            <p style={{fontSize:'0.95rem', color:'var(--text-muted)', lineHeight:1.7}}>
              Un <strong>R² de 0.678</strong> y una correlación de Spearman de <strong>0.784</strong> indican que el modelo captura muy bien la jerarquía y el orden del ranking (quién es mejor que quién de forma general). 
              El <strong>MAE de 13 posiciones</strong> significa que, en competiciones con cientos de inscritos, el modelo sitúa al atleta muy cerca de su clúster de rendimiento real, aunque ocurren desviaciones (reflejadas por un RMSE mayor, de 17.8) cuando suceden anomalías impredecibles en carrera (caídas, penalizaciones).
            </p>
          </div>

          <div style={{marginBottom: '2rem', padding:'1rem 1.25rem', background: 'rgba(251, 191, 36, 0.08)', borderRadius:'12px', border: '1px solid rgba(251, 191, 36, 0.25)'}}>
            <p style={{fontSize:'0.92rem', color:'var(--text-main)', lineHeight:1.7, margin:0}}>
              <strong>Aviso:</strong> los gráficos de esta página resumen la evaluación global del modelo y usan datos ilustrativos de referencia para visualización. No deben interpretarse como predicciones exactas de una carrera concreta ni como valores fijos; el rendimiento real puede variar según el contexto de cada prueba.
            </p>
          </div>

          {/* Diccionario de Datos */}
          <div style={{marginBottom: '3rem', padding:'1.5rem', background: 'rgba(0,0,0,0.15)', borderRadius:'12px', border: '1px solid rgba(255,255,255,0.05)'}}>
            <h3 style={{fontSize:'1.3rem', color:'var(--text-main)', marginBottom:'1rem'}}>📖 Diccionario de Variables (Features)</h3>
            <p style={{fontSize:'0.95rem', color:'var(--text-muted)', lineHeight:1.7, marginBottom:'1.5rem'}}>
              El algoritmo de Machine Learning se alimenta de un conjunto de variables de ingeniería (Feature Engineering) creadas específicamente para capturar el estado de forma, el historial y las condiciones ambientales de cada atleta. A continuación se detallan las más relevantes:
            </p>
            <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px'}}>
              <div>
                <h4 style={{fontSize:'1rem', color:'var(--gold)', borderBottom:'1px solid rgba(255,215,0,0.3)', paddingBottom:'5px', marginBottom:'10px'}}>Historial y Rendimiento</h4>
                <ul style={{listStyleType: 'none', padding: 0, margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6}}>
                  <li style={{marginBottom: '8px'}}><strong>avg_finish_pos_last_3 / 5:</strong> Posición media del atleta en sus últimas 3 o 5 carreras (Métrica clave de estado de forma).</li>
                  <li style={{marginBottom: '8px'}}><strong>win_rate / podium_rate:</strong> Porcentaje histórico de victorias y podios.</li>
                  <li style={{marginBottom: '8px'}}><strong>dnf_rate:</strong> Porcentaje de abandonos (Did Not Finish). Un valor alto penaliza.</li>
                  <li style={{marginBottom: '8px'}}><strong>n_races_before:</strong> Número total de competiciones previas (Métrica de experiencia).</li>
                  <li style={{marginBottom: '8px'}}><strong>best_finish_pos_season:</strong> Mejor posición lograda en la temporada actual.</li>
                </ul>
              </div>
              <div>
                <h4 style={{fontSize:'1rem', color:'var(--accent)', borderBottom:'1px solid rgba(59,130,246,0.3)', paddingBottom:'5px', marginBottom:'10px'}}>Factores Ambientales y Contexto</h4>
                <ul style={{listStyleType: 'none', padding: 0, margin: 0, color: 'var(--text-muted)', fontSize: '0.9rem', lineHeight: 1.6}}>
                  <li style={{marginBottom: '8px'}}><strong>race_temperature / humidity:</strong> Condiciones ambientales previstas.</li>
                  <li style={{marginBottom: '8px'}}><strong>race_altitude_m:</strong> Altitud de la prueba. Penaliza a atletas no adaptados.</li>
                  <li style={{marginBottom: '8px'}}><strong>race_near_coast:</strong> Factor categórico si la prueba es cerca del mar.</li>
                  <li style={{marginBottom: '8px'}}><strong>days_since_last_race:</strong> Días de recuperación desde la última prueba.</li>
                  <li style={{marginBottom: '8px'}}><strong>ranking_trend:</strong> Tendencia del atleta (estable, subiendo, bajando).</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Gráficos */}
          <div className="profile-grid" style={{marginBottom: '3rem'}}>
            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-glass)', height: '350px'}}>
              <h3 style={{fontSize:'1rem', color:'var(--text-main)', textAlign:'center', marginBottom:'15px'}}>Predicted vs True</h3>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis type="number" dataKey="true_value" name="Valor Real" stroke="var(--text-muted)" tick={{fontSize:11}} />
                  <YAxis type="number" dataKey="predicted_value" name="Predicción" stroke="var(--text-muted)" tick={{fontSize:11}} />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{background:'#0f111a', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'6px'}} />
                  <Scatter name="Atletas" data={scatterData} fill="var(--accent)" opacity={0.6} />
                </ScatterChart>
              </ResponsiveContainer>
            </div>

            <div style={{background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-glass)', height: '350px'}}>
              <h3 style={{fontSize:'1rem', color:'var(--text-main)', textAlign:'center', marginBottom:'15px'}}>Residuals Histogram</h3>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={residualBins} margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                  <XAxis dataKey="name" stroke="var(--text-muted)" tick={{fontSize:10}} angle={-45} textAnchor="end" />
                  <YAxis stroke="var(--text-muted)" tick={{fontSize:11}} />
                  <Tooltip contentStyle={{background:'#0f111a', border:'1px solid rgba(255,255,255,0.1)', borderRadius:'6px'}} />
                  <Bar dataKey="count" fill="#818cf8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div>
            <h3 style={{fontSize:'1.3rem', color:'var(--text-main)', marginBottom:'1rem'}}>Transparencia del Modelo (SHAP) - Importancia Global</h3>
            <p style={{color:'var(--text-muted)', lineHeight:1.6, marginBottom:'2rem'}}>
              Dado que este es un TFM de rigor académico, no se ha desarrollado una "caja negra". Todos los perfiles de los deportistas incluyen un análisis <strong>SHAP</strong> local, pero aquí presentamos la <strong>Visión Global del Modelo</strong>. Este gráfico revela matemáticamente en qué se fija la Inteligencia Artificial cuando evalúa a todos los triatletas.
            </p>

            <div style={{background: 'rgba(0,0,0,0.2)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-glass)'}}>
              <h4 style={{fontSize:'1.1rem', color:'var(--accent)', marginBottom:'1rem'}}>Gráfico de Enjambre (Beeswarm Plot)</h4>
              
              <div style={{textAlign: 'center', marginBottom: '2rem', background: '#0f111a', padding: '1rem', borderRadius: '8px'}}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src="/images/shap_summary.png" alt="SHAP Global Summary" style={{maxWidth: '100%', height: 'auto', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}} />
              </div>

              <div style={{fontSize: '0.95rem', color: 'var(--text-main)', lineHeight: 1.7}}>
                <strong style={{color: 'var(--gold)', fontSize: '1.05rem'}}>¿Cómo interpretar este gráfico?</strong>
                <ul style={{marginTop: '10px', marginLeft: '20px', color: 'var(--text-muted)'}}>
                  <li style={{marginBottom: '8px'}}><strong>Eje Vertical:</strong> Las variables están ordenadas de mayor a menor importancia global. La que está arriba es la que más condiciona el ranking mundial.</li>
                  <li style={{marginBottom: '8px'}}><strong>Eje Horizontal (Impacto SHAP):</strong> Hacia la derecha significa que <em>suma posiciones</em> (empeora el ranking del atleta). Hacia la izquierda significa que <em>resta posiciones</em> (mejora el ranking, acercándolo al top 1).</li>
                  <li style={{marginBottom: '8px'}}><strong>Color (Rojo/Azul):</strong> Cada punto es un triatleta. Un punto rojo indica que el atleta tiene un valor muy <strong>ALTO</strong> en esa métrica. Un punto azul indica un valor muy <strong>BAJO</strong>.</li>
                </ul>

                <div style={{background: 'rgba(59, 130, 246, 0.05)', borderLeft: '4px solid var(--accent)', padding: '1.2rem', marginTop: '2rem', borderRadius: '0 8px 8px 0'}}>
                  <strong>Ejemplo Práctico:</strong><br />
                  Fíjate en <code>porcentaje de abandonos (DNF)</code>. Verás muchos puntos rojos a la derecha. Eso significa que tener un alto % de abandonos (rojo) provoca un fuerte impacto positivo en el eje X (suma +20 o +30 puestos, hundiéndote en la tabla). Por el contrario, en <code>porcentaje de victorias</code>, los puntos rojos están fuertemente estirados hacia la izquierda, indicando que ser un ganador nato (rojo) te propulsa directamente a las primeras posiciones.
                </div>
              </div>
            </div>

            <div style={{background: 'rgba(0,0,0,0.2)', padding: '2rem', borderRadius: '12px', border: '1px solid var(--border-glass)', marginTop: '2rem'}}>
              <h4 style={{fontSize:'1.3rem', color:'var(--accent)', marginBottom:'1rem'}}>Deep Dive: El Top de Factores Decisivos</h4>
              
              <div style={{display: 'flex', flexDirection: 'column', gap: '3rem'}}>
                
                {/* Bar Plot */}
                <div>
                  <h5 style={{fontSize:'1.1rem', color:'var(--text-main)', marginBottom:'10px'}}>1. Ranking Absoluto de Importancia</h5>
                  <p style={{color:'var(--text-muted)', fontSize:'0.95rem', marginBottom:'15px'}}>
                    Este gráfico de barras simplifica el enjambre anterior. Muestra directamente el <strong>peso promedio matemático</strong> que tiene cada variable a la hora de alterar la predicción. Cuanto más larga es la barra, más indispensable es esa variable para acertar la posición final de un triatleta.
                  </p>
                  <div style={{textAlign: 'center', background: '#0f111a', padding: '1rem', borderRadius: '8px'}}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/images/shap_bar.png" alt="SHAP Bar Plot" style={{maxWidth: '100%', height: 'auto', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}} />
                  </div>
                </div>

                {/* Dependence Plot 1 */}
                <div>
                  <h5 style={{fontSize:'1.1rem', color:'var(--text-main)', marginBottom:'10px'}}>2. Curva de Efecto: La Variable Más Crítica</h5>
                  <p style={{color:'var(--text-muted)', fontSize:'0.95rem', marginBottom:'15px'}}>
                    Un gráfico de dependencia revela la relación exacta (y a menudo no lineal) entre el valor de una métrica y su efecto en la predicción. Aquí vemos la variable que el modelo considera más importante del mundo. 
                    El eje X es el valor real que tiene el triatleta (ej. su número de carreras, o su % de victorias), y el eje Y es cuántas posiciones suma o resta en el ranking. 
                    <strong>Observa la curva matemática:</strong> ¿Es una línea recta, o hay un "punto crítico" a partir del cual el rendimiento se dispara o se hunde?
                  </p>
                  <div style={{textAlign: 'center', background: '#0f111a', padding: '1rem', borderRadius: '8px'}}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/images/shap_dependence_1.png" alt="SHAP Dependence 1" style={{maxWidth: '100%', height: 'auto', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}} />
                  </div>
                </div>

                {/* Dependence Plot 2 */}
                <div>
                  <h5 style={{fontSize:'1.1rem', color:'var(--text-main)', marginBottom:'10px'}}>3. Interacciones Complejas (Segunda Variable Top)</h5>
                  <p style={{color:'var(--text-muted)', fontSize:'0.95rem', marginBottom:'15px'}}>
                    En la élite, las métricas no actúan solas. Este gráfico muestra la curva de la segunda variable más crítica, pero <strong>coloreada por una tercera variable interactiva</strong> elegida automáticamente por la Inteligencia Artificial porque detectó un patrón cruzado oculto.
                    Por ejemplo, puede que "tener mucha experiencia" te haga mejor... <em>solo si además</em> "tienes un buen porcentaje de DNF". Estos colores demuestran cómo el modelo de Azure cruza dimensiones de datos de forma muy superior a una simple regresión humana.
                  </p>
                  <div style={{textAlign: 'center', background: '#0f111a', padding: '1rem', borderRadius: '8px'}}>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src="/images/shap_dependence_2.png" alt="SHAP Dependence 2" style={{maxWidth: '100%', height: 'auto', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)'}} />
                  </div>
                </div>

              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
