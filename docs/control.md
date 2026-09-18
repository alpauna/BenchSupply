# Control and cooling

What the Pico does, what it deliberately does not do, and how it reaches two
isolated channels without giving the isolation away.

Numbers here come from [`calc/control.py`](calc/control.py).

```bash
python3 docs/calc/control.py
```

---

## The split: hardware closes the loop, the Pico moves the setpoint

**A dedicated TI/Maxim switching controller regulates each channel.** The Pico
never modulates anything. It selects the feedback divider, reads back V and I,
drives the display and the knob, and stages the fans.

This is not a stylistic preference — the RP2040 cannot do the other job:

```
200 kHz -> 5.0 us period
  PWM at 125 MHz: 625 counts = 9.3 bits of duty resolution
  ADC 500 kSPS  -> 2.5 samples per switching cycle
  cycle-by-cycle current limit must act in ~100 ns = 2% of one cycle
  RP2040 has no analog comparator
```

The duty resolution is survivable and the loop bandwidth is arguable. **The
protection is not.** A 180 W converter needs cycle-by-cycle overcurrent limiting
that acts inside a fraction of one switching cycle, and only analog hardware
does that. Lose regulation on a software modulator and 60 V goes into whatever
is plugged in with 8 A of inductor behind it.

The controller handles microseconds. The Pico handles milliseconds and up.

**Check the controller's output rating.** 60 V out means the part must stand
60 V on the output side, and much of the 4-switch buck-boost family stops below
that. Same trap as [the DC-DC module rated 40 V on a 45 V
rail](power-chain.md#the-inductor) — verify before committing.

## Setting the output: switch the bottom leg of the divider

```
Vout = Vref * (1 + Rtop * G)        G = bottom-leg conductance
```

With Vref 0.8 V and Rtop 74k, Rbot runs 1.00k at 60 V to 49.33k at 2 V —
1000 µS down to 20.3 µS.

**Vout is linear in conductance**, and parallel conductances add, so
binary-weighted switched resistors give *uniform voltage steps*. No lookup
table, no calibration curve:

| bits | step | branches |
|--:|--:|--:|
| 8 | 0.227 V | 8 |
| **10** | **0.057 V** | 10 |
| 12 | 0.014 V | 12 |

**Switch the bottom leg only.** The top leg sits at Vout, and no analog switch
wants 60 V across it.

**Ron hurts most at the top of the range**, because that is where the branch
resistance is smallest:

```
  Ron   5 ohm ->  0.50% at 60 V,  0.01% at 2 V
  Ron  50 ohm ->  5.00% at 60 V,  0.10% at 2 V
  Ron 100 ohm -> 10.00% at 60 V,  0.20% at 2 V
```

A CD4051-class mux at ~100 Ω costs 10 % at full output. Use low-Ron switches, or
fold a known Ron into the branch values.

Keep the divider and its switches **physically at the controller**. The FB node
is the most noise-sensitive point in the converter; running it across the box to
a mux invites instability.

## Wire it so a dead Pico gives 2 V, not 60

**Switches open must mean minimum output.** Size the *fixed* branch for 2 V and
let the switches **add** conductance to climb. Then a Pico that is unpowered, in
reset, or mid-reflash leaves 2 V on the terminals.

Wire it the other way round — switches closed for minimum — and every one of
those states commands full output.

## The barrier: optocouplers, but serialised

The two channels are isolated so they can be stacked for ±60 V. **One Pico
touching both feedback networks ties their grounds together and throws that
away.** The Pico stays on its own ground and everything crosses a barrier.

Optos suit this well: the setpoint lines are *static*, changing only when a
human turns a knob, so their speed penalty costs nothing.

**But do not use one opto per bit.**

```
10 bits x 2 channels = 20 switch lines
  one opto per line  -> 20 optos + 20 resistors + 20 pull-ups = 60 parts
  serialised         -> CLK + DATA + LATCH, +1 back for readback
                     -> 8 optos, about 24 parts - a 2.5x saving
```

A **shift register on the isolated side** (powered from that channel's own rail)
takes the serial stream and drives the switch array. Only three lines cross per
channel.

Sizing, for a garden-variety transistor-output opto:

```
  If  5 mA -> LED resistor 420 ohm     (RP2040 GPIO sources 12 mA max)
  If 10 mA -> LED resistor 210 ohm
    CTR  80% at If 5 mA -> Ic 4.0 mA;  10k pull-up needs 0.5 mA -> 8x margin
    CTR  40% (aged)     -> Ic 2.0 mA;  10k pull-up needs 0.5 mA -> 4x margin
```

Comfortable even after CTR halves with age. **Run the shift clock at a few kHz,
not at SPI speeds** — a 10k pull-up and a phototransistor make edges tens of
microseconds long. Ten bits then takes single-digit milliseconds, which nobody
turning a knob will notice.

**Power-on state:** an RC reset on the shift register's clear pin puts every
output at 0 before the Pico says anything — which is 2 V out. If the isolated
side browns out, the register clears and the output *falls*. Both safe
directions.

**Readback crosses the same barrier.** Displaying V and I means an ADC on the
isolated side with its data returning through one more opto. Share the clock
with the shift register and it costs one extra part per channel.

## Cooling

```
  100 W:  10 K rise -> 17.6 CFM   15 K -> 11.7 CFM   20 K -> 8.8 CFM
   60 W:  10 K rise -> 10.5 CFM   15 K ->  7.0 CFM   20 K -> 5.3 CFM
```

Three 40 mm fans give 9–15 CFM installed, which lands on 100 W at a 15 K rise.
One 80 mm would move the same air far more quietly — **staging is what buys the
quiet at low load**, which is most of the time.

### Stage on thresholds with hysteresis, not on "still rising"

| | on | off |
|---|--:|--:|
| fan 2 | 45 °C | 40 °C |
| fan 3 | 55 °C | 48 °C |

A rising-derivative trigger fires on every load step and every lid opening, and
it is hard to tune because dT/dt is noisy at any sane sample rate. Absolute
thresholds with a few degrees of backlash will not chatter.

### Fan 1 is not on that list

**Cooling must not depend on firmware.** Hardwire fan 1 to run whenever the box
is powered and let the Pico stage 2 and 3. A box dissipating 100 W with no fans
because the Pico is halted — or because someone is reflashing it — is a fire,
not a bug.

### The auxiliary supply

Fans want 12 V, the Pico wants 5, and **neither can come off an adjustable
channel** — the same argument as [not putting the fan on the adjustable
rail](../README.md#the-fan-is-not-a-load-for-the-adjustable-rail). That means a
small auxiliary mains module: 12 V for the fans, 5 V derived for the Pico.

## Open

- Where the temperature is measured. The pass elements and heatsinks will lead
  the toroids by a long way, so the thresholds above belong to whichever sensor
  is hottest — decide the sensor before the numbers.
- 4-pin PWM fans instead of on/off staging? Continuous ramping is quieter and
  the Pico has PWM to spare.
- Resolution: 10 bits gives 57 mV steps. Fine for a bench supply, coarse for
  anything calibrated.
- Whether a watchdog should clear the shift register if the Pico stops talking.
  The register currently holds its last setpoint, which fails *level* rather
  than *safe* — acceptable, since it cannot fail upward.
