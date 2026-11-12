// Consulta StreetViewService.getPanorama (preference BEST) para cada punto off=8 de panos/puntos.csv -> panos/panos_js.json
import { chromium } from 'playwright-core';
import fs from 'fs'; import http from 'http'; import path from 'path';
const D = path.resolve('panos');
const html = fs.readFileSync(path.join(D, 'js/sv.html'));
const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8123);
const filas = fs.readFileSync(path.join(D, 'puntos.csv'), 'utf8').trim().split(/\r?\n/);
const cab = filas.shift().split(',');
const pts = filas.map(l => Object.fromEntries(l.split(',').map((v, i) => [cab[i], v]))).filter(p => !p.off || p.off === '8');
const nav = await chromium.launch({ channel: 'chrome' });
const pag = await nav.newPage();
await pag.goto('http://localhost:8123/sv.html');
await pag.evaluate(k => cargar(k), process.env.GOOGLE_MAPS_KEY);
const out = [];
for (const [i, p] of pts.entries()) {
  const r = await pag.evaluate(([a, b]) => consultar(a, b, 15), [+p.lat, +p.lng]);
  out.push({ ...p, ...r });
  if (i === 0) console.log('primera respuesta:', r.status);
}
// Rastreo por vecinos (links): panos a < 45 m de algún punto consultado
const visto = new Set(out.filter(o => o.status === 'OK').map(o => o.pano));
const cola = out.filter(o => o.status === 'OK').flatMap(o => [...o.links.map(l => [l.pano, o]), ...o.tiempos.map(t => [t.pano, o])]);
const dist = (a, b, c, d) => Math.hypot((a - c) * 110574, (b - d) * 108900);
let n = 0;
while (cola.length && n < 1500) {
  const [id, de] = cola.shift(); if (!id || visto.has(id)) continue; visto.add(id); n++;
  const r = await pag.evaluate(([x]) => consultar(0, 0, 0, x), [id]);
  if (r.status !== 'OK') continue;
  const cerca = pts.some(p => dist(+p.lat, +p.lng, r.lat, r.lng) < 45);
  if (!cerca) continue;
  out.push({ mz: de.mz, lado: de.lado, s: '', off: 'vecino', ...r });
  for (const l of r.links) if (!visto.has(l.pano)) cola.push([l.pano, de]);
  for (const t of r.tiempos) if (!visto.has(t.pano)) cola.push([t.pano, de]);
}
console.log('rastreo:', n, 'consultas por vecino');
fs.writeFileSync(path.join(D, 'panos_js.json'), JSON.stringify(out));
console.log(out.length, 'consultas;', new Set(out.filter(o => o.status === 'OK').map(o => o.pano)).size, 'panos distintos');
await nav.close(); srv.close();
