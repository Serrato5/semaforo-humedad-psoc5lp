"""Diseño de la tarjeta de expansión (una cara, cobre B.Cu, componentes THT arriba).
Coordenadas en mm, vista superior (como KiCad): x a la derecha, y hacia abajo.
"""
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union
from shapely import affinity

W, H = 64.0, 51.0          # tamaño de la tarjeta
CLR = 0.6                  # separación mínima entre cobres de distinta red
EDGE = 1.0                 # cobre a borde de placa
TW = 1.0                   # pista de señal
TWP = 1.5                  # pista de 5 V

# ---------------------------------------------------------------- pads
def rnd(d):  return ('round', d, d)
def oval(w, h): return ('oval', w, h)

R_PAD, R_DR = rnd(2.0), 0.8            # resistencias, condensadores cerámicos
D_PAD, D_DR = rnd(2.2), 1.0            # 1N4007 (DO-41)
O_H = oval(1.6, 2.2)                   # pitch 2,54 en fila horizontal (LED, trimmer, electrolítico)
O_V = oval(2.6, 1.7)                   # pitch 2,54 en columna vertical (conectores)

comps = []   # (ref, valor, footprint, [pads], silk_outline(list of shapely), label_xy)
def comp(ref, val, fp, pads, outline=None, lbl=None):
    comps.append(dict(ref=ref, val=val, fp=fp, pads=pads, outline=outline or [], lbl=lbl))

def pad(num, x, y, shape, drill, net):
    return dict(num=num, x=x, y=y, shape=shape, drill=drill, net=net)

# J2: conector a la PSoC (1x8, vertical)
J2y = [12.0 + 2.54 * i for i in range(8)]
J2nets = ['+5V', 'GND', 'SENS', 'U_SECO', 'U_HUM', 'LED_R', 'LED_A', 'LED_V']
comp('J2', 'PSoC 1x8', 'PinHeader_1x08_P2.54mm',
     [pad(i + 1, 5.0, J2y[i], O_V, 1.0, J2nets[i]) for i in range(8)],
     [box(3.6, J2y[0] - 1.4, 6.4, J2y[-1] + 1.4)], (5.0, 9.0))

# J1: conector del sensor (orden del sensor v1.2: GND, VCC, AOUT)
comp('J1', 'Sensor', 'PinHeader_1x03_P2.54mm',
     [pad(3, 57.5, 8.5, O_V, 1.0, 'AOUT'), pad(2, 57.5, 11.04, O_V, 1.0, '+5V'),
      pad(1, 57.5, 13.58, O_V, 1.0, 'GND')],
     [box(56.1, 7.1, 58.9, 14.98)], (57.5, 16.6))

def axial(ref, val, x1, x2, y, n1, n2, padshape=R_PAD, drill=R_DR, body=(6.3, 2.5), fp='R_Axial_P10.16mm'):
    cx = (x1 + x2) / 2
    comp(ref, val, fp, [pad(1, x1, y, padshape, drill, n1), pad(2, x2, y, padshape, drill, n2)],
         [box(cx - body[0] / 2, y - body[1] / 2, cx + body[0] / 2, y + body[1] / 2)], (cx, y - 2.3))

# ---- protección de entrada
axial('R1', '1k', 40.5, 50.66, 8.5, 'SENS', 'AOUT')
axial('D1', '1N4007', 38.16, 28.0, 5.5, 'SENS', '+5V', D_PAD, D_DR, (5.2, 2.7), 'D_DO-41_P10.16mm')   # pad1 = ánodo
axial('D2', '1N4007', 38.16, 28.0, 12.5, 'SENS', 'GND', D_PAD, D_DR, (5.2, 2.7), 'D_DO-41_P10.16mm')  # pad1 = cátodo
comp('C3', '100n', 'C_Disc_D5.0mm_P5.00mm',
     [pad(1, 53.5, 16.0, R_PAD, R_DR, 'SENS'), pad(2, 53.5, 11.0, R_PAD, R_DR, 'GND')],
     [box(52.25, 9.8, 54.75, 17.2)], (51.0, 13.4))
# marca de cátodo para D1/D2 (banda): D1 cátodo en x=28, D2 cátodo en x=38.16
# ---- alimentación
comp('C2', '10u', 'CP_Radial_D5.0mm_P2.50mm',
     [pad(1, 9.0, 6.0, oval(2.2, 1.6), R_DR, '+5V'), pad(2, 9.0, 8.5, oval(2.2, 1.6), R_DR, 'GND')],
     [Point(9.0, 7.25).buffer(2.5).exterior], (12.8, 7.25))
comp('C1', '100n', 'C_Disc_D5.0mm_P5.00mm',
     [pad(1, 15.0, 5.5, R_PAD, R_DR, '+5V'), pad(2, 15.0, 10.5, R_PAD, R_DR, 'GND')],
     [box(13.75, 4.3, 16.25, 11.7)], (17.8, 8.0))

# ---- umbrales: R6 - RV2 - R5   y   R8 - RV3 - R7
def trimmer(ref, y, wiper_net):
    xs = [39.0, 41.54, 44.08]       # pin3, pin2 (cursor), pin1
    nets = [f'N_{ref}_B', wiper_net, f'N_{ref}_A']
    comp(ref, '10k 3296W', 'Potentiometer_Bourns_3296W_Vertical',
         [pad(3, xs[0], y, O_H, R_DR, nets[0]), pad(2, xs[1], y, O_H, R_DR, nets[1]),
          pad(1, xs[2], y, O_H, R_DR, nets[2])],
         [box(36.8, y - 2.4, 46.3, y + 2.4)], (41.54, y + 3.6))
    return nets

yA, yB = 23.0, 31.0
nA = trimmer('RV2', yA, 'U_SECO')
nB = trimmer('RV3', yB, 'U_HUM')
axial('R6', '3k3', 26.0, 36.16, yA, 'GND', nA[0])
axial('R5', '3k3', 47.0, 57.16, yA, nA[2], '+5V')
axial('R8', '3k3', 26.0, 36.16, yB, 'GND', nB[0])
axial('R7', '3k3', 47.0, 57.16, yB, nB[2], '+5V')
comp('C4', '100n', 'C_Disc_D5.0mm_P5.00mm',
     [pad(1, 48.0, 19.62, R_PAD, R_DR, 'U_SECO'), pad(2, 53.0, 19.62, R_PAD, R_DR, 'GND')],
     [box(46.8, 18.37, 54.2, 20.87)], (50.5, 17.6))
comp('C5', '100n', 'C_Disc_D5.0mm_P5.00mm',
     [pad(1, 48.0, 27.0, R_PAD, R_DR, 'U_HUM'), pad(2, 53.0, 27.0, R_PAD, R_DR, 'GND')],
     [box(46.8, 25.75, 54.2, 28.25)], (56.4, 27.0))

# ---- LEDs
rows = [(35.5, 'LED_R', 'R2', 'D3', 'rojo'), (41.5, 'LED_A', 'R3', 'D4', 'amarillo'), (47.5, 'LED_V', 'R4', 'D5', 'verde')]
for y, net, rref, dref, col in rows:
    axial(rref, '1k', 20.0, 30.16, y, net, f'{net}_K')
    comp(dref, f'LED {col}', 'LED_D5.0mm',
         [pad(1, 51.54, y, O_H, R_DR, 'GND'), pad(2, 49.0, y, O_H, R_DR, f'{net}_K')],   # 1 = cátodo, 2 = ánodo
         [Point(50.27, y).buffer(2.9).exterior], (55.8, y))

# ---------------------------------------------------------------- pistas
tracks = []   # (net, width, [(x,y),...])
def T(net, pts, w=TW): tracks.append((net, w, pts))

# 5 V: J2-1 arriba, borde superior, borde derecho hasta R7
T('+5V', [(5.0, 12.0), (5.0, 2.5), (61.5, 2.5), (61.5, 30.0)], TWP)
T('+5V', [(9.0, 6.0), (9.0, 2.5)], TWP)            # C2+
T('+5V', [(15.0, 5.5), (15.0, 2.5)], TWP)          # C1
T('+5V', [(28.0, 5.5), (28.0, 2.5)], TWP)          # D1 cátodo
T('+5V', [(57.5, 11.04), (61.5, 11.04)], TWP)      # J1 VCC
T('+5V', [(57.16, yA), (61.5, yA)], TWP)           # R5
T('+5V', [(57.16, yB), (61.5, yB)], TWP)           # R7
# sensor y protección
T('AOUT', [(57.5, 8.5), (50.66, 8.5)])
T('SENS', [(38.16, 5.5), (40.5, 8.5)])
T('SENS', [(40.5, 8.5), (38.16, 12.5)])
T('SENS', [(38.16, 12.5), (38.16, 15.5), (10.0, 15.5), (10.0, 17.08), (5.0, 17.08)])
T('SENS', [(38.16, 15.5), (53.0, 15.5), (53.5, 16.0)])
# umbrales
T(nA[0], [(36.16, yA), (39.0, yA)]); T(nA[2], [(44.08, yA), (47.0, yA)])
T(nB[0], [(36.16, yB), (39.0, yB)]); T(nB[2], [(44.08, yB), (47.0, yB)])
T('U_SECO', [(41.54, yA), (41.54, 19.62), (5.0, 19.62)])
T('U_SECO', [(41.54, 19.62), (48.0, 19.62)])
T('U_HUM', [(41.54, yB), (41.54, 27.0), (22.0, 27.0), (22.0, 22.16), (5.0, 22.16)])
T('U_HUM', [(41.54, 27.0), (48.0, 27.0)])
# LEDs (abanico desde J2-6/7/8)
T('LED_R', [(5.0, J2y[5]), (17.0, J2y[5]), (17.0, 35.5), (20.0, 35.5)])
T('LED_A', [(5.0, J2y[6]), (13.0, J2y[6]), (13.0, 41.5), (20.0, 41.5)])
T('LED_V', [(5.0, J2y[7]), (9.0, J2y[7]), (9.0, 47.5), (20.0, 47.5)])
for y, net, *_ in rows:
    T(f'{net}_K', [(30.16, y), (49.0, y)])

# ---------------------------------------------------------------- geometría
def pad_geom(p):
    kind, w, h = p['shape']
    if kind == 'round':
        return Point(p['x'], p['y']).buffer(w / 2, 32)
    r = min(w, h) / 2
    if w >= h:
        seg = LineString([(p['x'] - (w / 2 - r), p['y']), (p['x'] + (w / 2 - r), p['y'])])
    else:
        seg = LineString([(p['x'], p['y'] - (h / 2 - r)), (p['x'], p['y'] + (h / 2 - r))])
    return seg.buffer(r, 32)

def track_geom(t):
    net, w, pts = t
    return LineString(pts).buffer(w / 2, 16)

allpads = [p for c in comps for p in c['pads']]
nets = sorted({p['net'] for p in allpads} | {t[0] for t in tracks})
copper = {}
for n in nets:
    geoms = [pad_geom(p) for p in allpads if p['net'] == n] + [track_geom(t) for t in tracks if t[0] == n]
    copper[n] = unary_union(geoms)

board = box(0, 0, W, H)
inner = board.buffer(-EDGE, join_style=2)
signal = unary_union([g for n, g in copper.items() if n != 'GND'])
pour = inner.difference(signal.buffer(CLR, 16))
gnd_pads = unary_union([pad_geom(p) for p in allpads if p['net'] == 'GND'] +
                       [track_geom(t) for t in tracks if t[0] == 'GND'])
gnd = unary_union([pour, gnd_pads])
copper['GND'] = gnd
