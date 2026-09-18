#!/usr/bin/env python3
"""Hand-wound toroidal inductor for the buck-boost channel.

Core on hand: OD 24.5, ID 15.8, H 12.7 mm, rounded edges, two off.
MATERIAL UNKNOWN - and that is the number that decides whether this works.
Everything above the material fork is pure geometry and is settled.
"""
import math

OD, ID, H = 24.5, 15.8, 12.7          # mm, measured
MU0 = 4*math.pi*1e-7

# ---- geometry (material-independent) ---------------------------------------
Ae = ((OD - ID)/2) * H                # mm^2, core cross-section
le = math.pi * (OD + ID)/2            # mm, mean magnetic path
Ve = Ae * le                          # mm^3
Aw = math.pi * (ID/2)**2              # mm^2, winding window (the hole)
MLT = 2*(H + (OD-ID)/2)               # mm, mean length per turn

print("=== Core geometry ===")
print(f"  Ae  {Ae:6.1f} mm^2      cross-section")
print(f"  le  {le:6.1f} mm        mean magnetic path")
print(f"  Ve  {Ve:6.0f} mm^3 = {Ve/1000:.2f} cm^3")
print(f"  Aw  {Aw:6.1f} mm^2      the hole, before any wire goes in it")
print(f"  MLT {MLT:6.1f} mm        mean length per turn")
print("  (rounded edges take a few % off Ae - treat these as optimistic)")

# ---- the operating point, from power_budget.py -----------------------------
VIN, VOUT, IOUT, ETA = 29.3, 60.0, 2.5, 0.85   # low line, loaded: the worst case
PIN  = VOUT*IOUT/ETA
IL   = PIN/VIN                        # boost mode: inductor carries input current
D    = 1 - VIN/VOUT
print(f"\n=== Operating point (boost mode, low line, full load) ===")
print(f"  Vin {VIN} V -> Vout {VOUT} V at {IOUT} A,  D = {D:.3f}")
print(f"  inductor DC current = {IL:.2f} A")

def design(f_khz, ripple=0.30):
    f = f_khz*1e3
    dI = ripple*IL
    L  = VIN*D/(f*dI)
    Ipk= IL + dI/2
    E  = 0.5*L*Ipk**2
    return L, dI, Ipk, E

print(f"\n{'fsw':>7} {'L needed':>10} {'dI':>7} {'Ipk':>7} {'energy':>9}")
for f in (100, 150, 200, 300):
    L, dI, Ipk, E = design(f)
    print(f"{f:>5}kHz {L*1e6:>8.1f}uH {dI:>6.2f}A {Ipk:>6.2f}A {E*1e3:>7.2f}mJ")

# ---- the material fork -----------------------------------------------------
print("\n=== What the core has to be ===")
print("Energy a core can hold before it saturates ~ Ve*Bsat^2/(2*mu0*mu_r).")
print("Target: the 100 kHz case above.\n")
L, dI, Ipk, E = design(100)
print(f"{'material':<22} {'mu':>5} {'Bsat':>6} {'AL':>9} {'E max':>9} {'N for L':>8}   verdict")
for name, mu, bsat, note in (
    ("Ferrite (EMI choke)",  2000, 0.40, "ungapped"),
    ("Iron powder -26",        75, 1.38, "lossy >50kHz"),
    ("Sendust / Kool Mu 60",   60, 1.00, "good"),
    ("Sendust / Kool Mu 125", 125, 1.00, "good"),
    ("MPP 60",                 60, 0.75, "good, pricey"),
):
    AL   = MU0*mu*(Ae*1e-6)/(le*1e-3)          # H per turn^2
    Emax = (Ve*1e-9)*bsat**2/(2*MU0*mu)
    N    = math.sqrt(L/AL)
    ok   = "USABLE" if Emax > E*1.5 else "SATURATES - unusable"
    print(f"{name:<22} {mu:>5} {bsat:>5.2f}T {AL*1e9:>7.1f}nH {Emax*1e3:>7.2f}mJ"
          f" {N:>7.1f}   {ok}  {note}")

# ---- can the winding physically fit? ---------------------------------------
print("\n=== Winding fit: multi-strand, and the inner circumference limit ===")
SKIN = lambda f: 66.1/math.sqrt(f)      # mm, copper at 20C, f in Hz
AWG = {24:0.511, 25:0.455, 26:0.405, 27:0.361, 28:0.321, 29:0.286, 30:0.255, 31:0.227}
for f in (100e3, 200e3):
    d = SKIN(f)
    biggest = max((g for g,dia in AWG.items() if dia <= 2*d), default=None,
                  key=lambda g: AWG[g])
    print(f"  skin depth at {f/1e3:>3.0f} kHz = {d:.3f} mm -> strand no fatter than"
          f" {2*d:.2f} mm  = AWG {biggest} ({AWG[biggest]} mm)")
# Skin depth only bites the AC part. The DC sees plain DCR and does not care
# how thick the strand is - so sizing every strand to the skin depth is the
# wrong instinct here. Check how much current is actually AC:
dI = design(200)[1]
Iac = dI/math.sqrt(12)                   # triangular ripple, RMS
print(f"\n  ripple {dI:.2f} A p-p = {Iac:.2f} A RMS of AC, against {IL:.2f} A DC")
print(f"  AC is {Iac/IL*100:.0f}% of the DC. Skin and proximity effects act on")
print( "  that fraction only, so full litz is not worth winding by hand.")
print( "  Use several strands because 1.6 mm^2 of solid wire will not bend")
print( "  round a 15.8 mm hole - which is the reason that actually matters.")

J = 4.5                                  # A/mm^2, hand-wound in still air
Acu = IL/J
print(f"\n  {IL:.2f} A at {J} A/mm^2 -> {Acu:.2f} mm^2 of copper needed")
AWG25 = 0.162
n = math.ceil(Acu/AWG25)
bundle = math.sqrt(n*AWG25/0.75)*2/math.sqrt(math.pi)*1.08   # +8% enamel
print(f"  = {n} strands of AWG25 ({AWG25} mm^2 each) -> bundle ~{bundle:.2f} mm dia")
print(f"\n  A toroid's turn count is limited by its INNER circumference:")
print(f"{'fsw':>7} {'N needed':>9} {'N fits (1 layer)':>17}   verdict")
for fk in (100, 150, 200, 300):
    Lf = design(fk)[0]
    AL = MU0*60*(Ae*1e-6)/(le*1e-3)
    N  = math.sqrt(Lf/AL)
    Nmax = math.pi*(ID - bundle)/bundle
    v = "fits one layer" if N <= Nmax else f"needs 2 layers"
    print(f"{fk:>5}kHz {N:>8.1f} {Nmax:>16.1f}   {v}")
print("\n  (N for Kool Mu 60. A 125-mu core needs 1/sqrt(2) as many turns.)")

# ---- DC bias ---------------------------------------------------------------
print("\n=== DC bias rolls the permeability off ===")
AL = MU0*60*(Ae*1e-6)/(le*1e-3)
N  = math.sqrt(design(100)[0]/AL)
Hpk = N*design(100)[2]/(le*1e-3)
print(f"  {N:.0f} turns at {design(100)[2]:.2f} A peak -> H = {Hpk:.0f} A/m"
      f" = {Hpk/79.577:.0f} Oe")
print("  Kool Mu 60 holds roughly 60-70% of initial mu at that H, so the")
print("  inductance SAGS to ~0.65x at peak current and the ripple grows.")
print("  Design the turns for the biased value, not the datasheet AL.")

# ---- copper loss -----------------------------------------------------------
RHO = 1.72e-8
print("\n=== Copper loss (Kool Mu 60, one layer, 200 kHz) ===")
AL = MU0*60*(Ae*1e-6)/(le*1e-3)
L200 = design(200)[0]
N200 = math.sqrt(L200/AL)
mlt  = (MLT + 4)*1e-3                     # + wire buildup
R    = RHO*mlt*N200/(Acu*1e-6)
print(f"  {N200:.0f} turns x {mlt*1e3:.0f} mm = {N200*mlt:.2f} m of {Acu:.2f} mm^2")
print(f"  DCR ~ {R*1e3:.1f} mOhm -> I^2R = {IL**2*R:.2f} W at {IL:.2f} A")
print(f"  call it {IL**2*R*1.6:.2f} W with proximity effect in a wound bundle.")
print("  Core loss is on top of that and needs the material to compute.")
