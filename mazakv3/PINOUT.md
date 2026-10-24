# mazakv3 pinout: 7i92M + 7i77 + 7i76 + 7i70 + 7i71

Converted from the 7i96 + 7i77 config (`../7i96/`) on 2026-10-10.
The card is an original 7i76 (not 7i76U). Its manual is
`mesa card man/7i76man.pdf`, and the terminal numbers below come from it.
The TB2, TB3, TB5 and TB6 layouts are the same as on the 7i76U.

## Firmware

`7i92_7i77_7i76D.bit` from Mesa's `7i92.zip`. Copies of the bitfile and its
`.pin` file are in this folder. The 7i92M is a 7i92 with DB25M connectors and
uses the same firmware. Do not use the 7i92T firmware.

```
sudo apt install mesaflash
mesaflash --device 7i92 --addr 10.10.10.10 --write 7i92_7i77_7i76D.bit
mesaflash --device 7i92 --addr 10.10.10.10 --reload
mesaflash --device 7i92 --addr 10.10.10.10 --readhmid
```

Set the 7i92M IP jumpers for 10.10.10.10, the same as the 7i96.

## Cards

| Card | Connects to | sserial | HAL prefix |
|------|-------------|---------|------------|
| 7i77 | 7i92M **P2** | ch0 I/O, ch1 analog | `hm2_7i92.0.7i77.0.0` / `.0.1` |
| 7i71 | 7i77 expansion port | ch2 | `hm2_7i92.0.7i71.0.2` |
| 7i76 | 7i92M **P1** | ch3 | `hm2_7i92.0.7i76.0.3` |
| 7i70 | 7i76 TB3 RS-422 | ch4 | `hm2_7i92.0.7i70.0.4` |

`sserial_port_0=30010` in `mazakv3.hal` covers all five channels: the 7i77 is in mode 3 (analog in 0–3 plus the MPG counters on inputs 16–19), and the 7i76 is in mode 1 (analog in 0–3 on TB6 pins 1–4, for servo load meters).

## What changed from the 7i96 config

| Signal | Old (7i96) | New | Rewire? |
|--------|-----------|-----|---------|
| X Y Z A B spindle encoders | 7i77, encoder 00–05 | same | no |
| Servo ±10V and enables | 7i77 analog | same | no |
| Home/limit switches | 7i77 inputs | same | no |
| Hydraulic pump | 7i77 output-00 | same | no |
| MPG handwheel | 7i77 enc1 | same | no |
| All 7i71 outputs | ch2 | ch2 | no, if the 7i71 stays on the 7i77 |
| All 7i70 inputs | ch3 | **ch4** | yes: 7i76 TB3 (already done) |
| Carousel, stepgen 00 | 7i96 | 7i76 TB2 STEP0/DIR0 | yes |
| ATC, stepgen 01 | 7i96 | 7i76 TB2 STEP1/DIR1 | yes |
| Shifter, stepgen 02 | 7i96 | 7i76 TB2 STEP2/DIR2 | yes |
| Spindle VFD, stepgen 03 | 7i96 | 7i76 TB2 STEP3/DIR3 | yes |
| Stepgen 04 (spare) | 7i96 | 7i76 TB3 STEP4/DIR4 | — |
| Pallet encoder, encoder 06 | 7i96 encoder | 7i76 TB3 ENCA/ENCB/IDX | yes |
| estop-outcl | 7i96 `ssr.00.out-03` | 7i76 **output-03** (TB6-20) | yes, see below |
| Pallet CCW | 7i96 `ssr.00.out-04` | 7i76 **output-04** (TB6-21) | yes, see below |
| Pallet CW | 7i96 `ssr.00.out-05` | 7i76 **output-05** (TB6-22) | yes, see below |

### Moving the SSR outputs

The 7i96 SSRs were isolated switches, so they could switch any circuit in
either polarity. The original 7i76's outputs are **sourcing only**: when on,
the output supplies field power (TB1 VFIELD), so the load connects between the
output and field ground. The limit is **300 mA** per output.

Before wiring, check what each of these three outputs drives: the estop
chain and the pallet motor contactor or relay. A load that is not 24V DC, that
needs a dry contact, or that draws more than 300 mA needs an interposing
relay.

## 7i76 connections

| Terminal | Use |
|----------|-----|
| TB1 | field power 24V (VFIELD and VIN) |
| TB2 1–5 | carousel STEP0/DIR0 |
| TB2 7–11 | ATC STEP1/DIR1 |
| TB2 13–17 | shifter STEP2/DIR2 |
| TB2 19–23 | spindle VFD STEP3/DIR3 |
| TB3 7/8, 10/11, 13/14 | pallet encoder A, B, index |
| TB3 16–19 | RS-422 to the 7i70 |
| TB6 20 / 21 / 22 | outputs 3 / 4 / 5: estop-outcl, pallet CCW, pallet CW |

All 32 field inputs and the other 13 outputs are free.

## Check on first power-up

1. `dmesg | grep -i hm2` should show the 7i77 on ch0 and ch1, the 7i71 on
   ch2, the 7i76 on ch3 and the 7i70 on ch4.
2. `halcmd show pin hm2_7i92.0.7i76` and `halcmd show pin hm2_7i92.0.7i70`
   should both list pins.
3. If a remote is missing, the cables were probably plugged into the other
   ports. To swap the 7i70 and 7i71, run:
   `sed -i 's/7i70\.0\.4\./7i70.0.2./g; s/7i71\.0\.2\./7i71.0.4./g' *.hal`

