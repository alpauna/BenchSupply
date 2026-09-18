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
| Control - Pico, fans, sensors, UI | 1 | [`schematic-control.txt`](schematic-control.txt) | [`bom-control.csv`](bom-control.csv) |

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

## Where the optocouplers live

**On the converter boards, not on the control board.** Every signal leaving the
control board is Pico-referenced, including the LED drive going out and the
phototransistor collector coming back — the isolation happens at the far end.

Put them on the control board instead and it would carry **three** isolated
domains — Pico, channel A, channel B — with barrier slots between them. There is
no reason to.

## What is not here yet

Nothing. All four boards are drawn. What remains before layout is the
[layout spec](../docs/) — net classes, trace widths, hot-loop targets — and
confirming the three items above.
