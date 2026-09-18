#!/usr/bin/env python3
"""Floor thickness under two toroidal transformers.

The load is small and the stress was never the problem. Deflection is - a
floor that sags makes the box rock on its feet and puts the lid seat out of
plane - and creep makes whatever it sags settle in permanently.

Plate theory, simply supported on four edges (the walls), uniformly loaded.
Roark's coefficients for b/a ~ 1.2.
"""
E_PETG = 2000.0      # MPa. Printed PETG runs 1500-2100; see the sweep below.
NU     = 0.40
ALPHA, BETA = 0.0042, 0.487      # deflection and stress coefficients, b/a~1.2

MASS   = 2.90 * 2                # kg, two toroids
A, B   = 237.0, 279.0            # mm, interior span, short x long
q      = MASS*9.81/(A*B)         # N/mm^2, spread over the floor

print(f"Two toroids = {MASS:.1f} kg over a {A:.0f} x {B:.0f} mm floor")
print(f"  distributed load q = {q*1e3:.2f} kPa - which is nothing\n")
print(f"{'t':>4} {'D':>10} {'deflection':>12} {'stress':>9}")
for t in (3.0, 4.0, 5.0, 6.0, 8.0):
    D = E_PETG*t**3/(12*(1-NU**2))
    d = ALPHA*q*A**4/D
    s = BETA*q*A**2/t**2
    print(f"{t:>3.0f}mm {D:>9.0f} {d:>10.2f} mm {s:>7.2f} MPa")

print(f"""
  Stress was never the issue: PETG yields around 50 MPa and even 3 mm only
  sees {BETA*q*A**2/9:.1f}. Deflection is. At 3 mm the floor bows {ALPHA*q*A**4/(E_PETG*27/(12*(1-NU**2))):.1f} mm under its
  own occupants, which a box standing on four rubber feet will rock on.

  Doubling to 6 mm is 8x the stiffness (t^3) and a quarter of the stress
  (1/t^2): {ALPHA*q*A**4/(E_PETG*216/(12*(1-NU**2))):.2f} mm, which is nothing.""")

print("\n  Sensitivity to the modulus, since printed PETG is not a datasheet:")
for E in (1500, 2000, 2100):
    D3 = E*27/(12*(1-NU**2)); D6 = E*216/(12*(1-NU**2))
    print(f"    E = {E} MPa:  3 mm -> {ALPHA*q*A**4/D3:.2f} mm,"
          f"  6 mm -> {ALPHA*q*A**4/D6:.2f} mm")

print("""
  And what 6 mm does NOT fix: creep, and the bolt. Thickness slows creep, it
  does not stop it, and a box holding ~100 W runs warm, which speeds it up.
  Each toroid still hangs off ONE central bolt, and a bolt in plastic is a
  bearing problem, not a bending one. Put a steel spreader under the floor.""")

area = 279*237
for t_add in (3.0,):
    v = area*t_add/1000
    print(f"\n  Cost: {t_add:.0f} mm more floor = {v:.0f} cm^3 of envelope,"
          f" maybe {v*1.27*0.5:.0f}-{v*1.27:.0f} g depending on infill.")
