#!/usr/bin/env python3
"""Avance de capturas del visor por distrito -> src/capt.json
JM: manzanas con img.visor en data.json. Resto: marcos de CAPTURAS/<distrito>/marcos.json con <id>.png (sin rehacer/)."""
import json,os
S=os.path.dirname(os.path.abspath(__file__))+'/'
R=os.environ.get('CAPTURAS','/home/claude/capturas')+'/'
out={}
d=json.load(open(S+'data.json'))
out['JM']=dict(n=sum(1 for m in d if (m.get('img') or {}).get('visor')),t=len(d),u='manzanas (método antiguo)')
for p,dn in [('PL','pueblo_libre'),('SM','san_miguel'),('MG','magdalena_del_mar'),('SQ','surquillo'),('MF','miraflores'),('SI','san_isidro'),('BA','barranco')]:
    f=R+dn+'/marcos.json'
    M=json.load(open(f)) if os.path.exists(f) else []
    n=sum(1 for m in M if os.path.isfile(f"{R}{dn}/{m['id']}.png"))
    out[p]=dict(n=n,t=len(M),u='marcos')
json.dump(out,open(S+'capt.json','w'),ensure_ascii=False)
print(json.dumps(out,ensure_ascii=False))
