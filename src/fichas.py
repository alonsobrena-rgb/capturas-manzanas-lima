#!/usr/bin/env python3
"""Recortes por manzana para la ficha desplegable (7 distritos):
  img/pz/<ID>.jpg  plano de zonificación centrado en la manzana, contorno magenta 3 px (660x660).
  img/vm/<ID>.jpg  captura del visor (resolución nativa) recortada a la manzana + 25 m, mismo contorno. Solo si hay captura.
Idempotente: solo regenera lo que falta o cambió (sello en src/fichas_cache.json). Escribe src/fichas.json (qué manzanas tienen vm).
Geometría: src/mz_geo.json (generado por src/geo_mz.py; se regenera solo si falta alguna manzana).
Ajuste visor-plano: OFFSET_M (m, este/norte) por distrito, medido a ojo sobre las líneas de lotes del visor."""
import json, os, sys, math, hashlib
sys.dont_write_bytecode = True
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
S = os.path.dirname(os.path.abspath(__file__)) + '/'
REPO = os.path.dirname(S[:-1]) + '/'
CAP = os.environ.get('CAPTURAS', '/home/claude/capturas') + '/'
DIST = os.environ.get('DISTRITOS', '/home/claude/distritos') + '/'
DIRS = {'pueblo_libre': 'PL', 'surquillo': 'SQ', 'san_miguel': 'SM', 'magdalena_del_mar': 'MG', 'miraflores': 'MF', 'san_isidro': 'SI', 'barranco': 'BA'}
MPP = {'PL': 1.46993, 'SQ': 1.4111, 'SM': 1.2698, 'MG': 1.175779, 'MF': 1.2701, 'SI': 1.69342, 'BA': 1.1759}   # m por px de plano_full.png
OFFSET_M = {p: (0.0, 0.0) for p in DIRS.values()}      # (este, norte) en m a SUMAR a la geometría antes de dibujar sobre el visor
if os.path.exists(S + 'fichas_offset.json'):
    OFFSET_M.update({k: tuple(v) for k, v in json.load(open(S + 'fichas_offset.json')).items()})
VER = 'v3'
REDO = {'PL', 'SM'}   # distritos con capturas nuevas por manzana (las viejas no se muestran)
MAG = (255, 0, 255)
PZ, VM = REPO + 'img/pz/', REPO + 'img/vm/'
os.makedirs(PZ, exist_ok=True); os.makedirs(VM, exist_ok=True)
D = json.load(open(S + 'dist_av.json'))['mz']
GF = S + 'mz_geo.json'
G = json.load(open(GF)) if os.path.exists(GF) else {}
if any(m['id'] not in G for m in D):
    import subprocess; subprocess.check_call([sys.executable, S + 'geo_mz.py']); G = json.load(open(GF))
cf = S + 'fichas_cache.json'
cache = json.load(open(cf)) if os.path.exists(cf) else {}
h = lambda o: hashlib.md5(json.dumps(o, sort_keys=True).encode()).hexdigest()[:12]
stamp = lambda p: f'{os.stat(p).st_size}-{os.stat(p).st_mtime_ns}'


def outline(dr, rings, w=3):
    for r in rings:
        pts = [tuple(p) for p in r]
        if len(pts) > 2: dr.line(pts + [pts[0]], fill=MAG, width=w, joint='curve')


# ------------------------------ plano ------------------------------
def do_plano(pref, d, ms):
    pp = f'{DIST}{d}/plano_full.png'; ps = stamp(pp); im = None; n = 0
    for m in ms:
        i = m['id']; dst = PZ + i + '.jpg'; sig = h([VER, ps, G[i]])
        if cache.get('pz/' + i) == sig and os.path.exists(dst): continue
        if im is None: im = Image.open(pp).convert('RGB')
        rs = [r['px'] for r in G[i]]; xs = [p[0] for r in rs for p in r]; ys = [p[1] for r in rs for p in r]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        side = max(max(xs) - min(xs), max(ys) - min(ys)) + 2 * 45 / MPP[pref]      # manzana + ~45 m por lado
        side = max(side, 220 / MPP[pref])                                         # mínimo ~220 m de ventana
        x0, y0 = round(cx - side / 2), round(cy - side / 2); s = round(side)
        c = Image.new('RGB', (s, s), 'white'); c.paste(im.crop((x0, y0, x0 + s, y0 + s)), (0, 0))   # PIL rellena de negro fuera: se pisa abajo
        if x0 < 0 or y0 < 0 or x0 + s > im.width or y0 + s > im.height:
            c = Image.new('RGB', (s, s), 'white'); bx0, by0 = max(x0, 0), max(y0, 0); bx1, by1 = min(x0 + s, im.width), min(y0 + s, im.height)
            c.paste(im.crop((bx0, by0, bx1, by1)), (bx0 - x0, by0 - y0))
        k = 660 / s; c = c.resize((660, 660), Image.LANCZOS); dr = ImageDraw.Draw(c)
        outline(dr, [[((x - x0) * k, (y - y0) * k) for x, y in r] for r in rs])
        c.save(dst, 'JPEG', quality=78, optimize=True); cache['pz/' + i] = sig; n += 1
    return n


# ------------------------------ visor ------------------------------
def frame_for(i, frames, geo):
    """marco con la manzana: primero los que la tienen en 'completas', si no los de 'manzanas'; el de centro más cercano."""
    ll = [p for r in geo for p in r['ll']]; clo = sum(p[0] for p in ll) / len(ll); cla = sum(p[1] for p in ll) / len(ll)
    for key in ('completas', 'manzanas'):
        C = [f for f in frames if i in f.get(key, []) and f['png']]
        if C: return min(C, key=lambda f: (f['lat'] - cla) ** 2 + ((f['lng'] - clo) * .977) ** 2)
    return None


def do_visor(pref, d, ms):
    out = {}; n = 0
    v2 = os.environ.get('V2', '/home/claude/recap') + f'/{pref}_v2/'
    pp = os.environ.get('V2', '/home/claude/recap') + f'/plan1_{pref}.json'
    global PLAN_OK; PLAN_OK = {t['cap'] for t in json.load(open(pp))} if os.path.exists(pp) else None
    if pref in REDO:                     # distrito recapturado: solo capturas nuevas (1 por manzana, centradas)
        import glob
        for m in ms:
            i = m['id']; dst = VM + i + '.jpg'
            fs = sorted(glob.glob(v2 + i + '.png') + glob.glob(v2 + i + '_*.png'))
            if PLAN_OK is not None: fs = [f for f in fs if os.path.basename(f)[:-4] in PLAN_OK]   # sin cuadros descartados (pin fuera de la manzana)
            if not fs:
                if os.path.exists(dst): os.remove(dst)
                cache.pop('vm/' + i, None); continue
            out[i] = 'v2'; sig = h([VER, 'v2'] + [stamp(f) for f in fs])
            if cache.get('vm/' + i) == sig and os.path.exists(dst): continue
            ims = [Image.open(f).convert('RGB') for f in fs]; W = max(x.width for x in ims)
            c = Image.new('RGB', (W, sum(x.height for x in ims) + 8 * (len(ims) - 1)), 'white'); y = 0
            for x in ims: c.paste(x, (0, y)); y += x.height + 8
            c.save(dst, 'JPEG', quality=88, optimize=True); cache['vm/' + i] = sig; n += 1
        return n, out
    mp = f'{CAP}{d}/marcos.json'
    if not os.path.exists(mp): return 0, out
    frames = json.load(open(mp))
    for f in frames:
        src = f'{CAP}{d}/{f["id"]}.png'
        if not os.path.isfile(src): src = REPO + f'img/vis/{f["id"]}.jpg'
        f['png'] = src if os.path.isfile(src) else None
    cim = {}
    for m in ms:
        i = m['id']; f = frame_for(i, frames, G[i]); dst = VM + i + '.jpg'
        if not f:
            if os.path.exists(dst): os.remove(dst)
            cache.pop('vm/' + i, None); continue
        sig = h([VER, f['id'], stamp(f['png']), G[i], OFFSET_M[pref]])
        out[i] = f['id']
        if cache.get('vm/' + i) == sig and os.path.exists(dst): continue
        if f['id'] not in cim: cim = {f['id']: Image.open(f['png']).convert('RGB')}
        im = cim[f['id']]; W, H = im.size; cx, cy = (680, 435) if H == 871 else (672, 410) if H == 816 else (W / 2, H / 2 + 0)
        la0, lo0 = f['lat'], f['lng']; res = 156543.03392804097 / 2 ** f.get('z', 19) * math.cos(math.radians(la0))
        k = math.cos(math.radians(la0)); oe, on = OFFSET_M[pref]
        rs = [[(cx + ((lo - lo0) * 111320 * k + oe) / res, cy - ((la - la0) * 110574 + on) / res) for lo, la in r['ll']] for r in G[i]]
        xs = [p[0] for r in rs for p in r]; ys = [p[1] for r in rs for p in r]; mg = 25 / res
        box = tuple(round(v) for v in (max(min(xs) - mg, 0), max(min(ys) - mg, 0), min(max(xs) + mg, W), min(max(ys) + mg, H)))
        if box[2] - box[0] < 40 or box[3] - box[1] < 40:
            out.pop(i); continue
        c = im.crop(box); dr = ImageDraw.Draw(c)
        pass  # sin contorno en la captura del visor (tapaba números y quedaba desfasado)
        c.save(dst, 'JPEG', quality=90, optimize=True); cache['vm/' + i] = sig; n += 1
    return n, out


tot = {}; vm = {}
for d, pref in DIRS.items():
    ms = [m for m in D if m['d'] == pref]
    a = do_plano(pref, d, ms); b, o = do_visor(pref, d, ms); vm.update(o); tot[pref] = (a, b, len(o))
json.dump(cache, open(cf, 'w'), sort_keys=True)
json.dump(sorted(vm), open(S + 'fichas.json', 'w'))
print('fichas nuevas/actualizadas (plano, visor) y total con visor:', tot)
