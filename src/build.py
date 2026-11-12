#!/usr/bin/env python3
"""Genera index.html (raíz del repo) desde src/tpl.html + datos. Quita referencias a fotos Street View inexistentes."""
import json,os,datetime
S=os.path.dirname(os.path.abspath(__file__))+'/'
REPO=os.path.dirname(S[:-1])+'/'
L=lambda f:json.load(open(S+f,encoding='utf-8'))
data=L('data.json')
for m in data:
    for p in (m.get('predios') or []):
        s=p.get('sv_img')
        if s and not os.path.exists(REPO+s.split('#')[0]): p['sv_img']=None
fecha=os.environ.get('FECHA') or datetime.date.today().strftime('%d-%m-%Y')
t=open(S+'tpl.html',encoding='utf-8').read()
for k,v in [('__DATA__',data),('__DIST__',L('dist_av.json')),('__CAPT__',L('capt.json')),('__VIS__',L('vis.json')),('__FICHAS__',L('fichas.json'))]:
    t=t.replace(k,json.dumps(v,ensure_ascii=False,sort_keys=True).replace('</','<\\/'))
t=t.replace('__FECHA__',fecha)
open(REPO+'index.html','w',encoding='utf-8').write(t)
print('index.html',len(t),'bytes')
