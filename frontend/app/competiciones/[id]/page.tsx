'use client';

import { useState, useEffect, use } from 'react';
import Link from 'next/link';

export default function CompetitionResults({ params }: { params: Promise<{ id: string }> }) {
  const unwrappedParams = use(params);
  const id = unwrappedParams.id;
  
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`/api/competition/${id}/results`)
      .then(async r => {
        const d = await r.json();
        if (!r.ok || d.error) throw new Error(d.error || 'Error del servidor');
        setResults(d.results || []);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setError('Servicio no disponible temporalmente o la competición no existe.');
        setLoading(false);
      });
  }, [id]);

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div style={{marginBottom: '20px'}}>
          <Link href="/competiciones" style={{color: 'var(--accent)', textDecoration: 'none', fontWeight: 600}}>
            ← Volver al Calendario
          </Link>
        </div>

        <div className="glass-panel">
          <h2 className="section-title">Resultados Oficiales (Históricos)</h2>
          <p style={{color: 'var(--text-muted)', marginBottom: '20px'}}>
            Esta es la clasificación real que se dio en la carrera. No es una predicción, son los datos extraídos de la base de datos de la Federación.
          </p>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Puesto</th>
                  <th>Atleta</th>
                  <th>Club</th>
                  <th>Puntos FETRI</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}><div className="loading-spinner" style={{display: 'inline-block'}}></div><div style={{marginTop: '10px'}}>Cargando resultados...</div></td></tr>
                ) : error ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--red)'}}>⚠️ {error}</td></tr>
                ) : results.length === 0 ? (
                  <tr><td colSpan={4} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}>No hay resultados registrados para esta competición.</td></tr>
                ) : (
                  results.map((r, idx) => (
                    <tr key={idx}>
                      <td style={{fontWeight: 'bold', color: r.puesto <= 3 ? 'var(--gold)' : 'var(--text-main)'}}>
                        #{r.puesto}
                      </td>
                      <td>
                        <Link href={`/dashboard/athlete/${r.documento}`} style={{color: 'var(--text-main)', textDecoration: 'none'}}>
                          {r.atleta}
                        </Link>
                      </td>
                      <td style={{color: 'var(--text-muted)'}}>{r.club}</td>
                      <td>{r.puntos ? r.puntos.toFixed(1) : '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
