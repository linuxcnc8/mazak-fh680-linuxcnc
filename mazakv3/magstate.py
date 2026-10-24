#!/usr/bin/env python3
"""Remembers which carousel pot is out, across LinuxCNC restarts.

mag.0.pot-out / pot-pocket / pot-unknown  ->  mag_state.txt (written on every change)
mag_state.txt  ->  magstate.saved-pot-out / saved-pot-pocket / saved-pot-unknown at startup

Saves only after mag.0.state-loaded, so the empty startup values never
overwrite the file before mag has read it.

File format, one line:  <pot_out 0|1> <pocket> <pot_unknown 0|1>
An old two-field line counts as unknown if a pot is out (2026-10-24) - we
can't tell where that pot is.
"""
import os
import time

import hal

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mag_state.txt")


def load():
    try:
        with open(FILE) as f:
            fields = f.read().split()
        out, pocket = int(fields[0]) != 0, int(fields[1])
        unknown = int(fields[2]) != 0 if len(fields) > 2 else out
        return out, pocket, unknown
    except (OSError, ValueError, IndexError):
        return False, 0, False


def save(out, pocket, unknown):
    tmp = FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write(f"{int(out)} {pocket} {int(unknown)}\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, FILE)


h = hal.component("magstate")
h.newpin("pot-out", hal.HAL_BIT, hal.HAL_IN)
h.newpin("pot-pocket", hal.HAL_S32, hal.HAL_IN)
h.newpin("pot-unknown", hal.HAL_BIT, hal.HAL_IN)
h.newpin("state-loaded", hal.HAL_BIT, hal.HAL_IN)
h.newpin("saved-pot-out", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("saved-pot-pocket", hal.HAL_S32, hal.HAL_OUT)
h.newpin("saved-pot-unknown", hal.HAL_BIT, hal.HAL_OUT)
h.newpin("saved-valid", hal.HAL_BIT, hal.HAL_OUT)

last = load()
h["saved-pot-out"], h["saved-pot-pocket"], h["saved-pot-unknown"] = last
h["saved-valid"] = True
h.ready()

try:
    while True:
        time.sleep(0.1)
        if not h["state-loaded"]:
            continue
        cur = (bool(h["pot-out"]), int(h["pot-pocket"]), bool(h["pot-unknown"]))
        if cur != last:
            save(*cur)
            last = cur
except KeyboardInterrupt:
    pass
