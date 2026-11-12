#!/usr/bin/env python3
"""Copia las capturas del visor (PNG) a img/vis/<ID>.jpg (JPG q92, tamaño original) y genera src/vis.json.
Idempotente: solo convierte lo nuevo o modificado (sello en src/vis_cache.json)."""
import json,os
from PIL import Image
S=os.path.dirname(os.path.abspath(__file__))+'/'
REPO=os.path.dirname(S[:-1])+'/'
C=os.environ.get('CAPTURAS','/home/claude/capturas')+'/'
OUT=REPO+'img/vis/'
DIRS={'pueblo_libre':'PL','surquillo':'SQ','san_miguel':'SM','magdalena_del_mar':'MG','miraflores':'MF','san_isidro':'SI','barranco':'BA'}
os.makedirs(OUT,exist_ok=True)
cf=S+'vis_cache.json'
cache=json.load(open(cf)) if os.path.exists(cf) else {}
vis={};nuevas=[]
for d,pref in DIRS.items():
    mp=C+d+'/marcos.json'
    if not os.path.exists(mp): vis[pref]=[];continue
    ms=sorted((m for m in json.load(open(mp)) if os.path.isfile(f'{C}{d}/{m["id"]}.png')),key=lambda m:m['id'])
    for m in ms:
        src=f'{C}{d}/{m["id"]}.png';dst=OUT+m['id']+'.jpg';st=os.stat(src)
        sig=f'{st.st_size}-{st.st_mtime_ns}'
        if cache.get(m['id'])!=sig or not os.path.exists(dst):
            Image.open(src).convert('RGB').save(dst,'JPEG',quality=92,optimize=True)
            cache[m['id']]=sig;nuevas.append(m['id'])
    vis[pref]=[{'id':m['id'],'lat':m['lat'],'lng':m['lng'],'manzanas':m.get('manzanas',[])} for m in ms]
json.dump(cache,open(cf,'w'),sort_keys=True)
json.dump(vis,open(S+'vis.json','w'),ensure_ascii=False,sort_keys=True)
print('capturas nuevas/actualizadas:',len(nuevas),'| por distrito:',{k:len(v) for k,v in vis.items()})
