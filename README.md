# BenchSupply

A printed box for the bench supply that feeds the ECU and the VR test rig:
screw-down lid, 40 mm fan at one end, exhaust grid at the other, and a fused
IEC C14 inlet/switch module on the end wall beside that grid, its terminals
under a printed shield. A small **two-rail DC-DC module** has the long wall to
itself, fed from the 36 V supply inside — its fixed 5 V runs the
VR rig's Pico, its adjustable rail is a bench output.

**Forked from [`TritonECU/hardware/psu-enclosure`](../TritonECU/hardware/psu-enclosure) — this is the copy to grow.**
The two are still identical geometry: the DC-DC landed in **both**, because it
is part of the working box rather than speculative growth. `psu-enclosure` is
the version that stays printable; changes for the wider bench live here, so the
working enclosure is never in pieces. Diverge freely — from here on, expect to.

> **The supply this box was built around is being replaced.** It is going to a
> **toroidal transformer** and two isolated 2–60 V / 3 A channels, which is a
> different machine: two 2.9 kg toroids instead of one light switcher, ~100 W of
> heat instead of a warm box, and 5.8 A of mains with the inrush of two 350 VA
> transformers. **Do not print the tub from this file expecting it to hold that.**
> The reasoning is in [`docs/power-chain.md`](docs/power-chain.md); everything
> below still describes the box as drawn, which is correct for the old supply.

**This box contains mains wiring.** Read [Safety](#safety) before energising it.

## Room already in it

The box was sized generously on purpose. **The DC-DC is the first thing to take
any of that slack**, and it took less than it looks: 84 mm of the bay wall, and
depth only where its boss steps out.

| Where | Free space | Good for |
|---|---|---|
| Bay wall, between DC-DC and gland | **60 mm** of flat wall (x 106–166) | the largest unbroken panel span |
| Bay wall, past the gland | **90 mm** (x 194–282) | the mains has left this wall entirely — it is all low voltage now |
| Bay wall, END A end | 19 mm before the DC-DC | small stuff only |
| Wiring bay, volume | **50 mm** wide × 279 long, less the DC-DC's 84 and the shield's 32 at END B | terminal blocks, DC distribution |
| Over the supply | 2 mm to the rim taper, 17 mm to the lid | nothing tall — raise `head` if you need a shelf |
| Fan-end plenum | 10 mm × 195 × 98 | the air path. Do not fill it |
| The lid | untouched | a flat 285 × 212 plate; panel-mount anything to it |
| END A | the LV gland only | the rest of that wall is the fan and the plenum |
| END B | **full** | grid in the supply's shadow, inlet in the bay corner. Nothing left |

**A buck module for the fan is no longer on that list** — the DC-DC covers the
role, but *not* on its adjustable rail. See [The fan is not a load for the
adjustable rail](#the-fan-is-not-a-load-for-the-adjustable-rail).

The honest constraint is **height**, not floor area. `head` is 2 mm, so there is
no usable layer above the supply until you raise it — and every mm you add there
adds a mm to the outside.

**The X growth cap has moved.** This was written against a 300 bed, which put
the ceiling at about 290 including the pads — right where the tub already sits.
The printer is now a **QIDI X-Plus 5: 320 × 320 × 300**, read from
`Qidi X-Plus 5 0.4 nozzle.json` in QIDIStudio 02.07.02.60. Against the tub's
current 294 × 212 that is **26 mm spare in X and 108 in Y**, so X is no longer
the axis that stops you — height still is, and it is the one axis the bed does
not help with.

```
                 TOP VIEW  (285 long)

     END A                                      END B
   +--------------------------------------------------+
   |[FAN]                                       ######|
   |         power supply  266 x 153 x 77       ######|  <- exhaust grid
   |   intake -->  air over and under  -->  out ######|
   |------------------------------------------- -----+
   |(LV)           50 mm wiring bay          [SHIELD]|[PLUG]
   +--------[ DC-DC ]------------[GLAND]-------------+
        5 V + adj                 36 V out
```

The mains lives at **END B only** now — inlet on the end wall beside the grid,
its terminals inside a printed shield that stands on the floor. The whole long
wall is low voltage: see [the inlet and its
shield](#the-inlet-moved-to-end-b--and-brought-a-shield).

## Dimensions

| | |
|---|---|
| External | **285 × 212 × 106** mm |
| Bed footprint, tub | **294 × 212** — the fan pad and the plug pad stand proud of the ends; the long walls are flat |
| Bed footprint, lid | 285 × 212 |
| Clear space for the supply | **279 × 156 × 79** (the 266 × 153 × 77 minimum, with room) |
| Wiring bay | **50 mm** wide alongside the supply, clear end to end |

`openscad` echoes all of these on every render, so they follow the parameters
rather than this table. Re-read them after changing anything.

**The tub needs a genuine 300 × 300 bed**, with 5 mm to spare on each side in X.
Print it with a *skirt*, not a brim — a brim will not fit. If your printer
cannot reach 290, drop `clr_fan` from 10 to 6 and re-render; you lose plenum
depth at the fan and nothing else.

## Measure these before printing

The `.scad` is parametric but it cannot guess:

```
psu_l, psu_w, psu_h    the supply's real outside dimensions
standoff_xy            the supply's mounting-foot pattern
mod_cut_w/h, mod_depth the DC-DC module's body, and how far it stands behind
mod_flange, mod_lock_w its bezel lip and its snap locks
mod_boss               which is a DECISION, not a measurement — see below
```

The supply's dimensions default to the 266 × 153 × 77 minimum. **The foot
pattern has no default worth trusting** — there is no standard for it. The six
standoffs as shipped are *pads*: they hold the supply 4 mm off the floor so air
can get under it, and that is all they do. Measure the feet, edit
`standoff_xy`, then set `standoff_hole = true` to get M4 clearance holes with
head recesses on the underside of the floor.

The `mod_*` defaults are the module actually in hand — **64 × 38.5 × 25.4 behind
a 4 mm flange, with two 12.7 mm snap locks centred on the vertical edges.**
Measure yours. Every clearance on that wall that was tight enough to be worth
arithmetic is an `assert` in the `.scad`, so a wrong number stops the render
rather than the print.

## Bought parts

| Qty | Item | Notes |
|--:|---|---|
| 1 | **40 × 40 × 10 mm fan**, 12 V | 32 mm bolt centres, Ø3.5 holes — the WINSINN drawing |
| 1 | **IEC C14 inlet + rocker + fuse module** | BIQU 10 A 250 V; 58 × 48 face, 50 × 29 × 19 rear flange, M3 ears at 40 mm |
| 1 | 5 × 20 mm fuse | size it to the supply, not to the socket's 10 A rating |
| 10 | **M3 × 12 socket head** | lid |
| 4 | **M3 × 10 self-tapping** | fan, through its own Ø3.5 holes into the pad |
| 2 | **M3 × 12 self-tapping** | plug ears, into the 7 mm pad |
| 4 | M4 × 10 | supply feet, *once you have measured them* |
| 1 | **PG7 cable gland** or Ø12.5 rubber grommet | 36 V DC output, bay wall |
| — | 16–14 AWG wire + insulated spade terminals | the inlet module ships with a set |
| 4 | Stick-on rubber feet | the floor is flat by design |
| 1 | **DC-DC module, two rails** — fixed 5 V + LCD-set adjustable | 64 × 38.5 face, 25.4 deep, 4 mm flange, snap-lock mount. **40 V DC input rating** — confirmed, against a 36 V bus. See below |
| 1 | **Fuse + holder, 1–2 A**, inline | the 36 V tap to the DC-DC. *Not optional* — see below |
| 1 | **PG7 cable gland** or Ø12.5 grommet | low-voltage output, END A wall |
| 1 | **Schottky, 1 A** (1N5819 or similar) | in the 5 V feed to the Pico's `VSYS` |
| — | 20–22 AWG wire, **two colours** | the 5 V pair and the adjustable pair, kept tellable apart |
| 2 | **M3 × 10 self-tapping** | the mains shield, into its two floor posts |

## Printed parts

| Qty | Part | Orientation |
|--:|---|---|
| 1 | `tub` | **floor down**, open side up |
| 1 | `lid` | **outer face down** — see below |
| 1 | `shield` | **on its back** — the flat face that carries the wire slot, down on the bed |

**Print the lid upside down, outer face on the bed.** Modelled ribs-down as it
sits on the box, so flipping it makes every rib and the locating ring grow
*upward*. Nothing then overhangs except a 1.5 mm annular bridge over each screw
counterbore, which any printer manages. Printed the other way up, four ribs and
a 250 mm ring are all overhang.

**PETG or ABS, not PLA.** This one is not about stiffness — it is that the box
holds a warm supply and a mains connection, and PLA softens at temperatures a
loaded supply reaches in a closed box.

Walls and floor are 3 mm; 3 perimeters and 25 % infill is plenty. The lid wants
**4 perimeters** so the screw counterbores have solid material around them.

## How it is put together

### The lid seat is a rim band, not corner posts

With 3 mm of clearance beside the supply there is nowhere to put a corner post —
it would land inside the supply. So the screws go into a band that thickens the
wall inward around the whole top rim, sitting **entirely above the supply**
where the volume is free anyway. It costs 17 mm of height and no floor area.

The band's underside is a 45° taper (`rim_taper = rim_w`, keep them equal), so
it prints with no support and leaves no drooping ledge over the supply. Its
inner face is the rabbet the lid's locating ring drops into, which is what stops
the lid sliding and closes the dust gap.

Ten M3s: four along each long wall, one at each end.

### The fan mounts outside

Inside would cost 10 mm of a 10 mm plenum, and the supply is only 10 mm away.
The pad on the outside also gives the M3s **8 mm of plastic** to cut into
instead of 3.

**Mount it as an intake** — airflow arrow and label pointing *into* the box. Air
enters at END A, splits between the 4 mm gap under the supply and the space over
it, and leaves through the grid at END B. Blowing the length of the supply is
the whole reason the fan and grid are on opposite ends rather than opposite
sides. Run the fan off the supply's own DC output if the voltage matches, or off
a small fixed buck of its own — **not** off the DC-DC's adjustable rail, for the
reason in [The fan is not a load for the adjustable
rail](#the-fan-is-not-a-load-for-the-adjustable-rail).

### The grid is diamonds, not squares

A square hole in a vertical wall has a flat top edge that has to bridge. A
diamond has an apex, so every one of the 78 holes is self-supporting and nothing
droops into the airstream.

### The bay is still why things fit — just not the plug any more

The bay was originally sized by the inlet: its rear flange stands **19 mm**
proud of the panel, the spade terminals and their boots add more, and none of
that can happen on the wall the supply is pressed against. So a channel ran down
one long side.

**The inlet has since moved to END B**, and the bay stayed — because two other
things now need it. The DC-DC is 25.4 mm deep behind its panel, and the mains
shield is 44 mm wide. The shield is the binding one: 29 mm of flange, clearance
for booted spades either side, a wall each side, and a 39 mm bay cannot hold it
at any sane wall thickness.

At **50 mm** the shield fits with 3 mm a side, and the DC-DC gets 24.6 mm behind
it on a flat wall — so `mod_boss` went to **0** and the bump on the outside of
that wall disappeared. The box grew 11 mm in Y and lost a 12 mm boss, and the
plug pad moved from the Y face to the X face: **the bed footprint went from
290 × 213 to 294 × 212, which is no change worth the name.**

`gland_x` is a parameter. Slide it along the wall to land beside the supply's
own DC output terminals — but keep it clear of the shield, which owns the END B
end of the bay. The `.scad` asserts that for you.

## The inlet moved to END B — and brought a shield

### There is exactly one place on END B it can go

Not a free choice. Everywhere along END B the supply sits **3 mm** behind the
wall, and 12 mm of intruding flange plus 12 mm of booted terminals cannot live
in 3 mm. The one exception is the bay's corner, where the channel runs past the
end of the supply and there is depth all the way down the box.

The exhaust grid occupies the supply's shadow — exactly the part of that wall
the inlet cannot use — so the two do not compete. The inlet sits beside it.

### And it sits low, which is the shield's doing

The shield **stands on the enclosure floor** and uses that floor as the fourth
side of its wire slot. That only works if the terminals are near the floor, so
`plug_z` is **36**, putting the flange between z 11 and 61 and leaving 8 mm of
shield underneath for the wires to turn in.

It is still mounted **58 mm axis vertical**, so the rocker is at the top and the
fuse drawer pulls out below it. One consequence of the move: the M3 ears are at
40 mm centres, which is **wider than the 50 mm bay minus its walls**, so they no
longer land in the bay — they land in the solid wall either side of it. That is
fine, and it is why `plug_pad_y` has to stay inside the box: the pad is a slab
on the *outside* of END B, and running it past the corner leaves it hanging in
mid-air with no wall behind it. The `.scad` asserts that too.

### The shield: two open faces, and a slot that is open at the bottom

The inlet's spade terminals are the only exposed mains inside this box. With the
lid off they are a finger away. The shield covers them.

It is a cup with **two open faces**: the one against the END B wall, where the
inlet comes through, and the **bottom**, where it stands on the floor.

**The wire slot is the whole point of the shape.** The three spades are crimped
and booted *before* the shield goes anywhere near them, so the wires cannot be
threaded through a closed hole — a closed hole would mean stripping the
terminals off again to fit the cover. So the slot runs off the bottom edge of
the back wall: **three of its sides are printed into the shield, and the fourth
is the enclosure floor** once the shield is screwed down. Lay the booted wires
in, drop the shield over them, put two screws in.

The slot is **26 × 14**, which takes three booted spades side by side.

### Assembly order matters now

**Fit the inlet and drive its two ear screws before the shield goes on.** The
shield covers the back of the inlet completely; once it is down, those screws
are unreachable without taking it off again. Same for the spade terminals —
crimp, boot and seat them all first.

### Print it on its back

Laid with the slotted back face on the bed, every other wall of the shield is
perpendicular to the bed. **There is not one overhang in the part** — no
supports, no bridges, and the slot comes out as a clean rectangular notch rather
than a sagging hole.

## The second supply — a DC-DC module, not a second mains supply

The box gained a second output stage: a two-rail DC-DC with an LCD, panel
mounted at the END A end of the bay. **It is fed from the 36 V supply already in
the box, not from the mains.** That is what makes it a cheap addition — no
second inlet, no second cord, and no more live terminals in a box that already
has a set. Everything it does still sits downstream of the C14's fuse.

| rail | what it is for |
|---|---|
| **fixed 5 V** | the VR rig's Pico, and the DM542's `PUL+ / DIR+ / ENA+` commons |
| **adjustable** | set from the LCD; a bench rail, out through the same gland |

### 40 V in, on a 36 V bus — which makes it the weakest part on that bus

**The module is rated 40 V DC in.** Against 36 V that is 4 V of headroom, about
11 %, and in steady state it is fine: an open-frame supply regulates to a
percent or so and never goes near the ceiling. (Worth saying because most
modules this size stop at 32 V, which this supply would destroy on the first
switch-on. This one clears it.)

What the rating changes is *which part fails first*. The DM542 is rated **50 V**.
The DC-DC is rated **40**. **The lowest-rated thing on the 36 V bus is now the
supply the Pico runs on** — so an excursion that used to threaten only the
driver now takes out the 5 V rail first, and the step generator with it.

That excursion is already documented: [ramp the
decelerations](../TritonECU/hardware/vr-test-rig/BOM.md#ramp-the-decelerations--capacitance-cannot-fix-a-hard-stop).
A switching supply cannot sink current, so a hard stop dumps the wheel's energy
into whatever capacitance is on the bus and drives it to 64–120 V. That ramp was
load-bearing before. It is more so now, against a ceiling 10 V lower.

Two things follow:

- **Do not touch the supply's V-ADJ trimmer.** Open-frame supplies commonly trim
  ±10 %, and +10 % of 36 is **39.6 V** — 0.4 V from the module's absolute
  maximum, before any transient at all.
- The 1000 µF at the driver's `V+` is now insurance for the DC-DC as well as for
  the driver. Fit it.

#### And a TVS cannot cover the gap

The reflex is to clamp the bus. It does not work here, and the reason is
arithmetic rather than taste: the part would have to stand off 36 V without
conducting **and** clamp below 40 V, and nothing does both. The lowest standard
device that stands off 36 V is an `SMBJ36A` — breakdown **40.0–44.2 V**,
clamping at **58.1 V**. Its breakdown tolerance alone is wider than the whole
4 V margin: at one end of the spread it begins conducting at the module's
ceiling, and it does not clamp hard until 18 V past it.

The window between 36 V working and 40 V absolute maximum is too narrow for a
transient suppressor to live in. **The ramp is the mitigation; there is no
component to buy instead.**

### Fuse the tap

The 36 V supply will put **10 A into a fault** and has no idea it is a fault.
Put a **1–2 A fuse in the tap**, at the supply's terminal end so it protects the
wire and not just the module. The C14's fuse is sized for the whole supply and
will never notice a shorted DC-DC — which is a fault inside a plastic box.

### The Pico goes on `VSYS`, not `VBUS`

The Pico's **`VBUS` pin is the USB connector's 5 V, directly.** Feeding it means
back-feeding the host's USB port. Use **`VSYS` (pin 39)**, with GND on pin 38 —
that is what the datasheet provides for exactly this. USB reaches `VSYS` through
the on-board Schottky `D1`, so a cable can stay plugged in for programming: `D1`
reverse-blocks and nothing flows back into the port.

Put a **Schottky in the feed** as well, so the module is protected in the other
direction too. 5 V less the drop lands `VSYS` near 4.7 V, comfortably inside its
1.8–5.5 V range.

The part that is an *improvement* rather than a change: `PUL+ / DIR+ / ENA+`
come off this same 5 V rail. [The VR rig BOM](../TritonECU/hardware/vr-test-rig/BOM.md) used to
take them from the Pico's `VBUS`, which meant **the driver's opto commons died
the moment the USB cable was unplugged.** On this rail they do not.

The module's 5 V return, the Pico's GND and the 2N7002 sources are one node.
Run the 5 V and its return out as a **pair**.

### Star the ground — it is no longer floating

The optos were never isolating the Pico from the motor supply in the first
place: `PUL+` and `PUL−` are both in the Pico's domain and the barrier is inside
the driver. What changes is the **reference**. A non-isolated buck ties the
Pico's ground to the 36 V supply's negative, which is also the DM542's return —
and 2 A/phase of chopper current flows in that return.

So take the module's input **from the supply's own output terminals**, not
daisy-chained off the DM542's `V+ / V−` screws. Then the motor's return current
never flows through a conductor the Pico's ground shares, and the ripple stays
where it belongs.

One consequence worth knowing about: with the Pico's ground tied to the supply
negative, a USB cable to a PC now joins the PC's ground to it as well. That path
did not exist before.

### The fan is not a load for the adjustable rail

Tempting — the fan wants 12 V, this page used to hand-wave "a small buck module
in the bay", and there is now a rail in the bay that can be set to 12.
**Don't.** It would put the cooling on a knob, in a box whose airflow depends
entirely on that fan and which holds a warm supply and a mains connection. Give
the fan its own fixed source and leave the adjustable rail free.

### Label the two pairs at the gland

Two wire pairs leave the same gland and one of them can be at 30 V. **Two
colours, and a label at both ends.** Swapping them puts the adjustable rail on
the Pico's `VSYS`.

### It sits in still air

The fan blows END A to END B *over and under the supply*; the bay is off to one
side and barely sees it. At the load this rail was added for — a Pico and three
optos, call it 100 mA at 5 V, well under a watt — that does not matter. Start
pulling amps from the adjustable rail and the module wants a heatsink, because
the bay will not cool it.

## How the DC-DC is mounted

### It hangs on its own snap locks

Two tapered locks, one on each **vertical edge** of the cutout, 12.7 mm long,
centred. They start about 1 mm behind the bezel and taper back 3, so they grip a
panel **1 to 4 mm thick**. A 3 mm wall is right at the far end of that taper —
a loose grip on a module standing 25 mm off the panel — so the panel is
**thinned to 2 mm** over a patch reaching 6 mm past the cutout all round.

That relief is cut on the **inside** face. The outside stays flat, so the bezel
lands on plain wall and none of it shows.

Nothing else holds the module: no screws, no brackets. The cutout's left and
right edges are the only surfaces carrying it, so keep them clean and do not put
anything else on them. Printed floor-down they are vertical walls and come out
crisp — but test-fit the module before you wire anything to it.

### The panel is flat — the boss is gone

It was not always. When the inlet shared this wall the bay was 39 mm, the module
is 25.4 deep, and that left 13.6 mm for its terminals and the bend in the wire —
not enough if they exit straight back, which on these modules they usually do.
The panel sat on a boss that stepped **12 mm outward** to buy 25.6 mm.

Moving the inlet to END B forced the bay to 50 for the shield, and **50 − 25.4
is 24.6 mm on a flat wall** — as much as the boss ever bought. So `mod_boss` is
**0**, the bump is gone, and the long wall is flat from end to end.

Raise `mod_boss` again if you ever narrow the bay; the geometry is still there
and still drafted at 45°. The render asserts you have left enough room either
way.

### Why END A, and why the output leaves on the end wall

Three things now share the bay wall, and the order is deliberate: **low voltage
at END A, mains in the middle, 36 V DC at END B.** The DC-DC's output gland is
on the **END A wall**, not the bay wall, so the 5 V and adjustable pairs never
run the length of the bay toward END B, where the mains now is.

`mod_x` slides the module along the wall as `gland_x` does — and the `.scad`
asserts it clears both the gland and the ends, so a bad value stops the render.

## Safety

The box is plastic, so there is nothing to bond to earth — but the C14's earth
pin still has to go somewhere. **Run it to the supply's earth terminal.** Do not
leave it unconnected because the enclosure is non-conductive; the supply's
chassis and its output reference need it.

- The lid screws are the only thing between a finger and 120 V. Fit all ten.
- Fuse for the *supply*, not for the socket. The inlet module is rated 10 A;
  that is a ceiling, not a recommendation.
- Use the insulated spade terminals the inlet module ships with, fully seated.
- Fit the cable gland or grommet before pulling the DC output wires through. A
  bare printed hole will cut insulation over time, and the layer lines make it
  worse than a drilled one.
- Strain-relieve the mains wiring inside the bay so a tug on the cord cannot
  reach the terminals.
- **Fit the shield.** It is the only thing between a finger and the inlet's
  terminals once the lid is off, and it is two screws. Fit the inlet and drive
  its ear screws *first* — the shield covers them.
- **Fuse the DC-DC's 36 V tap at 1–2 A.** A shorted module on a 10 A supply is
  an ignition source, and the C14 fuse is far too big to see it.
- Keep the DC-DC's wiring at the END A end of the bay, clear of the inlet's
  spade terminals. That separation is why the module and its gland are where
  they are; do not undo it by routing the low-voltage pairs past the plug.

## Rendering

```bash
./render.sh          # all three parts to stl/
```

Or one at a time:

```bash
openscad -D 'part="tub"' bench_supply.scad
openscad -D 'part="lid"' bench_supply.scad
openscad -D 'part="shield"' bench_supply.scad
```

`part = "assembly"` (the default when you open the file) shows the tub, the lid
in place, the shield in **red**, and **ghosts** of the supply, the fan, the
DC-DC and the inlet. The inlet ghost is the one to look at: its terminal block
is what the shield has to swallow, and what sets the bay width.

STL export is not byte-deterministic — rendering the same unchanged file twice
produces different files. **`bench_supply.scad` is the source of truth**; the
STLs are a convenience so the parts can be printed without installing OpenSCAD.
Re-run `render.sh` after any change and do not read anything into the diff.

## Parameters worth knowing

| Parameter | Default | What it moves |
|---|--:|---|
| `psu_l/w/h` | 266/153/77 | everything — **measure yours** |
| `standoff_xy`, `standoff_hole` | pads, off | the supply's foot pattern |
| `clr_fan` | 10 | plenum depth at the fan end, and total length |
| `bay_w` | 50 | wiring channel; the **shield** needs most of it now |
| `rim_w`, `rim_taper` | 6, 6 | lid seat. **Keep them equal** — that is the 45° |
| `boss_d` | 9 | lid screw engagement. Heat-set inserts? 7 is enough |
| `lid_screw` | 2.6 | M3 self-tapping pilot. Heat-set M3 insert: **4.2** |
| `fan_guard` | true | concentric webs over the fan bore |
| `plug_y`, `plug_z` | bay centre, 36 | where the inlet lands on END B. **Low, so the shield reaches the floor** |
| `gland_x` | −105 | where the 36 V output leaves the bay wall |
| `bay_w` | **50** | set by the shield now, not the plug |
| `sh_clr`, `sh_wall` | 5, 2.5 | shield clearance round the terminals, and its wall |
| `sh_notch_w/h` | 26, 14 | the wire slot. Its fourth side is the floor |
| `sh_tab_z` | 20 | screw tabs, high enough to clear the slot |
| `grid_pitch`, `grid_sq` | 10, 6 | exhaust open area |
| `mod_cut_w/h`, `mod_depth` | 64/38.5, 25.4 | the DC-DC's body — **measure yours** |
| `mod_boss` | **0** | how far the DC-DC's panel steps out. 0 = flat wall; changes the box |
| `mod_panel_t` | 2.0 | panel at the cutout. The snap locks grip 1–4 |
| `mod_x` | 64 | where the DC-DC lands along the bay wall |
| `mod_relief_m` | 6 | how far the thinned panel reaches past the cutout |
