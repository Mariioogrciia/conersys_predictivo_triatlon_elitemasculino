'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Clubes() {
  const [clubes, setClubes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/clubs_directory')
      .then(async r => {
        const d = await r.json();
        if (!r.ok || d.error) throw new Error(d.error || 'Error del servidor');
        setClubes(d); 
        setLoading(false); 
      })
      .catch(e => { 
        console.error(e); 
        setError('Servicio no disponible temporalmente. Inténtalo más tarde.');
        setLoading(false); 
      });
  }, []);

  const filtered = clubes.filter(c => 
    (c.club || '').toLowerCase().includes(search.toLowerCase()) || 
    (c.provincia || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div className="glass-panel">
          <h2 className="section-title">Directorio de Clubes</h2>
          
          <div style={{marginBottom: '20px'}}>
            <input 
              type="text" 
              placeholder="Buscar por nombre o provincia..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              style={{width: '100%', maxWidth: '400px', padding: '10px 15px', borderRadius: '8px', border: '1px solid var(--border-glass)', background: 'rgba(255,255,255,0.05)', color: '#fff'}}
            />
          </div>

          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Club</th>
                  <th>Sede</th>
                  <th>Provincia</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}><div className="loading-spinner" style={{display: 'inline-block'}}></div><div style={{marginTop: '10px'}}>Cargando clubes...</div></td></tr>
                ) : error ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--red)'}}>⚠️ {error}</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}>No se encontraron resultados</td></tr>
                ) : (
                  filtered.map((c, idx) => (
                    <tr key={idx}>
                      <td style={{fontWeight:600}}>{c.club}</td>
                      <td>{c.ciudad_sede || 'Desconocida'}</td>
                      <td>{c.provincia || 'Desconocida'}</td>
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
