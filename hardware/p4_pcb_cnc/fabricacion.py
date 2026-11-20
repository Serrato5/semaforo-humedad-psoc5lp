"""Genera G-code (Mach3), Gerber, Excellon y archivo KiCad a partir de diseno.py."""
import sys, math, os, datetime
sys.path.insert(0, '.')
from diseno import *

OUT = 'salidas'
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ parámetros CNC
TOOL = 0.25            # diámetro efectivo de la fresa en V 30° (el que usa el laboratorio)
PASSES = [0.125, 0.300, 0.475]   # desplazamientos del centro de la fresa desde el cobre (3 pasadas)
Z_CUT = -0.10          # profundidad de aislamiento (ajustar con pasada de prueba)
Z_MARK = -0.30         # marca de centro para perforar a mano
Z_EDGE = -0.15         # marca del contorno para cortar con segueta
Z_SAFE = 2.0
Z_TRAVEL = 1.0
F_CUT, F_PLUNGE, RPM = 90, 30, 12500

def to_machine(x, y):
    """Vista desde el cobre: espejo en X. Origen = esquina inferior izquierda vista desde el cobre."""
    return (W - x, H - y)

def rings(g):
    out = []
    for p in (g.geoms if hasattr(g, 'geoms') else [g]):
        if p.geom_type != 'Polygon' or p.is_empty: continue
        out.append(list(p.exterior.simplify(0.01).coords))
        for h in p.interiors:
            out.append(list(h.simplify(0.01).coords))
    return out

def order_paths(paths, start=(0, 0)):
    """vecino más cercano para reducir recorridos en vacío"""
    rest = paths[:]; res = []; cur = start
    while rest:
        i = min(range(len(rest)), key=lambda k: math.dist(cur, rest[k][0]))
        p = rest.pop(i)
        # en anillos, empezar en el punto más cercano
        if p[0] == p[-1]:
            j = min(range(len(p) - 1), key=lambda k: math.dist(cur, p[k]))
            p = p[j:-1] + p[:j] + [p[j]]
        res.append(p); cur = p[-1]
    return res

def header(title, extra=''):
    return [f'({title})', '(Tarjeta de expansion - semaforo de humedad - PSoC 5LP)',
            f'(Generado {datetime.date.today()} - placa {W:.0f} x {H:.0f} mm, cara de cobre hacia arriba)',
            '(Origen X0 Y0 = esquina inferior izquierda de la placa vista desde el cobre; Z0 = superficie del cobre)',
            extra,
            'G21 G90 G94 G17 G40 G49', f'G0 Z{Z_SAFE:.3f}', f'M3 S{RPM}', 'G4 P3']

def footer():
    return [f'G0 Z{Z_SAFE:.3f}', 'M5', 'G0 X0 Y0', 'M30']

def cut_paths(paths, z, name):
    lines = []; length = 0.0
    for p in paths:
        mp = [to_machine(*q) for q in p]
        lines.append(f'G0 Z{Z_TRAVEL:.3f}')
        lines.append(f'G0 X{mp[0][0]:.4f} Y{mp[0][1]:.4f}')
        lines.append(f'G1 Z{z:.4f} F{F_PLUNGE}')
        lines.append(f'G1 F{F_CUT}')
        for a, b in zip(mp, mp[1:]):
            lines.append(f'G1 X{b[0]:.4f} Y{b[1]:.4f}')
            length += math.dist(a, b)
        lines.append(f'G0 Z{Z_TRAVEL:.3f}')
    return lines, length

# 1) aislamiento -------------------------------------------------------------
signal_only = unary_union([g for n, g in copper.items() if n != 'GND'])
iso_paths = []
for d in PASSES:
    iso_paths += rings(signal_only.buffer(d, 16))
iso_paths = order_paths([p for p in iso_paths if len(p) > 2])
body, L = cut_paths(iso_paths, Z_CUT, 'iso')
g = header('1 - AISLAMIENTO DE PISTAS', f'(Herramienta: fresa en V 30 grados, diametro efectivo {TOOL} mm; {len(PASSES)} pasadas; Z {Z_CUT} mm; F{F_CUT})') + body + footer()
open(f'{OUT}/1_aislamiento.ngc', 'w').write('\n'.join(g) + '\n')
t_iso = L / F_CUT

# 2) marcas de taladro ------------------------------------------------------
holes_list = [(p['x'], p['y'], p['drill']) for p in allpads]
pts = order_paths([[(x, y), (x, y)] for x, y, _ in holes_list])
g = header('2 - MARCAS DE CENTRO PARA PERFORAR A MANO', f'(Misma fresa en V; punzonado a Z {Z_MARK} mm; {len(pts)} huecos)')
for p in pts:
    x, y = to_machine(*p[0])
    g += [f'G0 Z{Z_TRAVEL:.3f}', f'G0 X{x:.4f} Y{y:.4f}', f'G1 Z{Z_MARK:.4f} F{F_PLUNGE}', f'G0 Z{Z_TRAVEL:.3f}']
g += footer()
open(f'{OUT}/2_marcas_taladros.ngc', 'w').write('\n'.join(g) + '\n')

# 3) contorno ---------------------------------------------------------------
edge = [[(0, 0), (W, 0), (W, H), (0, H), (0, 0)]]
body, Le = cut_paths(edge, Z_EDGE, 'edge')
g = header('3 - MARCA DEL CONTORNO (CORTAR DESPUES CON SEGUETA O CIZALLA)', f'(Z {Z_EDGE} mm)') + body + footer()
open(f'{OUT}/3_contorno.ngc', 'w').write('\n'.join(g) + '\n')

# ------------------------------------------------------------------ Gerber
def gnum(v): return f'{int(round(v * 1e6))}'
def gxy(x, y): return f'X{gnum(x)}Y{gnum(H - y)}'
def region(ring):
    s = ['G36*', f'{gxy(*ring[0])}D02*', 'G01*']
    s += [f'{gxy(*q)}D01*' for q in ring[1:]]
    s += ['G37*']
    return s

def gerber_copper():
    s = ['%TF.GenerationSoftware,Claude,diseno.py*%', '%TF.FileFunction,Copper,L2,Bot*%', '%FSLAX46Y46*%', '%MOMM*%', '%LPD*%']
    def polys(g): return [p for p in (g.geoms if hasattr(g, 'geoms') else [g]) if p.geom_type == 'Polygon']
    order = [copper['GND']] + [g for n, g in copper.items() if n != 'GND']
    for g in order:
        for p in polys(g):
            s += ['%LPD*%'] + region(list(p.exterior.coords))
            for h in p.interiors:
                s += ['%LPC*%'] + region(list(h.coords))
    s += ['%LPD*%', 'M02*']
    return '\n'.join(s) + '\n'

open(f'{OUT}/tarjeta-B_Cu.gbr', 'w').write(gerber_copper())
edge_g = ['%TF.FileFunction,Profile,NP*%', '%FSLAX46Y46*%', '%MOMM*%', '%ADD10C,0.100*%', 'D10*',
          f'{gxy(0,0)}D02*', 'G01*', f'{gxy(W,0)}D01*', f'{gxy(W,H)}D01*', f'{gxy(0,H)}D01*', f'{gxy(0,0)}D01*', 'M02*']
open(f'{OUT}/tarjeta-Edge_Cuts.gbr', 'w').write('\n'.join(edge_g) + '\n')

drills = sorted({d for *_, d in holes_list})
ex = ['M48', 'METRIC,TZ', 'FMAT,2'] + [f'T{i+1}C{d:.3f}' for i, d in enumerate(drills)] + ['%', 'G90', 'G05']
for i, d in enumerate(drills):
    ex.append(f'T{i+1}')
    for x, y, dd in holes_list:
        if dd == d: ex.append(f'X{x:.3f}Y{H - y:.3f}')
ex.append('M30')
open(f'{OUT}/tarjeta.drl', 'w').write('\n'.join(ex) + '\n')

# ------------------------------------------------------------------ KiCad (.kicad_pcb)
netnames = ['GND'] + [n for n in nets if n != 'GND']
nid = {n: i + 1 for i, n in enumerate(netnames)}
def q(s): return '"' + s.replace('"', '') + '"'
k = ['(kicad_pcb (version 20221018) (generator pcbnew)', '  (general (thickness 1.6))', '  (paper "A4")',
     '  (layers (0 "F.Cu" signal) (31 "B.Cu" signal) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen")',
     '    (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))',
     '  (setup (pad_to_mask_clearance 0))', '  (net 0 "")']
k += [f'  (net {nid[n]} {q(n)})' for n in netnames]
for c in comps:
    xs = [p['x'] for p in c['pads']]; ys = [p['y'] for p in c['pads']]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    k.append(f'  (footprint {q("Proyecto:" + c["fp"])} (layer "F.Cu") (at {cx:.3f} {cy:.3f})')
    lx, ly = c['lbl']
    k.append(f'    (fp_text reference {q(c["ref"])} (at {lx-cx:.3f} {ly-cy:.3f}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))')
    k.append(f'    (fp_text value {q(c["val"])} (at 0 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))')
    for o in c['outline']:
        if o.geom_type == 'Polygon':
            x0, y0, x1, y1 = o.bounds
            k.append(f'    (fp_rect (start {x0-cx:.3f} {y0-cy:.3f}) (end {x1-cx:.3f} {y1-cy:.3f}) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
        else:
            x0, y0, x1, y1 = o.bounds
            r = (x1 - x0) / 2; ccx, ccy = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
            k.append(f'    (fp_circle (center {ccx:.3f} {ccy:.3f}) (end {ccx+r:.3f} {ccy:.3f}) (stroke (width 0.12) (type solid)) (fill none) (layer "F.SilkS"))')
    for p in c['pads']:
        kind, w, h = p['shape']
        shp = 'circle' if kind == 'round' else 'oval'
        k.append(f'    (pad {q(str(p["num"]))} thru_hole {shp} (at {p["x"]-cx:.3f} {p["y"]-cy:.3f}) (size {w} {h}) (drill {p["drill"]}) (layers "*.Cu" "*.Mask") (net {nid[p["net"]]} {q(p["net"])}))')
    k.append('  )')
for net, w, pts in tracks:
    for a, b in zip(pts, pts[1:]):
        k.append(f'  (segment (start {a[0]:.3f} {a[1]:.3f}) (end {b[0]:.3f} {b[1]:.3f}) (width {w}) (layer "B.Cu") (net {nid[net]}))')
k.append(f'  (gr_rect (start 0 0) (end {W} {H}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts"))')
k.append(f'  (zone (net {nid["GND"]}) (net_name "GND") (layer "B.Cu") (hatch edge 0.5) (connect_pads yes (clearance {CLR}))'
         f' (min_thickness 0.25) (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))'
         f' (polygon (pts (xy {EDGE} {EDGE}) (xy {W-EDGE} {EDGE}) (xy {W-EDGE} {H-EDGE}) (xy {EDGE} {H-EDGE}))))')
k.append(')')
open(f'{OUT}/tarjeta_humedad.kicad_pcb', 'w').write('\n'.join(k) + '\n')

# ------------------------------------------------------------------ resumen
print(f'aislamiento: {len(iso_paths)} trayectorias, {L:.0f} mm, ~{t_iso:.0f} min a F{F_CUT}')
print(f'taladros: {len(holes_list)} ({", ".join(f"{d} mm x{sum(1 for *_, dd in holes_list if dd == d)}" for d in drills)})')
print(f'contorno: {Le:.0f} mm')
