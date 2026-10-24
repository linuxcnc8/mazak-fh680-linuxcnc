# LinuxCNC upgrade notes - mazakv3

Things to check or undo when LinuxCNC is upgraded from **2.10.0~pre1**
(the current install, built locally from source in May 2026 - there are no
saved pre1 .debs; `dpkg-repack` them first if you want a way back).

## 1. Abort hang workaround (quick prepare ack) - 2026-10-24

**The bug (2.10.0~pre1):** iocontrol now runs inside milltask. Its abort
clears `tool-prepare` / `tool-change` but leaves task's IO status at
"busy". Abort while a T prepare (magazine fetching) or an M6 is pending, and
task stays in exec_state 7 (waiting for motion and IO):

- program runs and MDI hang ("running" but nothing happens)
- switching to Manual (F3) is slow, because AXIS waits for task
- Stop doesn't clear it - only a restart does

Fixed upstream: commit `990cb293bd` (2026-05-16, "task: set io.status=DONE
on emcIoAbort to unblock tool-change abort", issue #3675), included in
**v2.10.0-pre2**.

**The workaround (pending-prepack/):** `mag.0.io-prepared` answers
iocontrol's `tool-prepare` immediately. The mag latches the request and
fetches as before. `mag.0.tool-prepared` (the real "pot ready") still goes only
to the atc and the panel, and the atc won't swap until the right pot is at the
change position.

- Side effect: a T no longer blocks the program. The fetch runs while
  the program carries on.
- Part 2 (pending-m6wait/): the M6 remap (`sub_progs/toolchange.ngc`)
  waits for the pot with `M66 P14 L3 Q1` in a loop on `motion.digital-in-14`
  (= `mag.0.tool-prepared`) **before** calling the built-in M6. Without it,
  the program went straight into the built-in M6 and waited there, so an
  Abort hung task anyway. An Abort during the M66 wait is safe. The loop
  stops with an abort message if the magazine faults.
- An Abort during the actual swap (built-in M6 running) can still hang task -
  restart.

After the upgrade the M66 wait can stay (it's harmless and still lets
positioning overlap the fetch).

**After upgrading LinuxCNC (fix included), to undo it:** in `toolchanger.hal`,
replace

```
net tool-prepared mag.0.tool-prepared
net tool-prep-ack mag.0.io-prepared => iocontrol.0.tool-prepared
```

with

```
net tool-prepared iocontrol.0.tool-prepared mag.0.tool-prepared
```

`mag.0.io-prepared` is then unused and can stay in the comp. The latch works
either way. Keeping the workaround after the upgrade is also fine. It just
keeps the "fetch while the program carries on" behaviour.

**Test after the upgrade:** run a program, abort while the magazine is
fetching, then run again and switch to Manual. Neither should hang.

## 2. Recompile the custom comps

The pre2 sources have HAL API changes, so rebuild every custom comp against
the new headers (LinuxCNC closed).

**pre2 comps can't assign to pins or params any more.** `pin = x;` fails with
"lvalue required as left operand of assignment". Writes must be `pin_set(x);`
(reads are unchanged). The five comps were ported on 2026-10-25 by
`pending-pre2comps/conv.py`. `rev.py` turns them back and checks the result
is identical to the pre1 source. `pending-pre2comps/orig/` holds the pre1
versions, which `pending-linuxcnc-pre2/rollback.sh` puts back. The "Old type
'bit'/'float'" warnings are harmless. Python `hal.HAL_BIT/HAL_S32/HAL_FLOAT`
still work, but give FutureWarnings (new names: `hal.HAL_BOOL/HAL_SINT/HAL_REAL`).

Commands:

```
cd comp && for c in atc mag drawbar; do sudo halcompile --install $c.comp; done && cd ..
sudo halcompile --install spindle_orient.comp
sudo halcompile --install ../pallet.comp          # configs/mazak/pallet.comp
```

`prod_counter.so` (source: `configs/cnc_lathe_2/prod_counter.comp`) is used by
the lathe config, not this one - rebuild it too if the lathe runs on this PC.

## 3. Other things to re-check after an upgrade

- `pushmsg`: a long `msgs=` line crashed rtapi_app at startup on pre1 (it
  loads fine in halrun). Keep messages short with no commas, and test a real
  start.
- Module renames in pre2: `conv_float_s32` is now `conv_real_sint` (frontpanel.hal
  changed 2026-10-25; the pre1 copy is in pending-pre2comps/orig/). All other modules
  and pin names were checked in halrun and match.
- Rolling back to pre1 after pending-atcmanual is installed: run
  pending-atcmanual/rollback.sh FIRST. The pre1 atc.comp has no manual-mode pins,
  so toolchanger.hal would fail on `atc.0.arm-maxa`.
- `[EMCIO] EMCIO = iov2` is ignored in 2.10 (iocontrol is inside milltask).
- `linuxcnc-ethercat` is installed but this config doesn't use it (no `lcec`).
