"""Consulta la metadata de Street View (gratis) para cada punto de panos/puntos.csv -> panos/panos.csv"""
import csv, json, os, time, urllib.request, urllib.parse
KEY = os.environ['GOOGLE_MAPS_KEY']
D = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(f'{D}/puntos.csv')))
out = []
for i, p in enumerate(rows):
    q = urllib.parse.urlencode(dict(location=f"{p['lat']},{p['lng']}", radius=12, source='outdoor', key=KEY))
    try:
        r = json.load(urllib.request.urlopen('https://maps.googleapis.com/maps/api/streetview/metadata?' + q, timeout=20))
    except Exception as e:
        r = {'status': 'ERROR'}
    if i == 0 and r.get('status') not in ('OK', 'ZERO_RESULTS'):
        raise SystemExit(f"Primera respuesta: {r.get('status')} {r.get('error_message','')}")
    loc = r.get('location') or {}
    out.append(dict(p, status=r.get('status'), pano_id=r.get('pano_id', ''), plat=loc.get('lat', ''), plng=loc.get('lng', ''), fecha=r.get('date', '')))
    time.sleep(0.05)
with open(f'{D}/panos.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print(len(out), 'consultas,', len({o['pano_id'] for o in out if o['status'] == 'OK'}), 'panos distintos')
