#!/usr/bin/env python3
"""Pick the inductor core and its winding.

Two things here that a naive calculation gets wrong:

1. Powder cores lose permeability under DC bias. Size the turns from the
   datasheet AL and the inductor is right at no load and low where it matters.
   The turns are solved AGAINST the biased permeability, iterating, because
   more turns means more H means more roll-off.

2. Ae worked out from the outside dimensions is about 20% optimistic. The
   rounded edges that stop the core cutting the wire take real cross-section
   away. Measured against the Kool Mu catalogue for core 0254 below - use
   catalogue data whenever you have it.
"""
import math
MU0 = 4*math.pi*1e-7

# ---- the operating point (docs/power-chain.md) ------------------------------
L_TARGET = 41.5e-6          # H, wanted AT PEAK CURRENT, 200 kHz
I_DC, I_PK, DI = 6.02, 6.93, 1.81   # 60 V x 2.5 A, derated from 3.0
I_AC = DI/math.sqrt(12)
I_RMS = math.sqrt(I_DC**2 + I_AC**2)
RHO, DELTA = 1.72e-8, 0.148          # copper; skin depth in mm at 200 kHz

# Kool Mu DC-bias roll-off, % of initial permeability vs H in Oersted.
# Read off the vendor's DC bias curves - confirm for the exact part.
BIAS = {
 40:  [(0,100),(10,97),(20,92),(30,86),(50,74),(80,58),(120,42)],
 # 60u is anchored on the 0077083A7 datasheet: 80% at 39 Oe, 50% at 87 Oe,
 # both MINIMUMS, so a real core does better. The others are still estimates.
 60:  [(0,100),(20,90),(39,80),(60,66),(87,50),(120,38)],
 75:  [(0,100),(10,93),(20,85),(30,77),(50,61),(80,46),(120,32)],
 90:  [(0,100),(10,92),(20,82),(30,73),(50,57),(80,42),(120,29)],
 125: [(0,100),(10,88),(20,76),(30,66),(50,50),(80,35),(120,24)],
}
def mu_frac(mu, H_oe):
    pts = BIAS[mu]
    if H_oe <= 0: return 1.0
    for (h0,p0),(h1,p1) in zip(pts, pts[1:]):
        if H_oe <= h1: return (p0 + (p1-p0)*(H_oe-h0)/(h1-h0))/100
    return pts[-1][1]/100

def turns(AL_nH, le_mm, mu):
    """Solve N against the biased permeability."""
    N = math.sqrt(L_TARGET/(AL_nH*1e-9))
    for _ in range(80):
        H = (N*I_PK/(le_mm*1e-3))/79.577
        N = math.sqrt(L_TARGET/(AL_nH*1e-9*mu_frac(mu, H)))
    return N, (N*I_PK/(le_mm*1e-3))/79.577

# =============================================================================
# THE CHOSEN CORE - Magnetics Kool Mu toroid, core data 0254, from the
# catalogue page, not from the outside dimensions.
# =============================================================================
AL_0254 = {14:19, 19:26, 26:35, 40:54, 60:81, 75:101, 90:121, 125:168}  # nH/T^2
LE, AE, VE = 98.4, 107.0, 10600.0        # mm, mm^2, mm^3
OD, ID, HT = 40.77, 23.32, 15.37         # OD max, ID min, HT max

print("=== Geometry-derived Ae vs the catalogue, core 0254 ===")
Ae_est = ((OD-ID)/2)*HT
le_est = math.pi*(OD+ID)/2
print(f"  Ae  from dimensions {Ae_est:6.1f} mm^2   catalogue {AE:6.1f}"
      f"   {(AE/Ae_est-1)*100:+.0f}%")
print(f"  le  from dimensions {le_est:6.1f} mm     catalogue {LE:6.1f}"
      f"   {(LE/le_est-1)*100:+.0f}%")
print(f"  AL at 60u:  estimated {MU0*60*(Ae_est*1e-6)/(le_est*1e-3)*1e9:.0f} nH"
      f"   catalogue {AL_0254[60]} nH")
print("  The rounded edges cost 20% of Ae. That is turns, not a rounding error.")

print(f"\n=== Which permeability? (0254, {L_TARGET*1e6:.1f} uH at {I_PK} A) ===")
print(f"{'mu':>4} {'AL':>6} {'N':>4} {'H':>7} {'mu left':>8} {'dB':>7}"
      f" {'bundle max':>11} {'Cu':>7} {'P_cu':>7} {'Emax':>7}")
MLT = 54.3          # datasheet, winding length per turn at 20% fill
                    # (its 0% figure, 48.2, equals 2*(HT+(OD-ID)/2) exactly)
BUNDLE = 2.21                            # 3 x AWG18, twisted
for mu in (40, 60, 75, 90, 125):
    AL = AL_0254[mu]
    N, H = turns(AL, LE, mu)
    dB   = L_TARGET*DI/(N*AE*1e-6)       # T, peak-peak ripple flux density
    dmax = math.pi*ID/(N + math.pi)
    Lw   = N*(MLT + 2*BUNDLE)*1e-3
    R    = RHO*Lw/2.47e-6
    E    = (VE*1e-9)*1.0**2/(2*MU0*mu)
    print(f"{mu:>4} {AL:>5}n {N:>4.0f} {H:>5.1f}Oe {mu_frac(mu,H)*100:>7.0f}%"
          f" {dB*1e3:>5.1f}mT {dmax:>9.2f}mm {Lw:>6.2f}m {I_DC**2*R:>6.2f}W"
          f" {E*1e3:>5.0f}mJ")

print("""
  Note what did NOT decide this: DC bias. Every permeability lands at 80-85%,
  because higher mu needs fewer turns, which lowers H, which offsets the
  steeper roll-off curve. On a smaller core that trade goes the other way.

  What decides it is dB. Core loss scales roughly as dB^2.1 and Kool Mu's
  loss coefficient rises with permeability too, so the copper that 125u saves
  is paid back several times over in the core. Lower mu, lower dB, less loss.
  Check the vendor's loss curves for magnitude; the direction is not in doubt.

  => 0254 at 60u, 24 turns.""")

# =============================================================================
# The winding
# =============================================================================
print("\n=== Wire, for 24 turns on 0254 ===")
N60 = 24
d_max = math.pi*ID/(N60 + math.pi)
print(f"  I_rms {I_RMS:.2f} A ({I_DC:.2f} DC + {I_AC:.2f} AC)")
print(f"  fattest bundle that still gives {N60} turns in one layer:"
      f" {d_max:.2f} mm\n")

AWG = {14:(1.628,2.081), 16:(1.291,1.309), 18:(1.024,0.823),
       20:(0.812,0.518), 22:(0.644,0.326), 25:(0.455,0.162)}
print(f"{'winding':<14} {'Cu mm2':>7} {'bundle':>8} {'DCR':>8} {'P_dc':>7}"
      f" {'P_ac':>7} {'J':>6} {'fits':>6}")
for n, g in ((10,25),(5,20),(3,18),(2,16),(1,14)):
    ds, As = AWG[g]
    A   = n*As
    d   = 2*math.sqrt(A/0.75/math.pi)*1.08
    mlt = (MLT + 2*d)*1e-3
    R   = RHO*mlt*N60/(A*1e-6)
    rac = max(1.0, ds/(4*DELTA) + 0.25)
    print(f"{f'{n} x AWG{g}':<14} {A:>6.2f} {d:>6.2f}mm {R*1e3:>6.1f}mR"
          f" {I_DC**2*R:>6.2f}W {I_AC**2*R*rac*1e3:>5.0f}mW"
          f" {I_RMS/A:>5.1f} {'yes' if d<=d_max else 'NO':>6}")
# ---- core loss, from the datasheet's own figure ---------------------------
P100, B_REF, F_REF = 750.0, 100.0, 100e3     # mW/cm3 max at 100 kHz, 100 mT
def core_loss(dB_mT, f, Ve_mm3):
    return P100*((dB_mT/2)/B_REF)**2.1*(f/F_REF)**1.4 * Ve_mm3/1000 / 1000
dB60 = L_TARGET*DI/(24*AE*1e-6)*1e3
print(f"\n=== Core loss at 60u, 24 turns ===")
print(f"  datasheet {P100:.0f} mW/cm3 max at 100 kHz / 100 mT")
print(f"  ours: {dB60/2:.2f} mT peak at 200 kHz -> {core_loss(dB60, 200e3, VE):.2f} W")
Rw = RHO*(MLT*1e-3)*24/2.47e-6
print(f"  plus {I_DC**2*Rw:.2f} W copper = {I_DC**2*Rw + core_loss(dB60,200e3,VE):.2f} W total")

print("""
  P_ac is milliwatts everywhere, even solid AWG14 - the AC is 9% of the
  current, so skin effect is not what sizes this wire. Strand it because
  2.5 mm^2 of solid copper will not bend round the hole twenty-four times.

  => 3 x AWG18 twisted, grade 2 heavy build, Class 180 (H).
     Cut ~1.3 m per strand. Wind 25 turns, measure, remove one if it reads
     high - and do not pot it until it measures right.""")
