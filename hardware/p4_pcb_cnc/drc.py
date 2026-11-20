import sys, itertools
sys.path.insert(0, '.')
from diseno import *
from shapely.geometry import MultiPolygon, Polygon

ok = True
def err(m):
    global ok; ok = False; print('ERROR:', m)

# 1) separación entre redes (sin el plano; el plano se construye con CLR)
pure = {}
for n in nets:
    geoms = [pad_geom(p) for p in allpads if p['net'] == n] + [track_geom(t) for t in tracks if t[0] == n]
    pure[n] = unary_union(geoms)
minpair = (9e9, None)
for a, b in itertools.combinations(nets, 2):
    d = pure[a].distance(pure[b])
    if d < minpair[0]: minpair = (d, (a, b))
    if d < CLR - 1e-6:
        err(f'separación {d:.3f} mm entre {a} y {b}')
print(f'separación mínima entre redes: {minpair[0]:.3f} mm ({minpair[1]})')

# 2) borde
for n, g in pure.items():
    d = g.exterior.distance(board.exterior) if isinstance(g, Polygon) else min(p.exterior.distance(board.exterior) for p in g.geoms)
    if not board.buffer(-EDGE + 1e-6).contains(g):
        err(f'red {n} a menos de {EDGE} mm del borde')

# 3) conectividad de cada red (sin GND)
for n in nets:
    if n == 'GND': continue
    g = pure[n]
    parts = len(g.geoms) if hasattr(g, 'geoms') else 1
    npads = sum(1 for p in allpads if p['net'] == n)
    if parts != 1:
        err(f'red {n} partida en {parts} piezas')
    if npads < 2:
        err(f'red {n} con solo {npads} pad')

# 4) GND: plano + pads, todos los pads GND en una sola pieza
gp = copper['GND']
pieces = list(gp.geoms) if hasattr(gp, 'geoms') else [gp]
gpads = [p for p in allpads if p['net'] == 'GND']
idx = set()
for p in gpads:
    pt = Point(p['x'], p['y'])
    for i, pc in enumerate(pieces):
        if pc.buffer(1e-6).contains(pt):
            idx.add(i)
print(f'GND: {len(pieces)} piezas de cobre; pads GND repartidos en {len(idx)} pieza(s)')
if len(idx) != 1:
    err('pads GND no quedan unidos por el plano')
# anchura mínima del plano en el cuello: comprobar que sigue unido con erosión de 0.3 mm
ero = gp.buffer(-0.3)
epieces = list(ero.geoms) if hasattr(ero, 'geoms') else [ero]
idx2 = set()
for p in gpads:
    pt = Point(p['x'], p['y'])
    for i, pc in enumerate(epieces):
        if pc.distance(pt) < 1.2:
            idx2.add(i)
print(f'GND con cuellos de 0,6 mm erosionados: pads en {len(idx2)} pieza(s)')

# 5) cada pad toca cobre de su red con otro pad (pads aislados)
for p in allpads:
    if p['net'] == 'GND': continue
    others = [q for q in allpads if q['net'] == p['net'] and q is not p]
    if not others:
        err(f"pad {p} sin pareja")

# 6) cuerpos de componentes que se pisan
outs = []
for c in comps:
    for o in c['outline']:
        poly = Polygon(o) if o.geom_type == 'LinearRing' else o
        outs.append((c['ref'], poly))
for (ra, a), (rb, b) in itertools.combinations(outs, 2):
    if ra != rb and a.intersection(b).area > 0.05:
        err(f'cuerpos de {ra} y {rb} se solapan ({a.intersection(b).area:.2f} mm²)')
# cuerpos fuera de placa
for r, a in outs:
    if not board.contains(a):
        err(f'cuerpo de {r} sale de la placa')

print('nets:', len(nets), ' pads:', len(allpads), ' pistas:', len(tracks))
print('DRC OK' if ok else 'DRC CON ERRORES')
for i, pc in enumerate(epieces):
    ps=[ (p['x'],p['y']) for p in gpads if pc.distance(Point(p['x'],p['y']))<1.2]
    print('pieza erosionada', i, 'area %.1f'%pc.area, ps)
