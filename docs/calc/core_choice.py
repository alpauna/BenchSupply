#!/usr/bin/env python3
"""Pick the inductor core for the buck-boost channel.

The catch this handles that a naive AL calculation does not: powder cores lose
permeability under DC bias. Sizing turns from the datasheet AL gives an
inductor that is right at no load and badly low where it matters. So the turns
are solved AGAINST the biased permeability, and then checked against how many
turns physically fit in one layer.
"""
import math
MU0 = 4*math.pi*1e-7

# Operating point (docs/power-chain.md, low line + full load, 200 kHz)
L_TARGET = 34.6e-6      # H, wanted AT PEAK CURRENT
I_DC, I_PK = 7.23, 8.31
F_SW = 200e3
BUNDLE = 1.79           # mm, 10 x AWG25

# Kool Mu / sendust DC-bias roll-off, %initial permeability vs H in Oersted.
# From the vendor's DC bias curves - confirm against the datasheet for the
# exact part before winding.
BIAS = {
 60:  [(0,100),(10,95),(20,88),(30,80),(50,65),(80,50),(120,35),(200,22)],
 125: [(0,100),(10,88),(20,76),(30,66),(50,50),(80,35),(120,24),(200,15)],
}
def mu_frac(mu, H_oe):
    pts = BIAS[mu]
    if H_oe <= pts[0][0]: return 1.0
    for (h0,p0),(h1,p1) in zip(pts, pts[1:]):
        if H_oe <= h1:
            return (p0 + (p1-p0)*(H_oe-h0)/(h1-h0))/100
    return pts[-1][1]/100

def solve(OD, ID, H, mu):
    Ae = ((OD-ID)/2)*H; le = math.pi*(OD+ID)/2
    AL = MU0*mu*(Ae*1e-6)/(le*1e-3)
    N = math.sqrt(L_TARGET/AL)                 # unbiased starting guess
    for _ in range(60):                        # iterate: more turns -> more H
        H_oe = (N*I_PK/(le*1e-3))/79.577
        N = math.sqrt(L_TARGET/(AL*mu_frac(mu, H_oe)))
    H_oe = (N*I_PK/(le*1e-3))/79.577
    Nfit = math.pi*(ID-BUNDLE)/BUNDLE
    return dict(Ae=Ae, le=le, AL=AL*1e9, N=N, Nfit=Nfit, H=H_oe,
                frac=mu_frac(mu,H_oe), fits=N<=Nfit)

print(f"Target {L_TARGET*1e6:.1f} uH AT {I_PK} A peak, one layer, {F_SW/1e3:.0f} kHz\n")
print(f"{'core OD x ID x H':<22} {'mu':>4} {'AL':>7} {'mu left':>8} {'N':>6} {'fits':>6}   ")
cores = [("your green ones?", 24.5,15.8,12.7),
         ("~27 mm class",     26.9,14.7,11.2),
         ("~33 mm class",     33.0,19.7,11.4),
         ("~40 mm class",     40.6,23.7,15.2)]
best=None
for lab,OD,ID,Hh in cores:
    for mu in (60,125):
        r = solve(OD,ID,Hh,mu)
        mark = "YES" if r['fits'] else "no"
        print(f"{lab+' '+f'{OD:.0f}x{ID:.0f}x{Hh:.0f}':<22} {mu:>4} {r['AL']:>5.0f}nH"
              f" {r['frac']*100:>6.0f}% {r['N']:>5.0f} {mark:>6}")
        if r['fits'] and best is None: best=(lab,OD,ID,Hh,mu,r)
print()
lab,OD,ID,Hh,mu,r = best
print(f"=== Smallest that works: {lab}, {OD}x{ID}x{Hh}, mu {mu} ===")
print(f"  {r['N']:.0f} turns, {r['Nfit']:.0f} fit in one layer")
print(f"  H = {r['H']:.0f} Oe -> {r['frac']*100:.0f}% of initial mu at peak")
print(f"  wind {math.ceil(r['N'])+1} turns and measure - hand-wound never lands first time")
