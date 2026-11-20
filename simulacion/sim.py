import numpy as np, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from matplotlib.ticker import FuncFormatter
CF=FuncFormatter(lambda v,p: ('%g'%round(v,2)).replace('.',','))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':22})
# --- 1) Transitorio: el sensor pasa de seco (2.68 V) a húmedo (2.09 V) y regresa
t=np.linspace(0,20,4001)
vs=np.interp(t,[0,3,9,12,17,20],[2.68,2.68,2.09,2.09,2.68,2.68])
rng=np.random.default_rng(1); vs=vs+rng.normal(0,0.002,len(t))
# filtro R1-C3 (tau=0.1 ms, despreciable aquí) y seguidor ideal
vbuf=vs.copy()
Us,Uh,hys=2.48,2.29,0.010
def comp(vp,vn):
    out=np.zeros(len(vp),bool); st=False
    for i,(a,b) in enumerate(zip(vp,vn)):
        if st and a<b-hys/2: st=False
        elif not st and a>b+hys/2: st=True
        out[i]=st
    return out
seco=comp(vbuf,np.full_like(vbuf,Us)); hum=comp(np.full_like(vbuf,Uh),vbuf); ama=~(seco|hum)
fig,ax=plt.subplots(2,1,figsize=(16,9),sharex=True,gridspec_kw={'height_ratios':[3,2]})
a=ax[0]; a.plot(t,vbuf,color='#1D2733',lw=3,label='Vbuf (P3[1])')
a.axhline(Us,color='#C0392B',ls='--',lw=2.5,label='Umbral seco 2,48 V')
a.axhline(Uh,color='#2E8B57',ls='--',lw=2.5,label='Umbral húmedo 2,29 V')
a.set_ylabel('Voltaje (V)'); a.set_ylim(1.95,2.95); a.legend(loc='upper center',fontsize=19,ncol=3,frameon=False); a.grid(alpha=.3)
for k,(sig,col,name) in enumerate([(seco,'#C0392B','LED rojo'),(ama,'#E0A100','LED amarillo'),(hum,'#2E8B57','LED verde')]):
    y=2-k; ax[1].fill_between(t,y,y+0.7*sig,step='mid',color=col); ax[1].text(-0.3,y+0.3,name,ha='right',va='center',fontsize=20)
ax[1].set_yticks([]); ax[1].set_xlabel('Tiempo (s)'); ax[1].set_xlim(0,20); ax[1].spines[['left','right','top']].set_visible(False)
ax[0].yaxis.set_major_formatter(CF); ax[1].xaxis.set_major_formatter(CF)
fig.tight_layout(); fig.savefig('sim_transitorio.png',dpi=110); plt.close()
# --- 2) Protección de entrada: Vin (0-12 V) -> nodo SENS, R1=1k, diodos a 5 V y GND
Vt=0.025852
def clamp(Vin,Is,N,Rs=0):
    f=lambda V:(Vin-V)/1000 - Is*(np.exp((V-5)/(N*Vt))-1) + Is*(np.exp(-V/(N*Vt))-1)
    return brentq(f,-2,13)
vin=np.linspace(-3,12,301)
v4007=[clamp(v,7.03e-9,1.808) for v in vin]; v5819=[clamp(v,3.17e-5,1.373) for v in vin]
fig,a=plt.subplots(figsize=(16,7))
a.plot(vin,vin,color='#9AA3AD',ls=':',lw=2.5,label='Sin protección')
a.plot(vin,v4007,color='#1D2733',lw=3.5,label='1N4007 (montado)')
a.plot(vin,v5819,color='#B5462B',lw=3.5,ls='--',label='1N5819 Schottky (v2)')
a.axhspan(0,5,color='#2E8B57',alpha=.08); a.text(-2.8,4.4,'Rango seguro de la PSoC (0 a 5 V)',fontsize=19,color='#2E7D57')
a.annotate(f'{v4007[-1]:.2f} V'.replace('.',','),(12,v4007[-1]),xytext=(9.6,7.2),fontsize=20,arrowprops=dict(arrowstyle='->'))
a.annotate(f'{v5819[-1]:.2f} V'.replace('.',','),(12,v5819[-1]),xytext=(9.6,3.0),fontsize=20,color='#B5462B',arrowprops=dict(arrowstyle='->',color='#B5462B'))
a.set_xlabel('Voltaje en el cable del sensor (V)'); a.set_ylabel('Voltaje que llega a P3[0] (V)')
a.set_ylim(-3,12.5); a.grid(alpha=.3); a.legend(loc='upper left',fontsize=19,frameon=False)
a.yaxis.set_major_formatter(CF); a.xaxis.set_major_formatter(CF)
fig.tight_layout(); fig.savefig('sim_proteccion.png',dpi=110); plt.close()
print('clamp12', round(v4007[-1],3), round(v5819[-1],3), 'clamp-3', round(v4007[0],3))
print('fc', 1/(2*np.pi*1e3*100e-9))
