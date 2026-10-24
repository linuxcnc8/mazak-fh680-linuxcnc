# axisrc.py -- AXIS hooks for the Mazak (2026-10-11)
#
# Loaded via [DISPLAY]USER_COMMAND_FILE in mazakv3.ini. AXIS execs this as Python
# just before the GUI is shown, so root_window, vars, comp etc. are in scope.
# NOTE: USER_COMMAND_FILE *replaces* ~/.axisrc, it does not load both.
#
# JOG SPEED KNOB <-> AXIS JOG SLIDER
#   The feed/rapid/spindle knobs move AXIS's sliders because halui sends the new
#   override to motion and AXIS reads it back. Jog speed has no such path - the
#   AXIS jog slider is GUI-only - so this file joins them up the same way:
#
#     knob -> limit1.jog.out --(this file)--> both AXIS jog sliders
#     mm/min slider  --> axisui.jog-speed  --> jog-lspeed --+
#     deg/min slider --> axisui.jog-aspeed --> jog-aspeed --+-> jog-mux -> halui
#   (frontpanel.hal's jog-mux picks deg/min while an A/B button is held)
#
#   The sliders are the jog speeds for everything: the front panel buttons
#   (halui), the AXIS jog buttons and the keyboard. Turning the knob moves both
#   sliders - full knob = KNOB_MAX_LINEAR mm/min and KNOB_MAX_ANGULAR deg/min.
#   Dragging a slider with the mouse sticks until the knob is turned again, the
#   same as the override sliders.

import hal as _hal

_KNOB_PIN = "limit1.jog.out"   # knob in mm/min, after the dead zone (frontpanel.hal)
KNOB_MAX_LINEAR = 6000         # = limit1.jog.max in frontpanel.hal
KNOB_MAX_ANGULAR = 3600        # deg/min at full knob (10 rev/min)
_KNOB_DEADBAND = 10            # mm/min - ignore pot noise smaller than this
_knob_last = [None]


def user_hal_pins():
    comp.newpin("jog-speed", _hal.HAL_FLOAT, _hal.HAL_OUT)
    comp.newpin("jog-aspeed", _hal.HAL_FLOAT, _hal.HAL_OUT)
    comp.ready()


def _set_jog_sliders(knob):
    # Move each slider (via the scale's variable, so its -command does not fire
    # and re-quantise the speed), then set the speed itself. after_idle so it
    # lands after anything the slider schedules.
    lin = max(knob, 0)
    ang = lin / KNOB_MAX_LINEAR * KNOB_MAX_ANGULAR
    root_window.tk.eval("set jog_slider_val [setval %f $max_speed]" % lin)
    root_window.tk.eval("set ajog_slider_val [setval %f $max_aspeed]" % ang)
    root_window.after_idle(lambda: (vars.jog_speed.set(round(lin)),
                                    vars.jog_aspeed.set(round(ang))))


def user_live_update():
    try:
        knob = _hal.get_value(_KNOB_PIN)
    except Exception:
        knob = None
    if knob is not None and (_knob_last[0] is None
                             or abs(knob - _knob_last[0]) >= _KNOB_DEADBAND):
        _knob_last[0] = knob
        _set_jog_sliders(knob)
    try:
        comp["jog-speed"] = float(vars.jog_speed.get())
        comp["jog-aspeed"] = float(vars.jog_aspeed.get())
    except Exception:
        pass
