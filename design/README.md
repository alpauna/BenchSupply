# design

Schematics and BOMs. The reasoning behind every value is in
[`../docs/power-chain.md`](../docs/power-chain.md) and
[`../docs/control.md`](../docs/control.md); the scripts in `../docs/calc/`
reproduce the numbers.

| board | qty | schematic | BOM |
|---|--:|---|---|
| Mains entry, distribution, soft start | 1 | [`schematic-mains.txt`](schematic-mains.txt) | [`bom-mains.csv`](bom-mains.csv) |
| Rectifier and bulk | **2** | [`schematic-rectifier.txt`](schematic-rectifier.txt) | [`bom-rectifier.csv`](bom-rectifier.csv) |
| LT8705 converter | **2** | [`schematic-converter.txt`](schematic-converter.txt) | [`bom-converter.csv`](bom-converter.csv) |

One mains board. One rectifier and one converter **per channel**.

## Before you draw any of it

**The LT8705 pin names in the converter schematic are functional, not
transcribed.** Check them and the pin numbers against the datasheet. That
document is the design intent.

**Confirm Qg on whichever FET you buy.** It is the binding parameter — at 60 V
switching loss beats conduction loss, so a 10 mΩ part carrying 150 nC loses to
a 25 mΩ part carrying 40 nC — and it is the number least reliably quoted in
distributor listings.

**Verify the ADG714 powers up with all switches open.** That is the fail-safe
direction: switches open is 2 V out, and it has to hold when the isolated side
is unpowered, in reset, or being reflashed.

## Three things in here that are structural, not preferences

Each survives a component failure, a firmware hang, or a reflash. None of them
should be "simplified" later without understanding what it is buying.

**The fixed divider branch sets 2 V and the switches only add.** Switches open —
unpowered, in reset, mid-reflash — is minimum output. Wired the other way round,
every one of those states commands 60 V into whatever is connected.

**`RLY_SOFT` is a one-shot, not a level.** It drops out by itself whether or not
`RLY_MAIN` closed, so the 10 Ω soft-start resistor can only ever be in circuit
for one monostable period. Without that, a relay that fails to close leaves it
at 85 W indefinitely.

**Fan 1 is hardwired on.** A box shedding 108 W with no fans because the Pico is
halted, or because someone is reflashing it, is a fire and not a bug.

## What is not here yet

The control board — Pico, opto barrier, fan drivers, 1-Wire sensors, the 5 V
module's connections. Fully specified in [`../docs/control.md`](../docs/control.md),
not yet drawn.
