'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const [news, setNews] = useState<any[]>([]);

  useEffect(() => {
    fetch('/api/news').then(r => r.json()).then(d => setNews(d)).catch(e => setNews([]));
  }, []);

  return (
    <>
      <div className="hero">
        <div className="in">
          <div className="tag">NUEVA TEMPORADA</div>
          <h1>El Camino a Los Ángeles 2028 Empieza Aquí</h1>
          <p>Sigue de cerca a nuestros triatletas de élite. Descubre estadísticas, resultados en vivo y nuestra nueva IA de análisis de rendimiento predictivo.</p>
          <Link href="/dashboard" className="btn">IR AL DASHBOARD PREDICTIVO →</Link>
        </div>
      </div>

      <div className="band">
        <div className="in">
          <div><div className="n">+14k</div><div className="l">FEDERADOS</div></div>
          <div><div className="n">350</div><div className="l">CLUBES ACTIVOS</div></div>
          <div><div className="n">12</div><div className="l">MEDALLAS INT.</div></div>
          <div><div className="n">8</div><div className="l">SEDES OFICIALES</div></div>
        </div>
      </div>

      <div className="sec wrap">
        <h2>ACTUALIDAD</h2>
        <div className="h3">Últimas Noticias y Resultados</div>
        <div className="grid">
          {news.map((item, idx) => (
            <a key={idx} href={item.link} target="_blank" rel="noopener noreferrer" className="card" style={{display:'block', textDecoration:'none', color:'inherit'}}>
              <div className={`ph c${(idx%6)+1}`}>&#x1F4F0;</div>
              <div className="bd">
                <div className="dt">{item.date || 'ACTUALIDAD'}</div>
                <h4>{item.title}</h4>
              </div>
            </a>
          ))}
        </div>
      </div>

      <div className="sponsors">
        <div className="row">
          <div className="sp">IBERDROLA</div>
          <div className="sp">LOTERÍAS</div>
          <div className="sp">GOfit</div>
          <div className="sp">AUSTRAL</div>
          <div className="sp">HALCÓN VIAJES</div>
        </div>
      </div>
    </>
  );
}
