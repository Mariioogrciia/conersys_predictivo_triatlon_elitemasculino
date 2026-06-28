import urllib.request, json
data = json.loads(urllib.request.urlopen('http://127.0.0.1:5050/api/ranking?limit=5', timeout=60).read().decode())
for r in data['ranking']:
    name = r['nombre'][:30].ljust(30)
    raw = r.get('prediccion_raw', '?')
    pos = r['posicion_predicha']
    anom = r['anomalia']
    motivo = r.get('anomalia_motivo', '')
    print(f"{name} raw={raw:<8} pos=#{pos}  anomalia={anom}  {motivo}")
