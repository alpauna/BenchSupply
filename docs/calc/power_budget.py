#!/usr/bin/env python3
"""Reproduces every number in docs/power-chain.md.

Nothing here is measured. It is all arithmetic from the ST-1228-T350Q
datasheet and the channel requirement, and it exists so the numbers in the
document can be checked rather than believed.
"""

# ---- the transformer, from PI_ST-1228-T350Q_200728.pdf ----------------------
VA        = 350.0     # nameplate
I_SEC     = 12.5      # A, nameplate
V_SEC     = VA / I_SEC
REG       = 0.05      # winding regulation, 350 VA toroid. 5-7% is the range.
V_DIODE   = 0.7
MASS      = 2.90      # kg
DIMS      = (113, 117, 70)   # mm

# ---- what the bench supply has to be ---------------------------------------
CH        = 2
V_MAX     = 60.0
I_MAX     = 3.0      # the current cap
P_MAX     = 150.0    # W per channel - the REAL limit. See the envelope below.
V_MIN     = 2.0

# ---- derating --------------------------------------------------------------
# A capacitor-input filter draws short, tall current pulses, so the RMS the
# winding sees is much larger than the DC it delivers. 0.62 is the usual
# figure for a full-wave cap-input rectifier; 0.70 is optimistic.
CAP_INPUT = 0.62
ETA_CONV  = 0.85      # buck-boost, at this power
ETA_XFMR  = 0.92

def rail(line=1.00, loaded=False):
    """DC off the bridge into the filter cap."""
    sag = 0.82 if loaded else 1.0          # winding drop at ~full secondary A
    return V_SEC * (1 + REG) * line * sag * 1.4142 - 2 * V_DIODE

def rule(t): print(f"\n=== {t} ===")

print(f"ST-1228-T350Q: {VA:.0f} VA / {I_SEC} A -> secondary {V_SEC:.0f} VAC"
      f", {MASS} kg, {DIMS[0]}x{DIMS[1]}x{DIMS[2]} mm")

rule("1. The raw rail, and why 60 V needs a boost")
worst = None
for lab, line, ld in (("132 V, no load", 1.10, False),
                      ("120 V, no load", 1.00, False),
                      ("120 V, loaded",  1.00, True),
                      ("108 V, loaded",  0.90, True)):
    v = rail(line, ld)
    ratio = V_MAX / v
    worst = ratio if worst is None else max(worst, ratio)
    print(f"  {lab:<16} {v:5.1f} V   60 V needs {ratio:.2f}x")
print(f"  Design case is the LAST row - low line AND loaded is the lowest the")
print(f"  rail ever gets, so the converter has to make {worst:.2f}x there.")
print("  Buck and linear topologies cannot step up at all. Boost capability")
print("  is a requirement, not a preference.")

rule("2. Usable DC power")
dc = VA * CAP_INPUT
print(f"  {VA:.0f} VA x {CAP_INPUT:.2f} = {dc:.0f} W DC usable per transformer")
print(f"  (350 VA is NOT 350 W. The rectifier takes the difference.)")

rule("3. One channel, or two, per transformer")
out_ch  = P_MAX
need_ch = out_ch / ETA_CONV
print(f"  one channel at {P_MAX:.0f} W out")
print(f"    -> {need_ch:.0f} W DC in -> {need_ch/CAP_INPUT:.0f} VA of transformer")
print(f"    against {dc:.0f} W available: margin {dc - need_ch:+.0f} W  "
      f"({'fits' if need_ch < dc else 'SHORT'})")
out_tot = out_ch * CH
need_tot = out_tot / ETA_CONV
print(f"  both channels = {out_tot:.0f} W out -> {need_tot/CAP_INPUT:.0f} VA needed")
print(f"    one 350 VA transformer is {350/(need_tot/CAP_INPUT)*100:.0f}% of that.")
print(f"  => ONE TRANSFORMER PER CHANNEL.")

rule("4. Isolation")
print("  The datasheet gives one secondary: 'Output wire Gray AWG#14', 28 VAC,")
print("  no centre tap. Rectifying one winding twice does not isolate anything")
print("  - both outputs still share the winding.")
print("  Two transformers put the barrier in the iron, so the converters do not")
print("  have to carry it: two NON-isolated buck-boosts, each output floating,")
print("  series-connectable for +/-60 V. That is the whole reason to buy the")
print("  second transformer rather than design two flybacks.")

rule("5. The 2 V end - why the pre-regulator has to track")
for label, src in (("fixed 40 V rail", rail()), ("tracking, +3 V above out", V_MIN + 3)):
    burn = (src - V_MIN) * I_MAX
    print(f"  {label:<26} drops {src - V_MIN:5.1f} V at {I_MAX} A"
          f" = {burn:6.1f} W to deliver {V_MIN*I_MAX:.0f} W")
print("  A fixed rail is not a thermal design, it is a heater.")

rule("6. Heat in the box, both channels at full")
conv = out_tot/ETA_CONV - out_tot
xfmr = (out_tot/ETA_CONV)/ETA_XFMR - out_tot/ETA_CONV
print(f"  converters {conv:.0f} W + transformers {xfmr:.0f} W = {conv+xfmr:.0f} W")
print(f"  mains draw: {CH} x {VA:.0f} VA / 120 V = {CH*VA/120:.1f} A")
print(f"  mass of iron alone: {CH*MASS:.1f} kg")
print("  The existing enclosure has one 40 mm fan, sized to blow over a single")
print("  cool switching supply. It is not the right box for this.")


rule("7. The envelope - it is power limited, not current limited")
avail = dc*ETA_CONV
print(f"  absolute ceiling: {dc:.0f} W DC x {ETA_CONV} = {avail:.0f} W out")
print(f"  specified at {P_MAX:.0f} W, which leaves {(VA*CAP_INPUT - P_MAX/ETA_CONV):.0f} W of DC headroom\n")
print(f"{'Vout':>7} {'I':>8} {'power':>8}")
for v in (12, 24, 40, 50, 55, 60):
    i = min(I_MAX, P_MAX/v)
    print(f"{v:>5} V {i:>6.2f} A {v*i:>6.0f} W"
          f"   {'full 3 A' if i >= I_MAX else 'power limited'}")
print(f"  corner point: {I_MAX} A up to {P_MAX/I_MAX:.0f} V, tapering to"
      f" {P_MAX/V_MAX:.1f} A at {V_MAX:.0f} V")
print("""
  A flat current derate would have thrown the bottom of the range away: the
  transformer does not care about amps, it cares about watts. 3 A at 12 V is
  36 W and nothing to it.

  The inductor is sized by the WORST case, which is boost at low line and full
  power - 6.02 A - not by the current cap. In buck mode the inductor carries
  the OUTPUT current, so 3 A there is well under it. One design covers the
  whole envelope.""")
