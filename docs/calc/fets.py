#!/usr/bin/env python3
"""The four switches for the LT8705, one channel.

Sized from the operating points rather than picked from a catalogue. The
non-obvious results: switch A carries the most current and does no switching,
and at 60 V the switching loss beats the conduction loss - so the target is
moderate Rds(on) with LOW gate charge, not the lowest Rds available.
"""
VIN_LO, VIN_HI, VOUT = 29.3, 44.3, 60.0
IL, IPK, F = 6.02, 6.93, 200e3
D = 1 - VIN_LO/VOUT
R, VGS = 0.025, 6.35
TA, TJMAX = 45.0, 150.0

def rule(t): print(f"\n=== {t} ===")

rule("1. Voltage: the two sides stand off different rails")
print("  A/B (buck side) stand off Vin, C/D (boost side) stand off Vout")
for lab, v in (("buck A/B, Vin max", VIN_HI), ("boost C/D, Vout max", VOUT)):
    print(f"  {lab:<24} {v:>5.1f} V -> x1.4 for ringing = {v*1.4:>5.1f} V")
print("  => 100 V throughout. One part number for all four; 1.67x on the")
print("     boost side, which is standard rather than generous.")

rule("2. Current: switch A is the worst case, and it is not obvious")
print(f"  boost mode, D = {D:.3f}")
print(f"    A (buck HS)  ON CONTINUOUSLY   {IL:>5.2f} A  - no switching at all")
print(f"    C (boost LS) conducts D        {IL*D**0.5:>5.2f} A rms")
print(f"    D (boost HS) conducts 1-D      {IL*(1-D)**0.5:>5.2f} A rms")
print("  A carries the most and switches least; C and D carry less and take")
print("  all the switching loss.")

rule("3. At 60 V, switching beats conduction")
print(f"{'Rds':>7} {'A conducts':>12}    {'t_sw':>6} {'C+D switching':>15}")
for r in (0.010, 0.025, 0.050):
    print(f"{r*1000:>5.0f}m {IL**2*r:>11.2f}W", end="")
    print("" if r != 0.010 else f"    {15:>4} ns {0.5*VOUT*IL*15e-9*2*F:>14.2f}W")
for t in (15e-9, 20e-9, 30e-9, 40e-9):
    print(f"{'':>19}    {t*1e9:>4.0f} ns {0.5*VOUT*IL*t*2*F:>14.2f}W")
print("  Switching scales with TIME, not with Rds. A 10 mOhm part carrying")
print("  150 nC of gate charge loses to a 25 mOhm part carrying 40.")
print("  => target 20-30 mOhm and Qg under ~50 nC.")

rule("4. Gate charge is a hard ceiling")
for qg in (30e-9, 50e-9, 100e-9, 150e-9):
    i = 4*qg*F
    print(f"  Qg {qg*1e9:>3.0f} nC x 4 FETs at {F/1e3:.0f} kHz -> {i*1000:>5.1f} mA"
          f" and {4*qg*VGS*F:>4.2f} W from INTVCC"
          f"   {'ok' if i < 0.06 else 'check the INTVCC limit, or feed EXTVCC'}")
print("  The LT8705 has an EXTVCC pin: supply the gate drive externally and")
print("  the internal regulator stops being the constraint.")

rule("5. Loss per switch, and whether it needs a heatsink")
for t in (15e-9, 30e-9):
    esw = 0.5*VOUT*IL*t*2*F/2
    a, c, d = IL**2*R, (IL*D**0.5)**2*R + esw, (IL*(1-D)**0.5)**2*R + esw
    print(f"  t_sw {t*1e9:>2.0f} ns:  A {a:.2f} W   C {c:.2f} W   D {d:.2f} W"
          f"   B ~0   total {a+c+d:.2f} W/channel")
print(f"\n  ambient in the box ~{TA:.0f} C, Tj max {TJMAX:.0f} C"
      f" -> {TJMAX-TA:.0f} C of budget")
print(f"{'package / mounting':<34} {'theta':>8} {'rise at 1.5 W':>14} {'Tj':>7}")
for lab, th in (("DPAK, 1 in2 of copper", 40), ("D2PAK, good copper", 25),
                ("TO-220, small clip heatsink", 20), ("TO-220, shared heatsink", 8)):
    print(f"  {lab:<32} {th:>5.0f} C/W {1.5*th:>12.0f} C {TA+1.5*th:>6.0f} C")
print("""
  A shared TO-220 heatsink is the easy answer for a hand build - and it is
  the heatsink the 1-Wire probe clamps to, which is why that sensor leads
  everything else in the box.

  All four tabs sit at DIFFERENT potentials, so each needs its own insulator
  on a shared sink. That is why the sink floats at a channel potential, and
  why the temperature probe has to be electrically isolated.""")
