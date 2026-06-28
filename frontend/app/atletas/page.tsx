'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Atletas() {
  const router = useRouter();
  const [atletas, setAtletas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/athletes_directory')
      .then(async r => {
        const d = await r.json();
        if (!r.ok || d.error) throw new Error(d.error || 'Error del servidor');
        setAtletas(d); 
        setLoading(false); 
      })
      .catch(e => { 
        console.error(e); 
        setError('Servicio no disponible temporalmente. Inténtalo más tarde.');
        setLoading(false); 
      });
  }, []);

  const filtered = atletas.filter(a => 
    (a.nombre || '').toLowerCase().includes(search.toLowerCase()) || 
    (a.club || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="dashboard-page">
      <div className="container" style={{paddingTop: '20px'}}>
        <div className="glass-panel">
          <h2 className="section-title">Directorio de Atletas</h2>
          
          <div style={{marginBottom: '20px'}}>
            <input 
              type="text" 
              placeholder="Buscar por nombre o club..." 
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
                  <th>Club</th>
                  <th>Grupo de Edad</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}><div className="loading-spinner" style={{display: 'inline-block'}}></div><div style={{marginTop: '10px'}}>Cargando atletas...</div></td></tr>
                ) : error ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--red)'}}>⚠️ {error}</td></tr>
                ) : filtered.length === 0 ? (
                  <tr><td colSpan={3} style={{textAlign:'center', padding: '2rem', color: 'var(--text-muted)'}}>No se encontraron resultados</td></tr>
                ) : (
                  filtered.map((ath, idx) => (
                    <tr key={idx} onClick={() => router.push(`/dashboard/athlete/${encodeURIComponent(ath.documento || ath.nombre)}`)} style={{cursor: 'pointer'}}>
                      <td style={{fontWeight:600}}>{ath.nombre}</td>
                      <td style={{color:'var(--text-muted)'}}>{ath.club || 'Independiente'}</td>
                      <td>{ath.ggee || 'Élite'}</td>
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
