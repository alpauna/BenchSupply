# Power chain

What the bench supply is, and why it is shaped this way. The enclosure follows
this document, not the other way round — and **as of this writing the enclosure
in `bench_supply.scad` is the wrong box for it.** See [What this does to the
enclosure](#what-this-does-to-the-enclosure).

Every number below comes out of the scripts in [`calc/`](calc/). Run them
rather than trusting the tables.

```bash
python3 docs/calc/power_budget.py    # transformer, rails, power, heat
python3 docs/calc/inductor.py        # core geometry, winding, losses
python3 docs/calc/core_choice.py     # which core to buy, solved under DC bias
python3 docs/calc/floor.py           # floor thickness under the transformers
python3 docs/calc/control.py         # setpoint divider, opto barrier, fans
python3 docs/calc/fets.py            # the four switches and their heatsinking
```

Control electronics and cooling are in [`control.md`](control.md).

---

## What it has to be

| | |
|---|---|
| Channels | **2** |
| Range | **2 V to 60 V**, adjustable |
| Current | **3 A**, to a **150 W per channel** ceiling — see the envelope |
| Regulation | both channels regulated |
| Isolation | **channel to channel**, so they can be wired in series for ±60 V |

That last line is the one that shapes everything. Two independent supplies that
can be stacked is a different machine from one supply with two rails.

## The transformer

**Seco-Larm ST-1228-T350Q**, from
[its datasheet](https://www.seco-larm.com/wp-content/uploads/2021/08/PI_ST-1228-T350Q_200728.pdf):

| | |
|---|---|
| Output | **28 VAC**, 12.5 A, 350 VA |
| Secondary | **one winding**. "Output wire Gray, AWG#14" — no centre tap |
| Input | 120 VAC, brown AWG#18 |
| Size, mass | 113 × 117 × 70 mm, **2.90 kg** |
| Built in | thermal fuse, transient suppressor, shielded windings |

The 28 V is not on the nameplate as such — it is 350 VA ÷ 12.5 A, and the model
number reads ST-12/**28**. It is a security-industry transformer meant to feed
Seco-Larm's own ST-2406 AC→DC units, which is why it has one plain winding.

## 350 VA is not 350 W

A capacitor-input filter draws short, tall current pulses. The winding sees an
RMS current much larger than the DC the rectifier delivers, so the usable DC
power is about **62 %** of the VA rating:

```
350 VA x 0.62 = 217 W DC usable
```

This single derating decides the rest of the document. Skip it and every power
budget comes out about 60 % too optimistic.

## One transformer is one channel

```
one channel, 60 V x 2.5 A = 150 W out
  -> 176 W DC in at 85%   -> needs 285 VA     against 217 W available: +41 W
both channels             = 300 W out
  -> needs 569 VA                             one 350 VA is 61% of that
```

**So: one transformer per channel — two ST-1228-T350Q.**

### It is power limited, not current limited

**3 A up to 50 V, tapering to 2.5 A at 60 V**, 150 W per channel. The
transformer does not care about amps, it cares about watts — 3 A at 12 V is 36 W
and nothing to it. A flat 2.5 A derate would have thrown the bottom of the range
away for no reason.

### The envelope, per channel

| V | I max | P | limited by |
|--:|--:|--:|---|
| 2 V | 3.00 A | 6 W | current |
| 5 V | 3.00 A | 15 W | current |
| 10 V | 3.00 A | 30 W | current |
| 12 V | 3.00 A | 36 W | current |
| 15 V | 3.00 A | 45 W | current |
| 20 V | 3.00 A | 60 W | current |
| 24 V | 3.00 A | 72 W | current |
| 30 V | 3.00 A | 90 W | current |
| 36 V | 3.00 A | 108 W | current |
| 40 V | 3.00 A | 120 W | current |
| 45 V | 3.00 A | 135 W | current |
| 48 V | 3.00 A | 144 W | current |
| **50 V** | **3.00 A** | **150 W** | **the corner** |
| 52 V | 2.88 A | 150 W | **power** |
| 55 V | 2.73 A | 150 W | **power** |
| 58 V | 2.59 A | 150 W | **power** |
| 60 V | 2.50 A | 150 W | **power** |

**Both channels can do this at once**, because each has its own transformer.
That is what the second ST-1228 buys, beyond the isolation.

### Stacked and paralleled

The channels are isolated, so they combine — which was the point:

| configuration | range | notes |
|---|---|---|
| **series** | to **120 V**, 3 A below 100 V, 2.5 A at 120 V | 300 W total |
| **± split** | **±60 V** about a common centre | the original requirement |
| **parallel** | to **6 A** below 50 V | 300 W total, but see below |

**Series needs a reverse-protection diode across each output — across, not in
series with it.** If one channel is off, current-limited or shorted while the
other is driving, the live one pushes current backwards through the dead one,
and the diode gives that current somewhere to go.

```
      +out ---+-------------------> load
              |
            [diode]   cathode to +out, anode to -out
              |
      -out ---+------------------->
```

It sits **anti-parallel** with the output and is reverse-biased in normal
operation, so it carries no current and drops nothing. Rate it for the full
output current, because that is what it has to survive when it does conduct.

**Nothing goes in series with the output.** A series diode would be intolerable
at the bottom of the range:

```
   Vout    drop    error  loss at 3 A
    2 V    0.5V    25.0%        1.5 W
    5 V    0.5V    10.0%        1.5 W
   60 V    0.5V     0.8%        1.5 W
```

0.5 V on a 2 V output is a quarter of it. Even inside the sense loop, where the
regulator could compensate, it is 1.5 W of heat and a volt the load never sees.
The same argument is why the converter is [synchronous](#synchronous-and-here-that-is-load-bearing):
no junction drops anywhere in the conduction path.

**Parallel is the awkward one.** Two independently regulated voltage sources
fight: whichever reads fractionally higher takes the whole load until it hits
its current limit. Run one channel in CC at the current you want it to
contribute and let the other regulate the voltage, or do not parallel them.

The inductor is sized by the **worst case, not the current cap**: boost at low
line and full power is 6.02 A, and in buck mode the inductor carries the
*output* current, so 3 A there is well under it. One design covers the whole
envelope.

#### Why 150 W and not the 184 W the transformer can just about give

3 A at the full 60 V is 180 W, and one transformer *just* covers it — 342 VA
needed against 350 available, a 2 % margin. The problem is what that margin
consists of:

```
 converter eff    DC in   VA needed    margin
          90%     200W        323      +27   ok
          85%     212W        342       +8   ok      <- the assumption
          82%     220W        354       -4   OVER
```

**Converter efficiency was the entire margin**, and the cap-input factor
multiplies it — at 0.58 rather than 0.62 it is over at any efficiency. Both are
estimates.

Capping at 150 W buys **+41 VA** and moves efficiency from being the deciding
variable to being a detail. It costs only the top corner — the last half amp
above 50 V — and the transformer's thermal fuse stops being something you
design against.

## Isolation comes from the iron, not from the converters

Rectifying one winding twice does not isolate anything. Both outputs still share
the winding, so they cannot be stacked. The barrier has to exist somewhere, and
there are only two places to put it:

| Where | What it costs |
|---|---|
| **In the converters** — two isolated flybacks | custom-wound transformer each, snubber, optocoupler feedback. The hard path |
| **In the iron** — two mains transformers | one more 2.9 kg toroid, and the converters become ordinary non-isolated buck-boosts |

Since 2.5 A per channel already forces a second transformer for power reasons,
**the isolation is free.** That is the argument for buying the second ST-1228
rather than designing two flybacks: it is not really about the iron, it is about
not having to carry a safety barrier inside a switching converter.

```
toroid A -> bridge -> rail A -> buck-boost -> channel A   (floating)
toroid B -> bridge -> rail B -> buck-boost -> channel B   (floating)
                                   series them for +/-60 V
```

## The converter has to boost, and it is not a SEPIC

**Boost is a requirement.** The raw rail is nowhere near 60 V, and it is at its
lowest exactly when the demand is highest:

```
  132 V, no load    44.3 V   60 V needs 1.35x
  120 V, no load    40.2 V   60 V needs 1.49x
  120 V, loaded     32.7 V   60 V needs 1.84x
  108 V, loaded     29.3 V   60 V needs 2.05x   <- design case
```

Low line and loaded is the worst case, and the converter has to make **2.05×**
there. No buck and no linear regulator steps up at all, so the topology must be
buck-boost across the whole range.

**But not a SEPIC.** The
[3–30 V SEPIC work](../../3-30-sepic-3A-DCtoDC/README.md) is 3 A at 5 V — 15 W.
This is **180 W per channel, twelve times that**. A SEPIC's coupling capacitor
carries the full ripple current, and at this power that is a punishing part to
specify and a hot one to live with. Use a **4-switch buck-boost**, or a boost
stage feeding a buck stage. The topology reasoning from the SEPIC documents
carries over; none of the part selection does.

There is also no *switchover* to design. A buck-boost crosses unity gain
continuously — one converter covers 2 V and 60 V with no handover, no relay and
no second regulator to swap in.

## The controller: LT8705

**Analog Devices LT8705**, synchronous 4-switch buck-boost, one per channel.

| | |
|---|---|
| Input | 2.8 – **80 V** |
| Output | 1.3 – **80 V** |
| Switching | 100 – 400 kHz — our 200 kHz sits mid-range |
| Drivers | quad N-channel, so all four switches are FETs |
| Loops | **four**: input voltage, input current, output voltage, output current |

### Why not the obvious TI part

A 60 V output rules out most of the family, which is the trap flagged earlier
and worth showing rather than asserting:

| part | input | output | verdict |
|---|---|---|---|
| **LM5176** (TI) | 4.2–55 V, 60 abs max | ~55 V | our 60 V is **at or over** the limit |
| **LT3790** | 60 V | 60 V | exactly at the limit, **zero margin** |
| **LT8705** | 2.8–80 V | 1.3–80 V | **20 V of margin on both** |

It is an ADI part rather than the TI/Maxim used elsewhere in these projects.
That is the cost, and it is not much of one.

### Synchronous, and here that is load-bearing

All three candidates are synchronous — but it is worth recording *why* not to
substitute a cheaper asynchronous part later:

```
  boost rectifier, diode : 0.5 V x 6.02 A x 0.488 = 1.47 W
  boost rectifier, FET   : 6.02^2 x 28 mOhm x 0.488 = 0.50 W
  buck low side at 12 V, diode : 0.89 W
  buck low side at 12 V, FET   : 0.15 W
  saved: 1.71 W = 1.1 percentage points at 150 W out
```

**Efficiency is the margin in this design.** The budget fits at 85 % with
+8 VA and is *over* at 82 %. Giving a point and a half away to diode drops
gives away most of what capping at 150 W just bought back.

### The input current loop is the feature that matters most

The transformer gives 217 W DC. At the 29.3 V the rail sags to, that is
**7.4 A** of input current.

Set the LT8705's input current limit near there and **the 150 W envelope stops
being a firmware promise and becomes a hardware property.** The transformer
cannot be overdrawn even if the Pico is wrong, hung, or being reflashed. Nothing
else in this design protects the transformer that directly.

### And the output current loop removes a part

CC mode is built in, so the external error amplifier diode-OR'd into the
feedback node — specified in [`control.md`](control.md#current-limit-is-analog-too--and-the-lt8705-already-has-it)
— is no longer needed. The Pico sets the CC threshold; the chip enforces it.

### It also moves the setpoint divider

`FBOUT` regulates at **1.207 V**, not the 0.8 V assumed while the part was
unchosen:

```
  Rtop/Rbot 0.657 at 2 V to 48.7 at 60 V   = 74:1
  with Rtop 48.7k: Rbot 1.00k at 60 V ... 74.1k at 2 V
  conductance 1000 uS ... 13.5 uS
```

Still **linear in conductance**, so binary-weighted switched resistors still
give uniform steps — 10 bits is 57 mV as before. And the part's 1.3 V minimum
output clears our 2 V floor.

## The four switches

Sized from the operating points, in [`calc/fets.py`](calc/fets.py). Two results
are not obvious, and both push against the instinct to buy the lowest Rds(on)
available.

### Specification

| | |
|---|---|
| Rating | **100 V** — one part number for all four |
| Rds(on) | **20–30 mΩ** |
| Gate charge | **≤ 50 nC** — this is the binding parameter |
| Package | TO-220 on a shared heatsink, or D2PAK with good copper |

Candidates in that window: `STD26NF10` (100 V, 33 mΩ, DPAK, low-Qg STripFET),
`STP40NF10L` (designed for minimised gate charge), or an SGT-trench part such as
MCC's `MCP2D5N10Y`. **Confirm Qg from the datasheet** before committing — it is
the number that decides this and the one least reliably quoted.

### Switch A carries the most current and does no switching

```
  boost mode, D = 0.512
    A (buck HS)  ON CONTINUOUSLY    6.02 A  - no switching at all
    C (boost LS) conducts D         4.31 A rms
    D (boost HS) conducts 1-D       4.21 A rms
```

In boost mode the buck-side high side is simply held on, so it carries the full
inductor current and dissipates pure I²R. C and D carry less and take all the
switching loss. They are not interchangeable duties, even though one part number
covers all four positions.

### At 60 V, switching loss beats conduction loss

```
    Rds   A conducts        t_sw   C+D switching
   10m        0.36W         15 ns          1.08W
   25m        0.91W         20 ns          1.44W
   50m        1.81W         30 ns          2.17W
                            40 ns          2.89W
```

Switching energy scales with switching **time**, not with Rds(on) — and gate
charge is what sets the time. **A 10 mΩ part carrying 150 nC loses to a 25 mΩ
part carrying 40 nC.** Hence 20–30 mΩ and low Qg, rather than the lowest
resistance on the shelf.

### Gate charge is a ceiling, not a preference

```
  Qg  30 nC x 4 FETs at 200 kHz ->  24.0 mA and 0.15 W from INTVCC   ok
  Qg  50 nC x 4 FETs at 200 kHz ->  40.0 mA and 0.25 W from INTVCC   ok
  Qg 100 nC x 4 FETs at 200 kHz ->  80.0 mA and 0.51 W               check
  Qg 150 nC x 4 FETs at 200 kHz -> 120.0 mA and 0.76 W               check
```

Four FETs at 200 kHz is a real load on a controller's internal regulator. The
LT8705 has an **`EXTVCC` pin** — supply the gate drive externally and the
internal regulator stops being the constraint. Worth planning for rather than
discovering.

### Heatsinking, and the sensor that goes with it

```
  t_sw 15 ns:  A 0.91 W   C 1.01 W   D 0.98 W   B ~0   total 2.90 W/channel
  t_sw 30 ns:  A 0.91 W   C 1.55 W   D 1.53 W   B ~0   total 3.98 W/channel
```

About **3–4 W per channel** across four devices. Against an internal ambient
near 45 °C and Tj max 150 °C:

| package / mounting | θ | rise at 1.5 W | Tj |
|---|--:|--:|--:|
| DPAK, 1 in² copper | 40 °C/W | 60 °C | 105 °C |
| D2PAK, good copper | 25 °C/W | 38 °C | 82 °C |
| TO-220, clip heatsink | 20 °C/W | 30 °C | 75 °C |
| **TO-220, shared heatsink** | 8 °C/W | 12 °C | 57 °C |

A shared TO-220 heatsink is the easy answer for a hand build — and it is the
heatsink the [1-Wire probe](control.md#temperature-sensing-1-wire-and-isolated-by-the-packaging)
clamps to, which is why that sensor leads everything else in the box.

**All four tabs sit at different potentials**, so each needs its own insulator
on a shared sink. That is precisely why the sink floats at a channel potential,
and why the temperature probe has to be electrically isolated.

## The inductor

Hand-wound, one per channel. At the design point — 29.3 V in, 60 V out, 3 A,
200 kHz — it is **41.5 µH carrying 6.02 A DC with 1.81 A of ripple**, storing
1.00 mJ. (More inductance than the 3 A case, and less current: derating raises
L because the ripple budget is a fraction of a smaller DC current.)

### Powder cores lose permeability under DC bias, and it changes the answer

This is the trap. Size the turns from the datasheet AL and you get an inductor
that is right at no load and badly low exactly where it matters.
[`calc/core_choice.py`](calc/core_choice.py) solves the turns *against* the
biased permeability instead, iterating because more turns means more H means
more roll-off:

```
core OD x ID x H         mu      AL  mu left      N   fits one layer
24.5 x 15.8 x 12.7       60    66nH     68%     28     no
24.5 x 15.8 x 12.7      125   137nH     64%     20    yes
33 x 20 x 11             60    69nH     79%     25    yes
```

The unbiased calculation says 23 turns of 60µ at 25 mm. The biased one says
**28, which does not fit in one layer.** Same core, same target, and the naive
number would have been wound and then found wanting.

Those AL figures are worked out from the outside dimensions, which is fine for
choosing a size but not for winding one — see the 20 % Ae error below. The core
that was actually chosen is done properly, off the catalogue.

### The core: Magnetics **0077083A7** — Kool Mu 0254, 60µ

Ordering code confirmed from [the datasheet](datasheets/KoolMu-0077083A7.pdf),
which is in this repo because finding it was genuinely difficult. Note `083` is
the **ordering code**, not the core-data number — the core data is 0254, and
guessing the part number from it would have failed. Hence the DigiKey number
below: the search is the hard part, not the decision.

| | |
|---|---|
| Part | **0077083A7**, black coated, 61 g |
| DigiKey | **4616-0077083A7-ND** |
| Permeability | **60µ** |
| AL | **81 nH/T² ± 8 %** |
| Ae / le / Ve | 107 mm² / 98.4 mm / 10 600 mm³ |
| Dimensions | OD 40.77 max, ID 23.32 min, HT 15.37 max (coated) |
| Window | 427 mm² |
| Turns | **24** for 41.5 µH at 6.93 A peak — **wind 25 and measure** |
| Wire | **3 × AWG18** twisted, grade 2 heavy build, Class 180 (H) |
| Coating | continuous to 200 °C, Curie 500 °C |
| Hƒ variant | **drop-in** — see below |

Every figure the design was built on matches the datasheet exactly.

#### The DC bias curve is better than assumed — and it was the figure on trust

```
  datasheet minimums:  80% of initial mu at 39 Oe,  50% at 87 Oe
  the estimate used:   80% at 30 Oe,                50% at 80 Oe
```

The real core holds up **better** than the interpolation table assumed, and
those are minimums. At our 21.5 Oe that is **89 %** rather than 87, and the turn
count is unchanged at 24. `core_choice.py`'s 60µ curve is now anchored on these
two points; the other permeabilities in it remain estimates.

#### AL is ±8 %, which is why you wind long and measure

```
  AL high, 87.5 nH   -> 23.1 turns
  AL nominal, 81 nH  -> 24.0 turns
  AL low,   74.5 nH  -> 25.0 turns
```

**Two turns of spread from tolerance alone.** Wind 25, measure, remove one if it
reads high — which was the right instruction before the datasheet and is now the
demonstrably right one.

#### Losses, from the datasheet's own loss figure

```
  datasheet 750 mW/cm3 max at 100 kHz / 100 mT
  ours: 14.6 mT peak at 200 kHz  ->  0.37 W core
  plus                               0.33 W copper
                                     0.70 W total
```

Scaled from the datasheet's single point rather than from memory — the earlier
~0.6 W guess for core loss was close. Copper uses the datasheet's **winding
length per turn, 54.3 mm at 20 % fill** (its 0 % figure, 48.2 mm, equals
2 × (HT + (OD−ID)/2) exactly, which is a good check on the formula).

#### It fits the window with room to spare

24 turns of a 2.21 mm bundle is **92 mm² in a 427 mm² window — 22 % fill.** The
wound coil will come out around **OD 43, HT 19 mm** (the datasheet gives 44.3 /
22.4 at 40 % fill), which is what the enclosure has to accommodate.

**Use the catalogue's Ae, not the one you can work out from the outside.**
Cross-section from the dimensions gives 134 mm²; the catalogue says **107** —
20 % less, because the rounded edges that stop the core cutting the wire take
real iron away. That error put AL at 100 nH instead of 81 and would have had
this wound at 20 turns instead of 22.

```
  mu     AL    N       H  mu left      dB  bundle max      Cu    P_cu    Emax
  40    54n   29  26.1Oe      88%  23.8mT      2.24mm   1.55m   0.39W   105mJ
  60    81n   24  21.5Oe      87%  28.9mT      2.67mm   1.28m   0.32W    70mJ
  75   101n   22  19.4Oe      85%  32.0mT      2.92mm   1.15m   0.29W    56mJ
  90   121n   20  17.9Oe      84%  34.8mT      3.14mm   1.06m   0.27W    47mJ
 125   168n   17  15.4Oe      82%  40.3mT      3.57mm   0.92m   0.23W    34mJ
```

**What did not decide it: DC bias.** Every permeability lands at 80–85 %,
because higher µ needs fewer turns, which lowers H, which offsets the steeper
roll-off curve. On a smaller core that trade runs the other way and low µ wins
on stability — here it does not separate them.

**What decides it is ΔB.** Core loss scales roughly as ΔB^2.1, and Kool Mu's
loss coefficient rises with permeability as well, so the 0.12 W of copper that
125µ saves is paid back several times over in the core. Lower µ, lower ΔB, less
total loss. Check the vendor's loss curves for the magnitude; the direction is
not in doubt.

Energy capacity at 60µ is **70 mJ against 1.00 mJ needed** — 70× — so
saturation is nowhere near the binding constraint. The binding constraint is
loss.

### The Hƒ variant is a drop-in, and does not unlock a faster converter

Magnetics also list **Kool Mu Hƒ**, a lower-core-loss formulation. For core 0254
the two catalogue rows are identical where they overlap:

```
   mu  standard     Hf
  26u       35n    35n   identical
  40u       54n    54n   identical
  60u       81n    81n   identical
  75u ... 125u             not offered in Hf
```

le, Ae, Ve and the dimensions match as well, so **nothing in this design
changes** — same 24 turns, same 3 × AWG18. And Hƒ stopping at 60µ costs nothing
here, because 60µ is where the ΔB argument landed anyway. (26µ would need 37
turns and cap the bundle at 1.84 mm, so it will not take the wire.)

What it buys is perhaps 20–30 % off the core loss — roughly **0.15 W per
channel** against a 5–7 W loss budget. Worth having for free, worth nothing in
efficiency terms, and it runs a little cooler in a box already shedding ~100 W.

**What it does not buy is a higher switching frequency.** Hƒ earns its keep at
500 kHz–1 MHz, where core loss is the limit. Here the limit is MOSFET switching
loss — 4 W at 200 kHz against 10 W at 500 kHz — so a lower-loss core does not
move the ceiling. Choosing Hƒ *in order to* switch faster would be the wrong
reason.

**One thing to confirm if you take the Hƒ variant:** the standard part's bias
curve is now known from its datasheet (80 % at 39 Oe minimum), and the turn
count depends on it. Hƒ matching on AL does not guarantee it matches on bias.
For the standard `0077083A7` this is no longer an open question.

### The wire

```
winding         Cu mm2   bundle      DCR    P_dc    P_ac      J   fits
10 x AWG25       1.62   1.79mm   13.2mR   0.48W     4mW   3.7    yes
5 x AWG20        2.59   2.26mm    8.4mR   0.30W     4mW   2.3    yes
3 x AWG18        2.47   2.21mm    8.8mR   0.32W     5mW   2.4    yes
1 x AWG14        2.08   2.03mm   10.4mR   0.38W     8mW   2.9    yes
```

24 turns leaves room for a bundle up to **2.70 mm** in one layer, which is the
payoff for the bigger core — the drawer core's 15.8 mm hole allowed 1.79 mm.
That headroom is what drops the current density from 4.5 to 2.9 A/mm² and takes
a third off the copper loss for nothing.

**P_ac is milliwatts in every row, including solid AWG14.** The ripple is
0.52 A RMS against 6.02 A of DC — the AC is 9 % of the current, so skin effect
is not what sizes this wire. Strand it because 2.5 mm² of solid copper will not
bend round that hole twenty-two times. Three strands is the fewest that still
handles easily; twist them loosely and treat them as one wire. Cut ~1.3 m per
strand — 24 turns of a 52 mm mean turn is 1.28 m, plus tails and the slack for
the turn you may remove.

### The cores already in the drawer do not work

Worth writing down so it is not re-litigated:

| On hand | Why not |
|---|---|
| "T30-2", measured 24.5 × 15.8 × 12.7 | **T30 is an inch code — 0.30 in = 7.8 mm OD.** The measured core is 3× that in every dimension and 30× the volume, so it is not a T30 of anything. And Micrometals mix 2 is iron powder, not ferrite, so the label contradicts itself |
| …if it is really mix 2 (µ10) | 56 turns needed, 25 fit. µ10 is an RF material, far too low for a 35 µH power inductor in this window |
| …if it is Mn-Zn ferrite (µ~2000), which a 25 × 15 × 12 ring usually is | stores **0.11 mJ** against 1.00 mJ needed — saturates on the first switching cycle |
| green cores, also on hand, "a little smaller" | never measured. Green is usually a power material (Micrometals -52, or a sendust) and would probably work — but the call was to buy to the spec above rather than reverse-engineer the drawer |

**Keep the ferrite rings.** Two switching converters and 5.8 A of mains draw
will want a **common-mode choke**, and an ungapped high-µ ring is exactly right
for that job — no net DC flux, so none of the above applies.

### Securing it — not with rigid epoxy

**Do not pot it in rigid epoxy.** The strongest reason has nothing to do with
epoxy: hand-wound inductance never lands first time, and with the bias roll-off
above you will want to measure L *at current*, adjust turns and measure again.
Epoxy makes that a one-shot. Beyond that, rigid epoxy shrinks on cure and
expands far more than the core does, a pressed powder toroid is brittle, and the
shell traps the heat the core and copper have to shed. **Varnish the winding**
to lock the turns and hold the core with a cable tie, a nylon screw or a printed
saddle. If it must be potted later, use a compliant silicone or soft
polyurethane, after the design measures right.

## The 2 V end is the hard end, and the pre-regulator has to track

60 V is the number that sounds difficult. 2 V is the one that actually is:

```
fixed 40 V rail            drops 38.2 V at 3 A = 114.5 W   to deliver 6 W
tracking, +3 V above out   drops  3.0 V at 3 A =   9.0 W   to deliver 6 W
```

A linear pass stage hanging off a fixed rail is not a thermal design, it is a
heater. The switcher has to **follow the output** a few volts above it, with the
linear stage cleaning up only that last few volts. Dissipation then stays
roughly constant across the whole 30:1 range instead of peaking at the bottom.

## What this does to the enclosure

`bench_supply.scad` was built around one 266 × 153 × 77 switching supply that
ran cool and weighed little. None of that survives:

| | Old box assumed | This needs |
|---|---|---|
| Occupant | one 266 × 153 × 77 supply | **two** 113 × 117 × 70 toroids, plus rectifiers, caps, two converters, two heatsinks |
| Mass | light, on 4 mm standoff pads | **5.8 kg of iron**, each toroid on a single central bolt |
| Floor | 3 mm printed, M4 pads | **now 6 mm** — 3 mm bowed 2.1 mm under 5.8 kg, 6 gives 0.27. Still wants a steel spreader under each bolt |
| Heat | a warm supply | **~100 W** at full output — 64 W converters, 37 W transformers |
| Airflow | one 40 mm fan, lengthwise over a long supply | nowhere near enough |
| Mains | one inlet, 10 A fuse | **5.8 A** draw, and the inrush of two 350 VA toroids. Needs a soft start |

The inlet-on-END-B and the printed mains shield are still good work and the
reasoning behind them still holds — mains at one end, a hood that uses the floor
as the fourth side of its wire slot. **Carry those ideas forward; do not carry
the box forward.**

## Open

- Second ST-1228, or one ~650 VA transformer with two genuinely independent
  secondaries? Two toroids give matched channels and are already half-bought;
  one larger lump is likely cheaper per VA but must not be centre-tapped.
- Soft start: NTC inrush limiter, or a resistor bypassed by a relay.
- Confirm Qg on the chosen FET, and whether `EXTVCC` is fed externally.
- Toroid or a gapped ferrite E-core on a bobbin? The toroid is specified above
  and has the closed flux path, which two converters and a mains filter will
  appreciate. But a bobbin is far easier to hand-wind — you wind it off the
  core — and trims by gap rather than by turns. Worth pricing before committing.
- Whether the VR rig's 36 V bus is simply "channel A set to 36 V" — which is
  regulated, and so removes the overvoltage problem that the raw 28 VAC rail
  created for the 40 V DC-DC module.
