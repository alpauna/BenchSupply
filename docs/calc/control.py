#!/usr/bin/env python3
"""Setpoint divider, the optocoupler barrier, and the fan staging.

The regulator closes its own loop in hardware. The Pico only moves the
feedback divider, and everything here is about doing that across an isolation
barrier without giving the barrier away or commanding full output when the
firmware is not running.
"""
import math

# ---- the divider -----------------------------------------------------------
VMIN, VMAX, VREF, RTOP = 2.0, 60.0, 0.8, 74e3
Gmin, Gmax = (VMIN/VREF-1)/RTOP, (VMAX/VREF-1)/RTOP
print("=== Setpoint divider: Vout = Vref*(1 + Rtop*G) ===")
print(f"  Vref {VREF} V, Rtop {RTOP/1e3:.0f}k")
print(f"  Rbot {1/Gmax/1e3:.2f}k at {VMAX} V  ...  {1/Gmin/1e3:.2f}k at {VMIN} V")
print(f"  conductance {Gmax*1e6:.0f} uS ... {Gmin*1e6:.1f} uS")
print("  Vout is LINEAR in bottom-leg conductance, so binary-weighted parallel")
print("  resistors give uniform voltage steps - no lookup table.\n")
print(f"{'bits':>5} {'step':>9} {'branches':>9}")
for n in (8, 10, 12):
    print(f"{n:>5} {(VMAX-VMIN)/(2**n-1):>7.3f} V {n:>9}")

print("\n  Switch the BOTTOM leg only: the top leg sits at Vout and no analog")
print("  switch wants 60 V across it. Ron is in series with each branch, so it")
print("  hurts most where the branch is smallest - the high-voltage end:")
for ron in (5, 50, 100):
    print(f"    Ron {ron:>3} ohm -> {ron/(1/Gmax)*100:5.2f}% at {VMAX} V,"
          f" {ron/(1/Gmin)*100:5.2f}% at {VMIN} V")

print("""
=== Fail-safe direction ===
  Switches OPEN must mean MINIMUM output. Size the FIXED branch for 2 V and
  let the switches ADD conductance to climb. Then a Pico that is unpowered,
  in reset, or mid-reflash leaves 2 V on the terminals.
  Wire it the other way and a dead Pico commands 60 V into whatever is
  plugged in, with 8 A of inductor behind it.""")

# ---- the barrier -----------------------------------------------------------
BITS, CH = 10, 2
print(f"\n=== The optocoupler barrier ===")
print(f"  {BITS} bits x {CH} channels = {BITS*CH} switch lines.")
print(f"  One opto per line = {BITS*CH} optos, {BITS*CH} LED resistors,"
      f" {BITS*CH} pull-ups = {BITS*CH*3} parts.")
print(f"  SERIALISE instead: a shift register on the isolated side, and only")
print(f"  CLK + DATA + LATCH cross the barrier.")
print(f"    {3} optos per channel out, +1 back for readback = {4*CH} total.")
print(f"    {BITS*CH*3} parts -> about {4*CH*3} - a {BITS*CH*3/(4*CH*3):.1f}x saving.\n")

VDD_PICO, VF, VDD_ISO = 3.3, 1.2, 5.0
for IF_MA in (5, 10):
    R = (VDD_PICO - VF)/(IF_MA/1000)
    print(f"  If {IF_MA:>2} mA -> LED resistor {R:.0f} ohm"
          f"  (RP2040 GPIO sources 12 mA max)")
for ctr in (0.8, 0.4):
    ic = 5 * ctr
    for pull in (1e3, 10e3):
        need = VDD_ISO/pull*1000
        print(f"    CTR {ctr*100:>3.0f}% at If 5 mA -> Ic {ic:.1f} mA;"
              f" {pull/1e3:.0f}k pull-up needs {need:.1f} mA -> {ic/need:.0f}x margin")
print("""
  Optos are slow - tens of microseconds with a 10k pull-up - and here that
  costs nothing: the setpoint changes when a human turns a knob. But it does
  cap the shift clock. Run it at a few kHz, not at SPI speeds; 10 bits then
  takes single-digit milliseconds.

  Power-on: an RC reset on the shift register's clear pin puts all outputs at
  0 before the Pico says anything, which is 2 V out. If the isolated side ever
  browns out the register clears and the output FALLS. Both safe directions.

  Readback crosses the SAME barrier. Measuring V and I for a display means an
  ADC on the isolated side and its data coming back through one more opto -
  share the clock with the shift register and it costs one part per channel.""")

# ---- what NOT to use --------------------------------------------------------
print("\n=== Why not a linear digipot as the bottom leg ===")
RPOT, TAPS = 50e3, 256
step_r = RPOT/(TAPS-1)
vout = lambda rb: VREF*(1+RTOP/rb)
print(f"  {RPOT/1e3:.0f}k, {TAPS} taps -> {step_r:.0f} ohm per tap")
for rb in (1.0e3, 5.0e3, 49.33e3):
    print(f"    at {vout(rb):>5.1f} V  one tap moves it"
          f" {abs(vout(rb)-vout(rb+step_r)):>7.3f} V")
lo = abs(vout(49.33e3)-vout(49.33e3+step_r)); hi = abs(vout(1e3)-vout(1e3+step_r))
print(f"  step spread {hi/lo:.0f}:1 - Rbot is linear in tap, Vout goes as 1/Rbot.")
print("  The binary-weighted array is uniform at the same bit count, and its")
print("  switches-open state is the safe one for free. A DAC fixes linearity")
print("  but its reset output is an END of the range, not the safe end.")

print("\n=== Serial switches vs a shift register + discrete switches ===")
for ron, part in ((2.5, "ADG714-class octal SPST, SPI"), (100.0, "CD4051-class mux")):
    print(f"  Ron {ron:>5.1f} ohm ({part})"
          f" -> {ron*Gmax*100:5.2f}% error at {VMAX} V")
print("  The serial switch IS the serial-to-parallel converter. One part.")

# ---- fans ------------------------------------------------------------------
print("\n=== Fan staging ===")
rho, cp = 1.2, 1005
for P in (60, 100):
    print(f"  {P:>3} W:  " + "   ".join(
        f"{dT} K rise -> {P/(rho*cp*dT)*2118.9:4.1f} CFM" for dT in (10,15,20)))
print("""  Three 40 mm fans give 9-15 CFM installed - right for 100 W at a 15 K rise.

  Stage on absolute thresholds WITH HYSTERESIS, not on "temperature still
  rising". A derivative trigger fires on every load step and lid opening, and
  it is hard to tune because dT/dt is noisy at any sane sample rate.

      fan 2   on 45 C   off 40 C
      fan 3   on 55 C   off 48 C

  FAN 1 IS NOT ON THIS LIST. Cooling must not depend on firmware: hardwire
  fan 1 to run whenever the box is powered, and let the Pico stage 2 and 3.
  A box dissipating 100 W with no fans because the Pico is halted, or because
  someone is reflashing it, is a fire - not a bug.

  Fans want 12 V, the Pico wants 5, and neither can come off an adjustable
  channel. That is a small auxiliary mains supply: 12 V for fans, 5 V derived
  for the Pico.""")
