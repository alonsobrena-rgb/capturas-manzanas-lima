"""Baja fotos de Street View Static API (pano + heading + pitch) del plan. Mide tiempo. Salida: panos/fotos/out/"""
import json,os,time,urllib.request,urllib.parse
K=os.environ['GOOGLE_MAPS_KEY'];P=json.load(open('panos/fotos/plan.json'));os.makedirs('panos/fotos/out',exist_ok=True)
t0=time.time();ok=0;log=[]
for e in P:
    q=dict(size='640x640',pano=e['pano'],heading=e['heading'],pitch=e['pitch'],fov=80,return_error_code='true',key=K)
    u='https://maps.googleapis.com/maps/api/streetview?'+urllib.parse.urlencode(q)
    n=f"panos/fotos/out/{e['lado']}_{e['k']:02d}.jpg"
    try:
        d=urllib.request.urlopen(u,timeout=30).read();open(n,'wb').write(d);ok+=1;log.append([n,len(d)])
    except Exception as ex: log.append([n,str(ex)[:80]])
s=round(time.time()-t0,1);print('fotos',ok,'de',len(P),'segundos',s)
json.dump(dict(fotos=ok,total=len(P),seg=s,log=log),open('panos/fotos/out/resumen.json','w'),indent=0)
