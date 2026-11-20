#!/usr/bin/env python3
"""Genera el esquemático KiCad (.kicad_sch) del Proyecto 5 a partir de una lista de componentes y redes.
Cada pin sale con un tramo de cable corto y una etiqueta de red (estilo 'netlabel'), sin cruces."""
import re, uuid, json, sys, os
LIB = os.environ.get('KLIB', os.path.expanduser('~/squashfs-root/share/kicad/symbols'))
OUT = sys.argv[1]
U = lambda: str(uuid.uuid4())
ROOT = U()

def block(text, start):
    d = 0
    for i in range(start, len(text)):
        if text[i] == '(':
            d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                return text[start:i+1]
    raise ValueError
_cache = {}
def libsym(libid):
    lib, name = libid.split(':')
    if libid in _cache: return _cache[libid]
    t = open(f'{LIB}/{lib}.kicad_sym').read()
    m = re.search(r'\n\t\(symbol "%s"\n' % re.escape(name), t)
    b = block(t, m.start() + 2)
    ext = re.search(r'\(extends "([^"]+)"\)', b)
    if ext:
        raise SystemExit(f'{libid} usa extends {ext.group(1)}')
    pins = {}
    for pm in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)\s*\(length ([-\d.]+)\)', b):
        tail = b[pm.end():pm.end()+600]
        num = re.search(r'\(number "([^"]+)"', tail).group(1)
        pins[num] = (float(pm.group(3)), float(pm.group(4)), int(float(pm.group(5))), pm.group(1))
    full = b.replace(f'(symbol "{name}"', f'(symbol "{libid}"', 1)
    _cache[libid] = (full, pins)
    return _cache[libid]

DIRS = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}   # dirección del pin hacia el cuerpo, en coordenadas de hoja
def fmt(v): return f'{v:.2f}'.rstrip('0').rstrip('.')

def build(parts, title):
    items = []; used = []
    for p in parts:
        full, pins = libsym(p['lib'])
        if p['lib'] not in used: used.append(p['lib'])
        X, Y = p['at']
        props = [('Reference', p['ref']), ('Value', p['val']), ('Footprint', p.get('fp', '')), ('Datasheet', ''), ('Description', p.get('desc', ''))]
        if p.get('lcsc'): props.append(('LCSC', p['lcsc']))
        pr = ''
        for i, (k, v) in enumerate(props):
            hide = ' (hide yes)' if k not in ('Reference', 'Value') else ''
            off = {'Reference': (2.54, -1.5), 'Value': (2.54, 1.5)}.get(k, (0, 0))
            pr += f'\n\t\t(property "{k}" "{v}" (at {fmt(X+off[0])} {fmt(Y+off[1])} 0) (effects (font (size 1.27 1.27)) (justify left){hide}))'
        pinl = ''.join(f'\n\t\t(pin "{n}" (uuid "{U()}"))' for n in pins)
        inb = 'no' if p.get('nobom') else 'yes'
        items.append(f'\t(symbol (lib_id "{p["lib"]}") (at {fmt(X)} {fmt(Y)} 0) (unit 1) (exclude_from_sim no) (in_bom {inb}) (on_board yes) (dnp no) (uuid "{p["uuid"]}"){pr}{pinl}\n\t\t(instances (project "semaforo_p5" (path "/{ROOT}" (reference "{p["ref"]}") (unit 1)))))')
        for num, (px, py, ang, typ) in pins.items():
            ax, ay = X + px, Y - py
            net = p['nets'].get(num)
            dx, dy = DIRS[ang]
            if net is None:
                items.append(f'\t(no_connect (at {fmt(ax)} {fmt(ay)}) (uuid "{U()}"))')
                continue
            L = 2.54
            ex, ey = ax - dx*L, ay - dy*L
            items.append(f'\t(wire (pts (xy {fmt(ax)} {fmt(ay)}) (xy {fmt(ex)} {fmt(ey)})) (stroke (width 0) (type default)) (uuid "{U()}"))')
            if (-dx, -dy) == (-1, 0): ang_l, just = 180, 'right bottom'
            elif (-dx, -dy) == (1, 0): ang_l, just = 0, 'left bottom'
            elif (-dx, -dy) == (0, -1): ang_l, just = 90, 'left bottom'
            else: ang_l, just = 270, 'right bottom'
            items.append(f'\t(label "{net}" (at {fmt(ex)} {fmt(ey)} {ang_l}) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just})) (uuid "{U()}"))')
    for t in TEXTS:
        items.append(f'\t(text "{t[2]}" (exclude_from_sim no) (at {t[0]} {t[1]} 0) (effects (font (size {t[3]} {t[3]}) (bold yes)) (justify left bottom)) (uuid "{U()}"))')
    libs = '\n'.join('\t\t' + _cache[l][0].replace('\n', '\n\t') for l in used)
    return f'''(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")
\t(uuid "{ROOT}")
\t(paper "A3")
\t(title_block (title "{title}") (date "2026-11-19") (rev "P5-v1") (company "Universidad Surcolombiana - Electrónica Análoga 3")
\t\t(comment 1 "Semáforo de humedad: tarjeta de expansión SMD para CY8CKIT-059")
\t\t(comment 2 "Equipo: Serrato, Velásquez, Ramírez, Morales, Valderrama"))
\t(lib_symbols
{libs}
\t)
{chr(10).join(items)}
\t(sheet_instances (path "/" (page "1")))
)
'''

spec = json.load(open(sys.argv[2]))
TEXTS = spec.get('texts', [])
for p in spec['parts']:
    p.setdefault('uuid', U())
open(OUT, 'w').write(build(spec['parts'], spec['title']))
json.dump({'root': ROOT, 'uuids': {p['ref']: p['uuid'] for p in spec['parts']}}, open(OUT + '.ids.json', 'w'))
print('ok', len(spec['parts']), 'componentes')
