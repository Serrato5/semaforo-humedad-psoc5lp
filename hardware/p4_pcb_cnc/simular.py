"""Simula el fresado: parte de la placa toda en cobre, resta lo que barre la fresa
según el G-code y comprueba que cada pad quede unido solo a pads de su misma red."""
import sys, re
sys.path.insert(0, '.')
from diseno import *
from fabricacion import to_machine, TOOL
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly

segs = []; x = y = 0.0; z = 5.0
for line in open('salidas/1_aislamiento.ngc'):
    line = line.split('(')[0].strip()
    if not line: continue
    m = dict(re.findall(r'([XYZ])(-?\d+\.?\d*)', line))
    nx, ny, nz = float(m.get('X', x)), float(m.get('Y', y)), float(m.get('Z', z))
    if line.startswith('G1') and nz < 0 and z < 0 and (nx, ny) != (x, y):
        segs.append(((x, y), (nx, ny)))
    x, y, z = nx, ny, nz
cut = unary_union([LineString(s).buffer(TOOL / 2, 8) for s in segs])
# placa en coordenadas de máquina
plate = box(0, 0, W, H)
remain = plate.difference(cut)
pieces = list(remain.geoms) if hasattr(remain, 'geoms') else [remain]

bad = 0
for i, pc in enumerate(pieces):
    netsin = set()
    for p in allpads:
        mx, my = to_machine(p['x'], p['y'])
        if pc.buffer(1e-6).contains(Point(mx, my)):
            netsin.add(p['net'])
    if len(netsin) > 1:
        bad += 1; print('CORTO: pieza', i, netsin)
# cada red sigue completa
for n in nets:
    idx = set()
    for p in allpads:
        if p['net'] != n: continue
        mx, my = to_machine(p['x'], p['y'])
        for i, pc in enumerate(pieces):
            if pc.buffer(1e-6).contains(Point(mx, my)): idx.add(i)
    if len(idx) != 1:
        bad += 1; print('ABIERTO: red', n, 'en', len(idx), 'piezas')
print('segmentos de corte:', len(segs), ' piezas de cobre resultantes:', len(pieces))
print('SIMULACION OK: sin cortos ni circuitos abiertos' if bad == 0 else f'SIMULACION CON {bad} PROBLEMAS')

fig, ax = plt.subplots(figsize=(8, 6.6))
for pc in pieces:
    if pc.geom_type != 'Polygon': continue
    ax.add_patch(MPoly(list(pc.exterior.coords), fc='#d98c4a', ec='none'))
    for h in pc.interiors: ax.add_patch(MPoly(list(h.coords), fc='white', ec='none'))
for p in allpads:
    mx, my = to_machine(p['x'], p['y'])
    ax.add_patch(plt.Circle((mx, my), p['drill'] / 2, fc='white', ec='k', lw=0.3))
ax.plot([0], [0], 'r+', ms=14, mew=2); ax.text(1, -2.2, 'Origen X0 Y0 (cero de la máquina)', color='red', fontsize=8)
ax.set_xlim(-2, W + 2); ax.set_ylim(-4, H + 2); ax.set_aspect('equal')
ax.set_title('Simulación del fresado (vista desde el cobre, coordenadas de máquina en mm)', fontsize=9)
ax.grid(alpha=0.25)
plt.tight_layout(); plt.savefig('salidas/simulacion_fresado.png', dpi=200)
