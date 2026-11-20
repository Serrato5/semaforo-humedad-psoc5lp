#!/usr/bin/env python3
"""Coloca la PCB del P5 con la API de KiCad (pcbnew). Uso:
   python gen_pcb.py place  spec.json ids.json salida.kicad_pcb   -> coloca y exporta .dsn para Freerouting
   python gen_pcb.py finish entrada.kicad_pcb ruta.ses            -> importa rutas, planos de GND, serigrafía
Parámetros por variables de entorno: ROW (mm entre filas del kit), FLIP=1 si la PSoC entra boca abajo."""
import pcbnew, json, sys, os, math
MM = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
FPDIR = os.path.expanduser('~/squashfs-root/share/kicad/footprints/')
ROW = float(os.environ.get('ROW', '20.32'))
FLIP = os.environ.get('FLIP', '0') == '1'
W, H = 80.0, 62.0
YA = 8.0                      # fila superior del socket
X26 = 9.0                     # pin 26 a la izquierda (lado del KitProg, que queda por fuera de la tarjeta)
YTOP, YBOT = (YA, YA + ROW)
ROWY = {'J1': YTOP, 'J2': YBOT} if not FLIP else {'J1': YBOT, 'J2': YTOP}
LOW = YBOT + 4.5              # inicio de la zona de componentes, fuera del cuerpo del kit

PLACE = {   # ref: (x, y, rot)
 'J3': (5.0, LOW + 7.0, 0),
 'R1': (11.5, LOW + 12.08, 0), 'C3': (17.5, LOW + 12.08, 90),
 'D1': (12.5, LOW + 7.5, 0), 'D2': (12.5, LOW + 16.5, 0),
 'R5': (25.0, LOW + 3.0, 0), 'RV2': (31.5, LOW + 5.5, 0), 'R6': (25.0, LOW + 8.0, 0), 'C4': (37.5, LOW + 5.5, 90),
 'R7': (25.0, LOW + 13.0, 0), 'RV3': (31.5, LOW + 15.5, 0), 'R8': (25.0, LOW + 18.0, 0), 'C5': (37.5, LOW + 15.5, 90),
 'C1': (62.0, LOW + 1.5, 0), 'C2': (68.0, LOW + 1.5, 0),
 'R2': (50.0, LOW + 6.0, 0), 'D3': (57.0, LOW + 6.0, 180),
 'R3': (50.0, LOW + 11.0, 0), 'D4': (57.0, LOW + 11.0, 180),
 'R4': (50.0, LOW + 16.0, 0), 'D5': (57.0, LOW + 16.0, 180),
 'H1': (3.5, 3.5, 0), 'H2': (W - 3.5, 3.5, 0), 'H3': (3.5, H - 3.5, 0), 'H4': (W - 3.5, H - 3.5, 0),
}
TPX = [44.0, 47.5, 51.0, 54.5, 58.0]
for i in range(5): PLACE[f'TP{i+1}'] = (TPX[i] + 6, H - 3.2, 0)

def place(spec, ids, out):
    b = pcbnew.BOARD()
    ds = b.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    ns = ds.m_NetSettings
    nc = ns.GetDefaultNetclass()
    nc.SetTrackWidth(MM(0.3)); nc.SetClearance(MM(0.2)); nc.SetViaDiameter(MM(0.6)); nc.SetViaDrill(MM(0.3))
    ds.m_MinClearance = MM(0.15); ds.m_TrackMinWidth = MM(0.15); ds.m_ViasMinSize = MM(0.5); ds.m_MinThroughDrill = MM(0.3)
    ds.m_HoleToHoleMin = MM(0.5); ds.m_CopperEdgeClearance = MM(0.4)
    # borde
    pts = [(0, 0), (W, 0), (W, H), (0, H)]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))
        s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
    nets = {}
    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(b, '/' + n); b.Add(ni); nets[n] = ni
        return nets[n]
    for p in spec['parts']:
        lib, name = p['fp'].split(':')
        fp = pcbnew.FootprintLoad(FPDIR + lib + '.pretty', name)
        fp.SetFPIDAsString(p['fp'])
        fp.SetReference(p['ref']); fp.SetValue(p['val'])
        fp.SetPath(pcbnew.KIID_PATH(f"/{ids['uuids'][p['ref']]}"))
        if 'TC33X' in p['fp']:
            for m in fp.Models(): m.m_Filename = '${KICAD10_3DMODEL_DIR}/Potentiometer_SMD.3dshapes/Potentiometer_Bourns_3314J_Vertical.step'
        if p.get('kit'):
            row, kit = p['kit']
            # tira horizontal: pin 1 de la tira sobre el pin kit[0] del kit, avanzando hacia la izquierda
            fp.SetOrientationDegrees(-90)
            fp.SetPosition(V(X26 + (26 - kit[0]) * 2.54, ROWY[row]))
        else:
            x, y, r = PLACE[p['ref']]
            fp.SetOrientationDegrees(r); fp.SetPosition(V(x, y))
        if p.get('lcsc'):
            fp.SetField('LCSC', p['lcsc'])
        fp.SetField('Description', p.get('desc', ''))
        for f in fp.GetFields():
            if f.GetName() in ('LCSC', 'Description'): f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
        if p['ref'][:2] in ('TP', 'H1', 'H2', 'H3', 'H4') or p['ref'] in ('D3', 'D4', 'D5'):
            fp.Reference().SetVisible(False)
        if p.get('nobom'):
            fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        if p['ref'].startswith('J'):
            fp.SetExcludedFromPosFiles(True)      # THT: los compra y suelda el equipo
        for pad in fp.Pads():
            n = p['nets'].get(pad.GetNumber())
            if n: pad.SetNet(net(n))
            elif p.get('kit'):
                k = pad.GetNumber(); nm = f'unconnected-({p["ref"]}-Pin_{k}-Pad{k})'
                ni = pcbnew.NETINFO_ITEM(b, nm); b.Add(ni); pad.SetNet(ni)
        b.Add(fp)
    b.BuildConnectivity()
    pcbnew.SaveBoard(out, b)
    pcbnew.ExportSpecctraDSN(b, out.replace('.kicad_pcb', '.dsn'))
    # informe de colocación
    for fp in b.GetFootprints():
        bb = fp.GetBoundingBox(False, False)
        if bb.GetLeft() < 0 or bb.GetRight() > MM(W) or bb.GetTop() < 0 or bb.GetBottom() > MM(H):
            print('FUERA DE LA TARJETA:', fp.GetReference())
    print('ok place', len(b.GetFootprints()), 'huellas', len(nets), 'redes', 'ROW', ROW, 'FLIP', FLIP)

def text(b, s, x, y, size=1.2, layer=pcbnew.F_SilkS, bold=True, rot=0, just=0):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(MM(size), MM(size))); t.SetTextThickness(MM(size * 0.15)); t.SetBold(bold)
    t.SetTextAngleDegrees(rot)
    if just: t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if just < 0 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    b.Add(t)

def finish(pcb, ses):
    b = pcbnew.LoadBoard(pcb)
    if ses:
        ok = pcbnew.ImportSpecctraSES(b, ses); print('SES importado', ok)
    gnd = b.FindNet('/GND')
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(gnd)
        z.SetLocalClearance(MM(0.3)); z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL); z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        o = z.Outline(); o.NewOutline()
        for x, y in [(0.3, 0.3), (W - 0.3, 0.3), (W - 0.3, H - 0.3), (0.3, H - 0.3)]: o.Append(MM(x), MM(y))
        b.Add(z)
    # serigrafía
    L = LOW
    text(b, 'SEMÁFORO DE HUMEDAD · PSoC 5LP', 40, YBOT + 2.6 if False else H - 6.8, 1.1)
    text(b, 'USCO · Electrónica Análoga 3 · P5 2026-B', 40, H - 5.2 + 0.0, 0.8, bold=False)
    for lab, yy in [('SECO', L + 6.0), ('MEDIO', L + 11.0), ('HÚMEDO', L + 16.0)]:
        text(b, lab, 60.0, yy, 1.0, just=-1)
    text(b, 'U SECO', 31.5, L + 8.7, 0.8); text(b, 'U HÚM', 31.5, L + 18.7, 0.8)
    for k, lab in enumerate(['GND', 'VCC', 'AOUT']):
        text(b, lab, 6.9, PLACE['J3'][1] + 2.54 * k, 0.8, just=-1)
    text(b, 'SENSOR', 5.0, L + 2.4, 0.8)
    for i, lab in enumerate(['VB', 'US', 'UH', '5V', 'G']):
        text(b, lab, TPX[i] + 6, H - 1.1, 0.8, bold=False)
    text(b, 'Fila J1 del PSoC', 40, ROWY['J1'] + 3.2, 0.9)
    text(b, 'Fila J2 del PSoC', 40, ROWY['J2'] - 3.2, 0.9)
    text(b, 'KitProg →' if False else '← KitProg (USB) por fuera', 14, (YTOP + YBOT) / 2, 0.9, just=-1)
    text(b, 'PSoC ' + ('boca abajo' if FLIP else 'componentes arriba'), 14, (YTOP + YBOT) / 2 + 2.2, 0.8, bold=False, just=-1)
    # silueta del PSoC (parte del kit sobre la tarjeta)
    xl, xr = X26 - 1.6, X26 + 25 * 2.54 + 1.6
    yt, yb = YTOP - 2.0, YBOT + 2.0
    for (x0, y0), (x1, y1) in [((xl, yt), (xr, yt)), ((xr, yt), (xr, yb)), ((xr, yb), (xl, yb))]:
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetStart(V(x0, y0)); s.SetEnd(V(x1, y1))
        s.SetLayer(pcbnew.F_SilkS); s.SetWidth(MM(0.15)); b.Add(s)
    filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
    pcbnew.SaveBoard(pcb, b)
    print('ok finish')

if __name__ == '__main__':
    if sys.argv[1] == 'place':
        place(json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), sys.argv[4])
    else:
        finish(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
