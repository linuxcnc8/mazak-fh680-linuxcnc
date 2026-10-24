# mazakv2 pinout — 7i97 + 7i76

Converted from the 7i96 + 7i77 config on 2026-08-10.
Anything marked **CHECK** has not been confirmed against real hardware.

## Cards

| Card | Where | sserial | Provides |
|------|-------|---------|----------|
| 7i97 | main, 10.10.10.10 | — | 6 encoders, 6 ±10V analog out + 6 enables, 16 isolated in, 6 SSR out |
| 7i70 | 7i97 TB4 RS-422 | `0.0` **CHECK** | 48 isolated inputs (unchanged) |
| 7i76 | 7i97 P1 expansion (DB25) | `0.1` **CHECK** | 5 step/dir, spindle encoder in, 32 field in, 16 field out |
| 7i71 | 7i76 RS-422 expansion | `0.2` **CHECK** | 48 isolated outputs (unchanged) |

Three remotes means channels 0, 1 and 2 — the old 7i77 took two channels on
its own and is gone. The order above assumes the firmware declares the main
card's TB4 port before the P1 daughtercard. `mazakv2.hal` carries a one-line
`sed` command to swap to the other order if dmesg says otherwise.

## 7i97 analog drive interface (TB3)

| Channel | HAL | Axis |
|---------|-----|------|
| AOUT0 / ENA0 | `pwmgen.00` | X — joint 0 |
| AOUT1 / ENA1 | `pwmgen.01` | Y — joint 1 |
| AOUT2 / ENA2 | `pwmgen.02` | Z — joint 2 |
| AOUT3 / ENA3 | `pwmgen.03` | A — joint 3 |
| AOUT4 / ENA4 | `pwmgen.04` | B — joint 4 |
| AOUT5 / ENA5 | — | spare |

There is no analog spindle output — the spindle is step/dir on `stepgen.03`.
The wiring for an analog spindle reference on AOUT5 is left commented out in
`mazakv2.hal` in case it is ever wanted.

ENA0–ENA3 share a common; ENA4 and ENA5 switch independently.
All six run offset mode + dither at 96 kHz, which is what Mesa specify for
LinuxCNC 2.9.2 and later. Each `pwmgen.NN.enable` now drives its own ENA
output — on the 7i77 a single `analogena` gated all six at once.

## 7i97 encoders (TB1 = 0–2, TB2 = 3–5)

| Encoder | Use |
|---------|-----|
| 00 | X |
| 01 | Y |
| 02 | Z |
| 03 | A |
| 04 | B |
| 05 | spindle |

All six are used. **CHECK** — everything past encoder 05 depends on the
firmware bitfile:

| Encoder | Use |
|---------|-----|
| 06 | pallet, on the 7i76's spindle encoder input |
| 08 | MPG handwheel (MPG1 = isolated inputs 2/3) |

## 7i97 isolated inputs (TB4 IN0–7, TB5 IN8–15)

| Input | Use |
|-------|-----|
| IN0 | estop — `gpio.000.in` **CHECK** the gpio index |
| IN2 / IN3 | MPG handwheel A/B (MPG1) |

IN0–IN7 double as four MPG quadrature encoder inputs
(MPG0 = IN0/1, MPG1 = IN2/3, MPG2 = IN4/5, MPG3 = IN6/7).
Because estop sits on IN0, MPG0 is unusable and the handwheel goes on MPG1.

## 7i97 isolated outputs (TB5)

Unchanged from the 7i96's SSRs — same HAL names, same numbers.

| Output | Use |
|--------|-----|
| `ssr.00.out-03` | estop-outcl |
| `ssr.00.out-04` | pallet CCW |
| `ssr.00.out-05` | pallet CW |

## 7i76 step/dir

Same stepgen instance numbers as the 7i96 had, so nothing in
`1extrajoint.hal` or `spindle_stepgen.hal` needed renumbering.

| Stepgen | Use |
|---------|-----|
| 00 | carousel — joint 5 |
| 01 | ATC — joint 6 |
| 02 | shifter — joint 7 |
| 03 | spindle VFD (untested, see `spindle_stepgen.hal`) |
| 04 | spare |

## 7i76 field inputs — proposed, needs wiring to match

| Input | Use |
|-------|-----|
| input-00 | X home |
| input-01 | Y home |
| input-02 | Z home |
| input-03 | A home |
| input-04 | X limit (both ends) |
| input-05 | Y limit (both ends) |
| input-06 | Z limit (both ends) |

All are used inverted (`-not`), same as they were on the 7i77.

## 7i76 field outputs

| Output | Use |
|--------|-----|
| output-00 | hydraulic pump / machine-is-on (was 7i77 output-00) |

## Unchanged — 7i70 inputs (now sserial ch 0, was ch 3)

01 pallet up · 02 pallet top · 03 arms to pallet · 04 arms to home ·
05 pallet bottom · 07 pallet middle · 09 carousel home · 10 ATC home ·
11/12 ATC tool pos 1/2 · 15 shifter home · 16/17 shifter clamped/unclamped ·
18/19 tool clamped/unclamped · 25 (was A home, now free) ·
32/33/34 MPG axis select · 35/36 MPG scale · 47 (was estop, now free)

## Unchanged — 7i71 outputs (sserial ch 2)

01 spindle tool unclamp · 02 (set 1) · 03 arms up · 04 arms to pallet ·
06 lube · 08 (set 1) · 09 shifter clamp · 10 shifter unclamp
