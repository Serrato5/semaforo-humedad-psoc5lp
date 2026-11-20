#!/usr/bin/env python3
"""Genera BOM y CPL en el formato de JLCPCB a partir de spec.json y del archivo de posiciones de KiCad."""
import csv, json, sys, collections
spec, pos, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
parts = json.load(open(spec))['parts']
# rotaciones extra que JLCPCB necesita para algunas huellas de KiCad (se verifican en la vista previa de JLCPCB)
ROT = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
smd = [p for p in parts if not p.get('nobom') and not p['ref'].startswith('J')]
g = collections.OrderedDict()
for p in smd:
    g.setdefault((p['val'], p['fp'], p['lcsc']), []).append(p['ref'])
with open(f'{outdir}/BOM_JLCPCB.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (v, fp, l), refs in g.items():
        w.writerow([v, ','.join(sorted(refs, key=lambda r: (r.rstrip('0123456789'), int(''.join(c for c in r if c.isdigit()))))), fp.split(':')[1], l])
rows = list(csv.DictReader(open(pos)))
with open(f'{outdir}/CPL_JLCPCB.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    for r in rows:
        ref = r['Ref']; rot = (float(r['Rot']) + ROT.get(ref, ROT.get(r['Package'], 0))) % 360
        w.writerow([ref, f"{float(r['PosX']):.3f}mm", f"{float(r['PosY']):.3f}mm", 'Top' if r['Side'] == 'top' else 'Bottom', f'{rot:g}'])
print('BOM', len(g), 'líneas;', 'CPL', len(rows), 'componentes')
