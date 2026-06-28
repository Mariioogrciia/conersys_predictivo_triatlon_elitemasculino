'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Competiciones() {
  const router = useRouter();
  const [competiciones, setCompeticiones] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/competitions_directory')
      .then(async r => {
        const d = await r.json();
        if (!r.ok || d.error) throw new Error(d.error || 'Error del servidor');
        setCompeticiones(d); 
        setLoading(false); 
      })
      .catch(e => { 
        console.error(e); 
        setError('Servicio no disponible temporalmente. Inténtalo más tarde.');
        setLoading(false); 
      });
  }, []);

  const filtered = competiciones.filter(c => 
    (c.nombre || '').toLowerCase().includes(search.toLowerCase()) || 
    (c.ciudad || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div className="glass-panel">
          <h2 className="section-title">Calendario de Competiciones</h2>
          
          <div style={{
            background: 'rgba(56, 189, 248, 0.1)', 
            borderLeft: '4px solid var(--accent)', 
            padding: '15px', 
            borderRadius: '4px', 
            marginBottom: '25px',
            fontSize: '0.9rem',
            color: 'var(--text-muted)'
          }}>
            <strong>Nota sobre los datos:</strong> Este calendario ha sido filtrado para mostrar exclusivamente pruebas de <strong>Triatlón Individual de Corta Distancia (Sprint y Olímpico)</strong> de categoría Élite Masculina. El modelo predictivo entrenado en <strong>Azure Machine Learning</strong> utiliza exclusivamente estas distancias y perfiles fisiológicos, por lo que las pruebas de Duatlón, Acuatlón y competiciones por equipos/relevos han sido excluidas para mantener el rigor de las predicciones.
          </div>
          
          <div style={{marginBottom: '20px'}}>
            <input 
              type="text" 
              placeholder="Buscar competición por nombre o ciudad..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{width: '100%', maxWidth: '400px', padding: '10px 15px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.05)', color: '#fff'}}
            />
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Fecha</th>
                  <th>Ubicación</th>
                  <th>Nivel</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}><div className="loading-spinner" style={{display: 'inline-block'}}></div><div style={{marginTop: '10px'}}>Cargando competiciones...</div></td></tr>
                ) : error ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--red)'}}>⚠️ {error}</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}>No se encontraron resultados</td></tr>
                ) : (
                  filtered.map((c, idx) => {
                    const dateObj = c.fecha ? new Date(c.fecha) : null;
                    const dateStr = dateObj ? dateObj.toLocaleDateString('es-ES', { year: 'numeric', month: 'long', day: 'numeric' }) : 'Desconocida';
                    return (
                      <tr 
                        key={idx} 
                        onClick={() => router.push(`/competiciones/${c.id}`)}
                        style={{cursor: 'pointer'}}
                        className="clickable-row"
                      >
                        <td style={{fontWeight:600, color: 'var(--accent)'}}>{c.nombre}</td>
                        <td style={{whiteSpace: 'nowrap'}}>{dateStr}</td>
                        <td>{c.ciudad}{c.provincia && c.provincia !== c.ciudad ? `, ${c.provincia}` : ''}</td>
                        <td style={{whiteSpace: 'nowrap'}}>
                          <span style={{
                            display: 'inline-block',
                            whiteSpace: 'nowrap',
                            background: c.championship_level === 1 ? 'rgba(255, 215, 0, 0.2)' : 'rgba(255, 255, 255, 0.1)',
                            color: c.championship_level === 1 ? 'var(--gold)' : 'var(--text-muted)',
                            padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600
                          }}>
                            Nivel {c.championship_level}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
