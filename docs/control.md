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

## Not a digipot or a DAC, and the reason is not cost

The obvious simplification is a serial digital potentiometer as the bottom leg.
It fails on resolution. `Rbot` is linear in tap, but `Vout` goes as `1/Rbot`:

```
      near      Rbot     Vout  next tap      step
    60.0V    1.00k   60.00V    50.30V    9.705V
    12.6V    5.00k   12.64V    12.19V    0.447V
     2.0V   49.33k    2.00V     2.00V    0.005V
```

A 50k/256-tap part gives **5 mV steps at the bottom and 9.7 V steps at the top**
— a 2000:1 spread, and unusable where you most want resolution. The
binary-weighted array gives 0.227 V *everywhere* at the same 8 bits, because
conductances add and Vout is linear in conductance.

A DAC injecting into the FB node fixes the linearity but loses the fail-safe:
its zero/reset output is one *end* of the range, and the polarity that would
make 0 V mean 2 V out is the one you cannot have — current sourced into FB
always *lowers* Vout. Getting a safe default back needs an inverting stage or a
watchdog on top of it.

The switched array gets uniform steps and a safe default from the same
property, for the price of some resistors.

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

A **serial-to-parallel device on the isolated side** (powered from that
channel's own rail) takes the clocked stream and drives the switch array. Only
three lines cross per channel:

```
  Pico --SPI--> [opto] [opto] [opto] --> serial-to-parallel --> switch array
                 CLK   DATA   LATCH          (isolated side)        |
                                                                 divider
                                                              bottom leg
```

### Use serial switches, not a shift register plus discrete switches

An **ADG714-class octal SPST** is SPI-controlled analog switches in one package
— it *is* the serial-to-parallel converter and the switch array, and its Ron is
about 2.5 Ω instead of a CD4051's ~100:

```
  Ron   2.5 ohm ->  0.25% error at 60 V (where Rbot is 1k)
  Ron 100.0 ohm -> 10.00% error at 60 V
```

Two daisy-chained give 16 bits of divider off the same three wires. Against
`74HC595` + discrete switches it is fewer parts, far lower Ron and the same
barrier cost. **Verify the power-up state is all-switches-open** — that is the
fail-safe direction, and it is the one thing worth reading the datasheet for
rather than assuming.

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

**Power-on state:** the switches must come up open, which is 2 V out. With an
`ADG714`-class part that should be its reset state — confirm it. With a
`74HC595` it is an RC reset on the clear pin. Either way, if the isolated side
browns out the outputs drop and the channel output *falls*. Both safe
directions.

### The interface is SPI, and that is forced by the optos

Every optocoupler is **unidirectional**. I²C's bidirectional `SDA` needs two of
them plus care to avoid latching itself low. SPI's lines each go one way by
definition, so they map onto optos with nothing clever required.

```
  out:  SCK, MOSI, CS_switches, CS_adc   = 4 optos   LED on the Pico side
  back: MISO                             = 1 opto    LED on the ISOLATED side
        5 per channel, 10 total   (against 20+ for one-opto-per-bit)
```

**Every line crosses optically, both directions.** The four outbound ones have
their LEDs on the Pico's side; the return has its LED on the *isolated* side,
driven by the ADC's and switch chip's `MISO` output through its own resistor,
with the phototransistor on the Pico. Nothing electrical bridges the gap — which
is the whole point, since these two channels get stacked in series.

That return opto is subject to the same speed limit as the rest: tens of
microseconds with a 10k pull-up. It bounds `MISO` exactly as it bounds `SCK`, so
the few-kHz clock covers both.

### Readback crosses the same barrier — and switch state comes free

The Pico needs current, voltage, and **confirmation that the switch word it
sent is the one that actually latched**. All three come back on that single
`MISO` opto.

**Switch state costs nothing extra.** The daisy-chain output of the switch chip
(or a `74HC595`'s `QH'`) shifts out what was previously loaded. Clock the new
word in and the old one comes back on the `MISO` line already there for the ADC.
Compare it against what was sent last time, and a bit corrupted in the barrier
becomes visible. On a box that can put 60 V out, that is worth having — an
undetected stuck bit is a wrong output voltage, silently.

**Current sense:**

```
   shunt   V at 3A        P   gain for 3.3V   12-bit LSB
     10m    30.0mV     90mW            110       0.73mA
     20m    60.0mV    180mW             55       0.73mA
     50m   150.0mV    450mW             22       0.73mA
```

**20 mΩ with a gain-50 amp** gives 3.0 V full scale — a stock INA gain, 180 mW
in the shunt, 0.73 mA per count at 12 bits.

High-side sensing puts the output on the amplifier's **common mode: up to 60 V**.
That needs an `INA293`-class part rated ≥80 V CM, not a garden-variety 26 V one.
Low-side is easier but puts the shunt in the return, which regulation then has
to account for.

### Current limit is analog too

The Pico reads current; it must not *enforce* the limit. Constant-current mode
needs an analog loop — an error amplifier on the shunt, diode-OR'd into the same
feedback node as the voltage loop, so whichever demands less wins. **The Pico
sets the CC threshold** (a second switched divider, or a DAC, on the isolated
side) and the analog loop acts on it.

This is the same argument as the main loop, and it matters more here: a short
circuit on the output is exactly the case where a millisecond-scale software
response is too slow.

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

### The auxiliary supply: one 5 V module off the mains

**5 V fans settle it** — there is no 12 V rail in the box at all. A single
off-the-shelf 120 V → 5 V module runs the Pico, the fans and the opto LEDs.
Neither can come off an adjustable channel, for the same reason as [not putting
the fan on the adjustable
rail](../README.md#the-fan-is-not-a-load-for-the-adjustable-rail): the user can
turn that rail down.

```
  Pico (RP2040, no radio)                      100 mA
  3 x 5 V 40 mm fans @ ~200 mA                 600 mA
  opto LEDs, 10 x 5 mA (worst case all on)      50 mA
  TOTAL                                        750 mA = 3.8 W

  5 W module  -> 1.0 A, 1.3x headroom   MARGINAL
  10 W module -> 2.0 A, 2.7x headroom   comfortable
```

**Buy the 10 W, not the 5.** The fans dominate and they draw their worst at
startup, all three at once if the box comes up hot.

Give the fans their own decoupling, or their own feed from the module. Brushed
or not, fan commutation puts spikes on the rail, and the Pico's ADC is reading
millivolts of shunt signal.

### What the module must NOT power: the isolated sides

Each channel's switch chip, ADC and sense amp sit on **that channel's ground**.
Feeding them from the control 5 V rail wires the two channels together and
undoes the isolation the second transformer was bought for.

They power themselves locally, and it costs nothing: each channel already has
its own ~40 V raw rail from its own toroid, isolated from the other by
construction. Either a small 60 V-capable buck per channel, or — check this
first — **the switching controller's own VCC/bias output**, which on many parts
can spare the tens of milliamps this needs.

### Check the fans actually move the air

```
  needed: 11.7 CFM for 100 W at a 15 K rise
  12 V 40 mm: ~8 CFM free, ~4.0 installed -> 3 of them = 12.0 CFM   OK
   5 V 40 mm: ~5 CFM free, ~2.5 installed -> 3 of them =  7.5 CFM   SHORT
```

A 5 V fan of a given size spins slower than its 12 V cousin, so **three 5 V
40 mm fans may not reach the number**. Check the CFM on the fans actually in
hand against 11.7. If they are short, the answer is 60 mm rather than a fourth
40 — more area at lower RPM is quieter as well as better.

## Open

- Where the temperature is measured. The pass elements and heatsinks will lead
  the toroids by a long way, so the thresholds above belong to whichever sensor
  is hottest — decide the sensor before the numbers.
- 4-pin PWM fans instead of on/off staging? Continuous ramping is quieter and
  the Pico has PWM to spare.
- Resolution: 10 bits gives 57 mV steps. Fine for a bench supply, coarse for
  anything calibrated.
- Where the temperature sensors sit electrically. A heatsink is often tied to a
  pass device's tab, which is a switching node — so the sensor may be on the
  isolated side too, and its reading has to come back across the barrier with
  everything else.
- Whether a watchdog should clear the switch array if the Pico stops talking.
  The register currently holds its last setpoint, which fails *level* rather
  than *safe* — acceptable, since it cannot fail upward.
