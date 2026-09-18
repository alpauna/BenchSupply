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
```

---

## What it has to be

| | |
|---|---|
| Channels | **2** |
| Range | **2 V to 60 V**, adjustable |
| Current | **3 A** per channel |
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
one channel, 60 V x 3 A  = 180 W out
  -> 212 W DC in at 85%  -> needs 342 VA      against 217 W available: +5 W
both channels            = 360 W out
  -> needs 683 VA                             one 350 VA is 51% of that
```

**So: one transformer per channel.** The margin on a single channel is 5 W,
which is nothing — but it is the right side of zero, and it does not have to
cover both channels at once.

## Isolation comes from the iron, not from the converters

Rectifying one winding twice does not isolate anything. Both outputs still share
the winding, so they cannot be stacked. The barrier has to exist somewhere, and
there are only two places to put it:

| Where | What it costs |
|---|---|
| **In the converters** — two isolated flybacks | custom-wound transformer each, snubber, optocoupler feedback. The hard path |
| **In the iron** — two mains transformers | one more 2.9 kg toroid, and the converters become ordinary non-isolated buck-boosts |

Since 3 A per channel already forces a second transformer for power reasons,
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

## The inductor

Hand-wound, one per channel. At the design point — 29.3 V in, 60 V out, 3 A,
200 kHz — it is **34.6 µH carrying 7.23 A DC with 2.17 A of ripple**, storing
1.19 mJ.

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

### The core: Magnetics Kool Mu toroid, core data 0254, 60µ

| | |
|---|---|
| Core | **Kool Mu toroid 0254** — 40.77 OD × 23.32 ID × 15.37 mm |
| Catalogue | AL **81 nH/T²** at 60µ, Ae **107 mm²**, le 98.4 mm, Ve 10 600 mm³ |
| Permeability | **60µ** |
| Turns | **22** for 34.6 µH at 8.31 A peak — wind 23 and measure |
| Wire | **3 × AWG18** twisted, grade 2 heavy build, Class 180 (H) |

**Use the catalogue's Ae, not the one you can work out from the outside.**
Cross-section from the dimensions gives 134 mm²; the catalogue says **107** —
20 % less, because the rounded edges that stop the core cutting the wire take
real iron away. That error put AL at 100 nH instead of 81 and would have had
this wound at 20 turns instead of 22.

```
  mu     AL    N       H  mu left      dB  bundle max      Cu    P_cu    Emax
  40    54n   27  28.9Oe      87%  25.8mT      2.42mm   1.43m   0.52W   105mJ
  60    81n   22  23.8Oe      85%  31.3mT      2.87mm   1.18m   0.43W    70mJ
  75   101n   20  21.5Oe      84%  34.7mT      3.14mm   1.06m   0.39W    56mJ
  90   121n   19  19.8Oe      82%  37.6mT      3.36mm   0.98m   0.36W    47mJ
 125   168n   16  17.1Oe      80%  43.6mT      3.81mm   0.85m   0.31W    34mJ
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

Energy capacity at 60µ is **70 mJ against 1.19 mJ needed** — 59× — so
saturation is nowhere near the binding constraint. The binding constraint is
loss.

### The wire

```
winding         Cu mm2   bundle      DCR    P_dc    P_ac      J   fits
10 x AWG25       1.62   1.79mm   12.1mR   0.63W     5mW   4.5    yes
5 x AWG20        2.59   2.26mm    7.7mR   0.40W     5mW   2.8    yes
3 x AWG18        2.47   2.21mm    8.1mR   0.42W     6mW   2.9    yes
1 x AWG14        2.08   2.03mm    9.5mR   0.50W    11mW   3.5    yes
```

22 turns leaves room for a bundle up to **2.91 mm** in one layer, which is the
payoff for the bigger core — the drawer core's 15.8 mm hole allowed 1.79 mm.
That headroom is what drops the current density from 4.5 to 2.9 A/mm² and takes
a third off the copper loss for nothing.

**P_ac is milliwatts in every row, including solid AWG14.** The ripple is
0.63 A RMS against 7.23 A of DC — the AC is 9 % of the current, so skin effect
is not what sizes this wire. Strand it because 2.5 mm² of solid copper will not
bend round that hole twenty-two times. Three strands is the fewest that still
handles easily; twist them loosely and treat them as one wire. Cut ~1.2 m per
strand — 22 turns of a 52 mm mean turn is 1.18 m, plus tails and the slack for
the turn you may remove.

### The cores already in the drawer do not work

Worth writing down so it is not re-litigated:

| On hand | Why not |
|---|---|
| "T30-2", measured 24.5 × 15.8 × 12.7 | **T30 is an inch code — 0.30 in = 7.8 mm OD.** The measured core is 3× that in every dimension and 30× the volume, so it is not a T30 of anything. And Micrometals mix 2 is iron powder, not ferrite, so the label contradicts itself |
| …if it is really mix 2 (µ10) | 56 turns needed, 25 fit. µ10 is an RF material, far too low for a 35 µH power inductor in this window |
| …if it is Mn-Zn ferrite (µ~2000), which a 25 × 15 × 12 ring usually is | stores **0.11 mJ** against 1.19 mJ needed — saturates on the first switching cycle |
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
| Floor | 3 mm printed, M4 pads | 3 mm of PETG under 2.9 kg per bolt **creeps**. Wants a steel spreader |
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
- Converter: 4-switch buck-boost controller, or boost-then-buck. Not chosen.
- Toroid or a gapped ferrite E-core on a bobbin? The toroid is specified above
  and has the closed flux path, which two converters and a mains filter will
  appreciate. But a bobbin is far easier to hand-wind — you wind it off the
  core — and trims by gap rather than by turns. Worth pricing before committing.
- Whether the VR rig's 36 V bus is simply "channel A set to 36 V" — which is
  regulated, and so removes the overvoltage problem that the raw 28 VAC rail
  created for the 40 V DC-DC module.
