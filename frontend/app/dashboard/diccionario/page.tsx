'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function DictionaryPage() {
  const router = useRouter();

  const groups = [
    {
      title: '1. Perfil e Historial General del Atleta',
      features: [
        { name: 'athlete_age_at_race', label: 'Edad del atleta', desc: 'Edad en el momento de competir. El modelo la usa para evaluar si está en pico de rendimiento (suele ser entre los 25 y 30 años en élite) o en fase de declive físico.' },
        { name: 'n_elite_races_before', label: 'Carreras élite previas', desc: 'Número total de competiciones de máximo nivel completadas. Es un indicador puro de "experiencia". A mayor experiencia, el modelo suele predecir menos variabilidad de resultados.' },
        { name: 'best_finish_pos_ever', label: 'Mejor posición histórica', desc: 'El pico histórico del atleta. El modelo lo considera el techo competitivo máximo que ha demostrado alcanzar a lo largo de toda su carrera.' },
        { name: 'win_rate', label: 'Porcentaje de victorias', desc: 'Mide cuántas carreras gana en proporción a las que disputa. Extremadamente importante para identificar a los campeones frente a los que solo puntúan.' },
        { name: 'dnf_rate', label: 'Porcentaje de abandonos (DNF)', desc: 'Indica resiliencia. Un alto DNF (Did Not Finish) penaliza fuertemente la predicción ya que refleja problemas físicos recurrentes o debilidad mental en carreras duras.' }
      ]
    },
    {
      title: '2. Estado de Forma Reciente (Momentum)',
      features: [
        { name: 'avg_finish_pos_last_3', label: 'Posición media (últimas 3)', desc: 'El promedio de resultados en sus últimas 3 carreras. Es el indicador más reactivo del estado de forma actual del triatleta a corto plazo.' },
        { name: 'avg_swim_rank_last_5', label: 'Ranking medio de natación (últimas 5)', desc: 'Indica cómo está saliendo del agua últimamente. Salir en el primer grupo es vital en corta distancia para no perder el pelotón de ciclismo delantero.' },
        { name: 'ranking_momentum', label: 'Momentum en el ranking', desc: 'Diferencia de puntos respecto a sus semanas anteriores. Si es positivo, el atleta viene en clara tendencia ascendente y el modelo confía más en él.' },
        { name: 'current_podium_streak', label: 'Racha actual de podios', desc: 'Suma de cuántas veces seguidas ha hecho podio. Un valor de 2 o más activa un "bonus" de confianza en la predicción.' },
        { name: 'days_since_last_race', label: 'Días desde la última carrera', desc: 'Mide la frescura frente al óxido. Un valor bajo (ej. 7 días) puede indicar fatiga acumulada, y un valor muy alto (>150) falta de ritmo de competición.' }
      ]
    },
    {
      title: '3. Adaptabilidad al Clima y Geografía',
      features: [
        { name: 'performance_heat_bias', label: 'Sesgo de rendimiento con calor', desc: 'Un valor negativo es bueno (resta posiciones en el ranking). Indica que el atleta rinde *mejor* de su media habitual cuando compite a más de 28°C.' },
        { name: 'performance_altitude_bias', label: 'Sesgo de rendimiento en altitud', desc: 'Mide si el atleta penaliza o mejora cuando compite a más de 500m sobre el nivel del mar. Crucial para carreras de montaña o ubicaciones altas.' },
        { name: 'performance_coast_bias', label: 'Sesgo de rendimiento en costa', desc: 'Capacidad de adaptación al nado en mar abierto, olas y salinidad, además de viento y humedad de zonas costeras.' }
      ]
    },
    {
      title: '4. Contexto Específico de la Carrera',
      features: [
        { name: 'avg_ranking_opponents', label: 'Ranking medio de oponentes', desc: 'Mide el "Nivel de la Startlist". Si el valor es bajo, significa que los rivales son top mundial, por lo que será más difícil predecir una buena posición.' },
        { name: 'n_participants_race', label: 'Número de participantes', desc: 'La densidad del pelotón. Carreras con >70 atletas tienen una dinámica de ciclismo mucho más agresiva y con más peligro de cortes o caídas.' },
        { name: 'n_previous_wins_at_city', label: 'Victorias previas en la ciudad', desc: 'Factores de "carrera fetiche". A muchos atletas se les da especialmente bien un circuito y la historia tiende a repetirse.' }
      ]
    }
  ];

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px', paddingBottom: '50px'}}>
        <div className="glass-panel" style={{maxWidth: '900px', margin: '0 auto'}}>
          <button className="btn-back" onClick={() => router.back()}>&#x2190; Volver</button>
          
          <h1 style={{fontSize: '2rem', marginBottom: '10px', color: 'var(--text-main)'}}>Diccionario de Variables del Modelo</h1>
          <p style={{color: 'var(--text-muted)', marginBottom: '40px', fontSize: '1.05rem', lineHeight: 1.6}}>
            Esta guía contiene el análisis exhaustivo de qué significa cada variable en la telemetría SHAP. 
            El algoritmo de Machine Learning de Azure utiliza estas variables para "aprender" de la historia, las condiciones ambientales y el momento de forma, combinando factores a los que ningún humano podría prestar atención simultáneamente.
          </p>
          
          <div style={{display: 'flex', flexDirection: 'column', gap: '30px'}}>
            {groups.map((g, i) => (
              <div key={i} style={{background: 'rgba(0,0,0,0.2)', borderRadius: '12px', border: '1px solid var(--border-glass)', padding: '2rem'}}>
                <h2 style={{color: 'var(--accent)', fontSize: '1.3rem', marginBottom: '20px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '10px'}}>
                  {g.title}
                </h2>
                
                <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
                  {g.features.map((f, j) => (
                    <div key={j} style={{display: 'grid', gridTemplateColumns: '1fr', gap: '8px'}}>
                      <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                        <strong style={{color: '#fff', fontSize: '1.05rem'}}>{f.label}</strong>
                        <code style={{background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: '4px', fontSize: '0.8rem', color: 'var(--gold)'}}>
                          {f.name}
                        </code>
                      </div>
                      <p style={{color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.5}}>
                        {f.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          
        </div>
      </div>
    </div>
  );
}
