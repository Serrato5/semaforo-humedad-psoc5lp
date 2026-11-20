import sys
sys.path.insert(0, '.')
from diseno import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from matplotlib.backends.backend_pdf import PdfPages

LBL = {'+5V': '5V', 'SENS': 'SENS', 'AOUT': 'AOUT', 'U_SECO': 'U_SECO', 'U_HUM': 'U_HUM'}

def polys(g):
    if g.is_empty: return []
    return list(g.geoms) if hasattr(g, 'geoms') else [g]

def draw_poly(ax, g, fc, ec='none', lw=0, alpha=1, mirror=False, z=1):
    for p in polys(g):
        if p.geom_type != 'Polygon': continue
        if mirror: p = affinity.scale(p, -1, 1, origin=(W / 2, 0))
        ext = list(p.exterior.coords)
        ax.add_patch(MPoly(ext, closed=True, fc=fc, ec=ec, lw=lw, alpha=alpha, zorder=z))
        for h in p.interiors:
            ax.add_patch(MPoly(list(h.coords), closed=True, fc='white' if fc != 'none' else 'none', ec=ec, lw=lw, zorder=z + 0.1))

def frame(ax, title):
    ax.set_xlim(-2, W + 2); ax.set_ylim(H + 2, -2); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(MPoly([(0, 0), (W, 0), (W, H), (0, H)], closed=True, fc='none', ec='black', lw=1.2, zorder=5))
    ax.set_title(title, fontsize=10)

def holes(ax, mirror=False):
    for p in allpads:
        x = W - p['x'] if mirror else p['x']
        ax.add_patch(plt.Circle((x, p['y']), p['drill'] / 2, fc='white', ec='black', lw=0.3, zorder=6))

def top_view(ax, with_copper=True):
    frame(ax, 'Vista superior (lado de componentes)')
    if with_copper:
        draw_poly(ax, copper['GND'], '#f2d0b0', z=1)
        for n, g in copper.items():
            if n != 'GND': draw_poly(ax, g, '#e0a070', z=2)
    for c in comps:
        for o in c['outline']:
            xy = list(o.exterior.coords) if hasattr(o, 'exterior') else list(o.coords)
            ax.add_patch(MPoly(xy, closed=True, fc='none', ec='#1a3d8f', lw=0.9, zorder=7))
        for p in c['pads']:
            draw_poly(ax, pad_geom(p), '#c06020', z=3)
        lx, ly = c['lbl']
        ax.text(lx, ly, c['ref'], fontsize=5.5, color='#1a3d8f', ha='center', va='center', zorder=8, weight='bold')
    holes(ax)
    # marcas de polaridad
    ax.text(28.0, 7.4, 'K', fontsize=4, color='red', ha='center', zorder=9)    # D1 cátodo a 5V
    ax.text(38.16, 14.4, 'K', fontsize=4, color='red', ha='center', zorder=9)  # D2 cátodo a SENS
    ax.text(9.0, 4.2, '+', fontsize=6, color='red', ha='center', zorder=9)
    for y, *_ in rows:
        ax.text(49.0, y - 1.9, 'A', fontsize=4, color='red', ha='center', zorder=9)
    ax.text(59.9, 8.8, 'AOUT', fontsize=3.2, zorder=9)
    ax.text(59.9, 11.3, 'VCC', fontsize=3.2, zorder=9); ax.text(59.9, 13.9, 'GND', fontsize=3.2, zorder=9)
    for i, n in enumerate(J2nets):
        ax.text(7.7, J2y[i] + 0.35, n.replace('U_', '').replace('LED_', 'L'), fontsize=3.2, zorder=9)

def bottom_view(ax):
    frame(ax, 'Cobre inferior visto desde abajo (así queda al fresar)')
    draw_poly(ax, copper['GND'], '#d98c4a', mirror=True)
    for n, g in copper.items():
        if n != 'GND': draw_poly(ax, g, '#c06020', mirror=True, z=2)
    holes(ax, mirror=True)
    ax.plot([0], [H], 'r+', ms=12, mew=2, zorder=10); ax.text(0.5, H + 1.6, 'X0 Y0', color='red', fontsize=7, zorder=10)

if __name__ == '__main__':
    fig, axs = plt.subplots(1, 2, figsize=(14, 6.2))
    top_view(axs[0]); bottom_view(axs[1])
    plt.tight_layout(); plt.savefig('salidas/vista_previa.png', dpi=200)

    # PDF a escala 1:1 (A4) para imprimir y comprobar huellas
    with PdfPages('salidas/plantilla_1a1_A4.pdf') as pdf:
        for fn, title in [(lambda ax: top_view(ax, False), 'componentes'), (bottom_view, 'cobre')]:
            fig = plt.figure(figsize=(8.27, 11.69))
            mm = 1 / 25.4
            ax = fig.add_axes([20 * mm / 8.27, (11.69 - (H + 4) * mm - 25 * mm) / 11.69, (W + 4) * mm / 8.27, (H + 4) * mm / 11.69])
            fn(ax)
            fig.text(0.08, 0.96, 'Tarjeta de expansión — semáforo de humedad (PSoC 5LP). ESCALA 1:1: imprimir al 100 % (sin ajustar a página).', fontsize=8)
            fig.text(0.08, 0.94, f'Verificar: la placa debe medir {W:.0f} x {H:.0f} mm. Regla de control abajo = 50 mm.', fontsize=8)
            axr = fig.add_axes([20 * mm / 8.27, 0.45, 50 * mm / 8.27, 0.01]); axr.set_xlim(0, 50); axr.set_yticks([])
            axr.set_xticks(range(0, 51, 10)); axr.tick_params(labelsize=6)
            pdf.savefig(fig); plt.close(fig)
    print('ok')
