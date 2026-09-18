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

## Decided: the isolated side stays dumb

Per-channel microcontrollers were considered — a small MCU on each switcher
board, talking to the Pico over a serial link — and rejected. **The isolated
side holds no firmware.** Only switches, an ADC and a sense amp, doing what they
are told over SPI.

### "Offload the work" is not an argument, because there is no work

```
BUS OCCUPANCY - how busy the wires are:
  V/I readback, 32 bits, 10 Hz, x2 channels     12.8%
  1-Wire read, 3 sensors, 1 Hz                   1.5%
  setpoint, only on knob turns                   0.1%
  TOTAL                                         14.4%

CPU OCCUPANCY - SPI on DMA, 1-Wire on PIO
  well under 1% of ONE of two cores at 125 MHz
```

The DS18B20's 750 ms conversion is **latency, not occupancy** — issue the
convert, go away, come back. Blocking on it would be a firmware bug, not a
reason to add silicon.

### What would genuinely argue for it, if this is ever revisited

- **2 optos per channel instead of 5** — 4 total rather than 10
- **Calibration lives on the channel**, so a board carries its own constants
- **Local housekeeping shares the channel's ground**, which would make the
  sensor-isolation problem vanish rather than be designed around

### Why not, anyway

It is roughly a wash on parts — six optos saved against two MCUs, their
supplies and decoupling — and plainly not a wash on firmware: two more
codebases, two more bootloaders, and version skew between them and the Pico. It
also does not touch the hard part, since [CC and cycle-by-cycle
protection](#current-limit-is-analog-too) stay analog either way.

**And it would weaken the fail-safe.** "Switches open = 2 V" is currently
*structural*: it holds when the isolated side is unpowered, resetting, or being
reflashed, because it is a property of the resistor network rather than of any
code. A hung MCU holding a high setpoint is a state that cannot exist today, and
adding one would create it.

A side that can only do what it is told, with its safe default built into the
divider, is far easier to reason about than one running its own program.

### RS-232 would have broken the isolation outright

Worth recording as a trap rather than a preference. **RS-232 is
ground-referenced** — ±12 V signalling against a common return — so wiring it
between the Pico and a channel board ties those grounds together and destroys
the barrier. That is the same failure as [powering the isolated side from the
control rail](#what-the-module-must-not-power-the-isolated-sides) or bolting a
sensor to a heatsink: the fourth way to give it away by accident.

Isolated RS-232/RS-485 transceivers exist, but they are digital isolators with a
transceiver bolted on — you pay for the isolation either way, so pay for it with
optos.

If MCUs ever do go in, the link is **optical UART at 9600**. 19200 is already
marginal through a cheap opto at 52 µs per bit, and nothing here needs the
speed:

```
    2400 baud ->  416.7 us per bit   fine
    9600 baud ->  104.2 us per bit   fine
   19200 baud ->   52.1 us per bit   marginal
  115200 baud ->    8.7 us per bit   needs a fast opto
```

## Cooling

```
  100 W:  10 K rise -> 17.6 CFM   15 K -> 11.7 CFM   20 K -> 8.8 CFM
   60 W:  10 K rise -> 10.5 CFM   15 K ->  7.0 CFM   20 K -> 5.3 CFM
```

Three 40 mm fans give 9–15 CFM installed, which lands on 100 W at a 15 K rise.
One 80 mm would move the same air far more quietly — **staging is what buys the
quiet at low load**, which is most of the time.

### Temperature sensing: 1-Wire, and isolated by the packaging

**The deciding question is not which bus. It is where the sensors sit
electrically.**

The temperature that matters is the pass-element heatsink. In a 4-switch
buck-boost the FET tabs are switching nodes, so they mount on insulators and the
heatsink is then tied to **its own channel's ground** for EMI. Channel A's
heatsink and channel B's are therefore at two different potentials — and when
the channels are stacked for ±60 V, 60 V apart.

**A metal-cased sensor bolted to each, both wired back to the Pico's ground,
bridges the two channels and undoes the isolation.** Again — this is the third
place the barrier can be given away by accident, after the setpoint divider and
the control rail.

Couple them thermally and isolate them electrically, and the problem disappears:
every sensor then lives on the Pico's ground, nothing crosses the barrier, and
the bus choice becomes free.

| | 1-Wire (DS18B20) | I²C (TMP102/LM75) |
|---|---|---|
| pins | **1** + pull-up | 2 |
| sensors per bus | many, unique 64-bit IDs | 8 addresses typical |
| cable runs | designed for metres | keep short — bus capacitance |
| addressing | automatic | plan addresses, strap pins |
| conversion | 750 ms at 12-bit | tens of ms |
| isolated probe form | **stainless, off the shelf** | rare |

**1-Wire.** One GPIO for the lot, sensors spread over a 285 mm box, no address
planning — and the stainless probe form is **electrically isolated by
construction**, which solves the problem above through packaging rather than
through care. (Good enough for a 60 V heatsink. It is not safety insulation, so
do not use one against anything at mains potential.)

The 750 ms conversion looks slow and is not. A heatsink's thermal time constant
is tens of seconds, so sampling at 1 Hz gives ~60 samples per time constant —
two orders of magnitude more than the control needs. **Thermal management is not
a fast loop.**

Neither bus would survive the opto barrier, incidentally: both are
bidirectional, and `SDA` and the 1-Wire data line have the same problem
[`MISO` does not](#the-interface-is-spi-and-that-is-forced-by-the-optos). Another
reason to keep the sensors on the Pico's side.

### Three sensors, and what each is for

| where | for |
|---|---|
| **pass-element heatsink** | drives the fan staging — it leads everything else by a long way |
| **toroid** | slow and high-mass, and it has its own thermal fuse; logging and a shutdown backstop |
| **intake air** | ambient reference. In the fan stream, away from any heatsink, or it reads its own self-heating |

The thresholds below belong to the **heatsink** sensor.

### A failed read must stage up

CRC failure, a missing sensor, a shorted bus: the firmware treats that as **hot**
and runs the fans. Not as cold, and not as "hold the last value". Same principle
as fan 1 being hardwired — the failure direction has to be the safe one.

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

### The module

| | |
|---|---|
| Rating | **5 V 3 A, 15 W**, isolated, 100–264 VAC in |
| Board (YS-U20S drawing) | 86.5 × 46.5 mm, ~24 mm tall (2 mm PCB + 22 mm parts) |
| Mounting | 4 × Ø3.2 |
| Terminals | 5.08 mm screw blocks both ends — `ACL`/`ACN` in, `+V`/`−V` out |

**3 A against a 750 mA load is 4× headroom** — comfortably past the "buy the
10 W not the 5 W" line, and enough to fix the airflow shortfall below by going
to 60 mm fans without worrying about the supply.

Screw terminals at both ends are welcome: no soldering to mains, and the DC side
lands straight on the control rail. The universal 100–264 V input also means it
does not care what the mains does.

> **Two datasheets, possibly two parts.** The mechanical drawing is a
> **YS-U20S** at 86.5 × 46.5 × 24; the linked NOYITO listing describes itself as
> *ultra-small*, which 86.5 mm is not. They may be the same board rebadged or
> they may not. **Take the mechanical numbers from whichever one actually
> arrives** — the enclosure depends on them, and the "on edge in the back bay"
> conclusion below is computed from the YS-U20S drawing.

#### Fuse the branch — 1 A, not 3

A separate fuse on this branch is right: the C14's fuse is sized for the whole
box and would never notice a fault in a 156 mA load. The value is the problem.

```
  at its 15 W rating        18.8 W in ->  156.2 mA
  at the real 3.8 W load     5.1 W in ->   42.2 mA
```

**A 3 A fuse is 19× the module's maximum input current.** The module can fail
short and cook without ever blowing it. A fuse that cannot blow is not there.

```
  0.25 A time-delay -> 1.6x rated draw   tight, inrush may nuisance-trip
  0.5  A time-delay -> 3.2x rated draw   sensible
  1.0  A time-delay -> 6.4x rated draw   sensible  <- chosen
  3.0  A               19x rated draw    cannot clear a fault in this branch
```

**1 A time-delay.** Time-delay rather than fast, because the module's input
capacitor charges through the fuse at switch-on. 1 A is the looser end of
sensible — it will clear a hard short but not a partial failure drawing a few
hundred milliamps — and it is stocked everywhere in 5 × 20, which 0.5 A often
is not.

#### All three branches, since the inlet now feeds three loads

| branch | draw | fuse |
|---|--:|---|
| toroid A primary, 350 VA | 2.92 A | 4 A time-delay |
| toroid B primary, 350 VA | 2.92 A | 4 A time-delay |
| 5 V control module | 0.16 A | **1 A time-delay** |
| **total** | **5.99 A** | 8 A time-delay at the C14 |

The branch values differ by **8:1**, which is exactly why branch fusing earns
its keep — one 8 A fuse upstream protects the cord and nothing else. The inlet
module is rated 10 A; that is a ceiling, not a recommendation.

Toroid primaries want time-delay regardless: a 350 VA toroid's inrush will pop
a fast fuse of any sensible rating, which is the same reason [the soft
start](power-chain.md#what-this-does-to-the-enclosure) is on the list.

#### It is open frame — so it needs a cover too

This is the part that matters. It is a **bare PCB with live AC terminals and a
live primary side** — so the inlet's spades are no longer the only exposed mains
in the box, and the [shield](../README.md#the-inlet-is-on-the-back-wall--and-brought-a-shield)
no longer covers everything that needs covering.

It needs the same treatment: a printed hood over it, or mounting it inside an
extension of the mains shield. The same rule applies either way — **no exposed
mains that a finger can reach with the lid off.**

#### Where it goes: landscape on the back wall, beside the inlet

Mounted **landscape, flat against the back wall**, low, at the **END A end** —
the intake end, so it sits in cool air rather than the exhaust, and close to
where the fans cluster.

**Not above the inlet.** The mains shield's roof is at z 68.5 and the rim taper
starts at 89, so there is **20.5 mm** of height above it and the board needs
46.5 landscape. Beside it there is **118 mm** of clear wall each way for an
86.5 mm board.

Standing it against the wall also solves the depth problem: lying on the floor
the board needs 46.5 mm and the back bay has 34; stood up it projects only its
24 mm of components plus standoffs, and the shell comes to **31.5 mm** — the
same 2.5 mm gap to the supply that the mains shield has.

```
5V shell  95.5 x 31.5 x 51 at x 62 on the back wall
          bay spare 2.5, gap to the mains shield 10.75
```

#### How it is held: two screws through the back wall

**Side tabs to floor posts were the first attempt and do not fit** — shell plus
tabs is 123.5 mm against 115 mm of free wall. Two M3 screws through the back
wall from outside, into blind bosses inside the shell, cost no length at all.
Same idea as the fan, which also screws in from the outside face.

**The bosses are blind on purpose.** The screw must stop in plastic and never
break through into the shell's interior, because that interior is mains.

#### It makes the inlet a distribution point

The IEC inlet now feeds **three** loads: toroid A's primary, toroid B's primary,
and this module's AC input. The shield was sized for three booted spades
*leaving* it. It is now a junction, and either it grows to hold a small mains
terminal block or that block lives beside it under its own cover.

Worth settling before the toroid layout is drawn, because it changes what the
back bay has to contain.

### Driving the fans: the 2N7002 boards, with a bigger transistor

The [2N7002 driver boards](../../TritonECU/hardware/2N7002%20Driver/) are the
right *shape* for this — but they were specified for 14 mA into a DM542
optocoupler, and a fan is fifteen times that.

```
 fan current   vs 115 mA rating     Vds   P in FET     verdict
       80 mA              0.7x   0.40V       32mW      ok
      120 mA              1.0x   0.60V       72mW      OVER RATING
      200 mA              1.7x   1.00V      200mW      OVER RATING
      250 mA              2.2x   1.25V      312mW      OVER RATING
```

A SOT-23 sheds roughly 200–350 mW at 25 °C and far less in a box already
shedding 100 W. Starting current is 2–3× running, so a 200 mA fan asks for
**400–600 mA at switch-on**. And that table is optimistic: it assumes 5 Ω, which
is the 2N7002 well enhanced — a **3.3 V** Pico GPIO does not enhance it that
far, so the real drop and dissipation are worse.

#### Keep the boards, swap the FET

The board carries the parts that actually matter: the 220 Ω gate resistor and,
more importantly, the **10 kΩ gate pulldown** that holds the FET off while the
Pico's GPIOs are high-impedance during boot. Both are right for any N-FET.

```
  2N7002  SOT-23: pin1 Gate, pin2 Source, pin3 Drain
  AO3400A SOT-23: pin1 Gate, pin2 Source, pin3 Drain   -- same pinout
```

| | Rds(on) @ Vgs 4.5 | at 250 mA | rated |
|---|--:|--:|--:|
| 2N7002 | 5 Ω | 1250 mV, 312 mW | 0.12 A |
| **AO3400A** | **28 mΩ** | **7 mV, 1.8 mW** | **5.7 A** |

A true logic-level part with Vgs(th) under ~1.2 V, so a 3.3 V gate fully turns
it on. Same footprint, same pinout, same passives — a transistor swap, not a
redesign.

#### Add a flyback diode, which the board does not have

A fan is an inductive load and the board leaves the drain open with no freewheel
path, so switching off spikes it. The 2N7002's 60 V gave some margin; an
AO3400's 30 V gives less. **A diode across each fan, cathode to +5 V** — a
1N4148 is ample at these currents.

#### You need two boards, not three

Fan 1 is [hardwired on](#fan-1-is-not-on-that-list) and has no FET at all. Only
fans 2 and 3 are switched.

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
- Whether a watchdog should clear the switch array if the Pico stops talking.
  The register currently holds its last setpoint, which fails *level* rather
  than *safe* — acceptable, since it cannot fail upward.
