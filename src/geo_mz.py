#!/usr/bin/env python3
"""Geometría de cada manzana (polígono) en píxeles del plano_full.png y en WGS84 -> src/mz_geo.json.
Adaptadores copiados de /home/claude/capturas/tiler2.py (etiquetas de la etapa 1 por id_original, georef por distrito).
Solo se necesita si falta una manzana en mz_geo.json (depende de archivos de trabajo en /tmp y /home/claude).
Uso: geo_mz.py [distrito ...]"""
import sys, os, json, pickle
sys.dont_write_bytecode = True
import numpy as np, cv2
from pyproj import Transformer

S = os.path.dirname(os.path.abspath(__file__)) + '/'
DIST = os.environ.get('DISTRITOS', '/home/claude/distritos') + '/'
PREF = {'pueblo_libre': 'PL', 'san_miguel': 'SM', 'surquillo': 'SQ', 'miraflores': 'MF', 'san_isidro': 'SI', 'magdalena_del_mar': 'MG', 'barranco': 'BA'}
tr = Transformer.from_crs('EPSG:24878', 'EPSG:4326', always_xy=True)


def adapter(dist):
    """-> lab, lab_of{id_original: etiqueta}, px2EN(x,y lab), EN2px(E,N -> px del plano_full.png)"""
    BASE = DIST + dist
    if dist == 'pueblo_libre':
        G = json.load(open(f'{BASE}/georef.json'))
        lab = np.load('/home/claude/pl_work/lab3.npy'); O = json.load(open('/home/claude/pl_work/out.json')); MZ = json.load(open(f'{BASE}/manzanas.json'))
        lab_of = {MZ[i]['id']: O[i]['label'] for i in range(len(MZ))}
        px2EN = lambda x, y: (G['a_x'] * (x / 2.4) + G['b_x'], G['a_y'] * (y / 2.4) + G['b_y'])
        EN2px = lambda E, N: (2.4 * (E - G['b_x']) / G['a_x'], 2.4 * (N - G['b_y']) / G['a_y'])
    elif dist == 'surquillo':
        d = np.load('/tmp/sq_seg.npz'); lab = d['comp']; oy, ox = [int(v) for v in d['off']]
        lab_of = json.load(open('/tmp/sq_idmap.json'))
        px2EN = lambda x, y: (276797.782 + 1.41129 * (x + ox), 8663092.83 - 1.410835 * (y + oy + 5))
        EN2px = lambda E, N: ((E - 276797.782) / 1.41129, (8663092.83 - N) / 1.410835 - 5)
    elif dist == 'miraflores':
        lab = np.load(f'{BASE}/L.npy'); ZP = 2.7777778; MFS = 1000 / 283.44
        lab_of = {m['id']: m['_i'] for m in json.load(open(f'{BASE}/manzanas.json'))}
        px2EN = lambda x, y: (276000 + (x / ZP - 285.6) * MFS, 8661000 - (y / ZP - 385.96) * MFS)
        EN2px = lambda E, N: (ZP * ((E - 276000) / MFS + 285.6), ZP * ((8661000 - N) / MFS + 385.96))
    elif dist == 'san_isidro':
        d = np.load(f'{BASE}/work/seg.npz'); lab = d['L']; oy, ox = [int(v) for v in d['off']]
        lab_of = json.load(open(f'{BASE}/work/av/idmap.json'))
        GX0, GE0, GY0, GN0 = 281.3, 275000.0, 411.9, 8663000.0; SS = (1982.0 - 281.3) / 6000.0
        px2EN = lambda x, y: (GE0 + ((x + ox) / 4.0 - GX0) / SS, GN0 - ((y + oy) / 4.0 - GY0) / SS + 6.0)
        # plano_full.png: 1 px = 0.48 pt
        EN2px = lambda E, N: ((GX0 + (E - GE0) * SS) / 0.48, (GY0 + (GN0 + 6.0 - N) * SS) / 0.48)
    elif dist == 'magdalena_del_mar':
        lab = np.load('/tmp/mg_L.npy')
        lab_of = {o['id']: int(o['_lab']) for o in pickle.load(open('/tmp/mg_out2.pkl', 'rb'))}
        px2EN = lambda x, y: (1.175778904792841 * x + 272338.9771826729 - 2.0, -1.1757788180994362 * y + 8664812.267084962 + 2.0)
        EN2px = lambda E, N: ((E + 2.0 - 272338.9771826729) / 1.175778904792841, (N - 2.0 - 8664812.267084962) / -1.1757788180994362)
    elif dist == 'barranco':
        WK = f'{BASE}/work/av'
        lab = np.load(f'{WK}/seg.npz')['comp']; lab_of = json.load(open(f'{WK}/idmap.json'))
        gj = json.load(open(f'{BASE}/georef.json'))['afin_px_a_psad56']; (ea, eb, ec), (na, nb, nc) = gj['E'], gj['N']
        px2EN = lambda x, y: (ea * x + eb * y + ec, na * x + nb * y + nc)
        A = np.array([[ea, eb], [na, nb]]); Ai = np.linalg.inv(A)
        EN2px = lambda E, N: tuple(Ai @ np.array([E - ec, N - nc]))
    elif dist == 'san_miguel':
        d = np.load('/tmp/smav/seg.npz'); lab = d['comp']; oy, ox = [int(v) for v in d['off']]
        lab_of = json.load(open('/tmp/smav/idmap.json')); g = json.load(open(f'{BASE}/georef.json'))
        px2EN = lambda x, y: ((x + ox - g['dx'] - g['bx']) / g['ax'], (y + oy - g['dy'] - g['by']) / g['ay'])
        EN2px = lambda E, N: (g['ax'] * E + g['bx'] + g['dx'], g['ay'] * N + g['by'] + g['dy'])
    return lab, lab_of, px2EN, EN2px


def rings(m, eps=0.8):
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cs = [c for c in cs if cv2.contourArea(c) >= 12]
    if not cs: return []
    amax = max(cv2.contourArea(c) for c in cs)
    return [cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float) for c in cs if cv2.contourArea(c) >= .02 * amax]


def build(dist):
    pref = PREF[dist]; lab, lab_of, px2EN, EN2px = adapter(dist)
    from scipy import ndimage as ndi
    OBJ = ndi.find_objects(lab); H, W = lab.shape; out = {}
    for o in json.load(open(f'{DIST}{dist}/manzanas_avenidas.json')):
        i = int(lab_of[o['id_original']]); sl = OBJ[i - 1]
        y0, x0 = max(sl[0].start - 2, 0), max(sl[1].start - 2, 0)
        sub = lab[y0:min(sl[0].stop + 2, H), x0:min(sl[1].stop + 2, W)] == i
        rs = []
        for r in rings(np.pad(sub, 1)):                      # relleno de 1 px para que el contorno cierre en el borde
            x = r[:, 0] - 1 + x0; y = r[:, 1] - 1 + y0
            E, N = px2EN(x, y); px, py = EN2px(E, N); lo, la = tr.transform(E, N)
            rs.append(dict(px=np.round(np.c_[px, py], 1).tolist(), ll=np.round(np.c_[lo, la], 6).tolist()))
        out[o['id']] = rs
    return out


if __name__ == '__main__':
    f = S + 'mz_geo.json'
    G = json.load(open(f)) if os.path.exists(f) else {}
    want = sys.argv[1:] or list(PREF)
    for d in want:
        G.update(build(d)); print(d, len(G))
    json.dump(G, open(f, 'w'), separators=(',', ':'), sort_keys=True)
