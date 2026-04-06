# Smart Grid Solar Inverter — Real-Time Simulation
Department of Electrical Engineering, B.I.T. Sindri

## Install

```bash
uv pip install -r requirements.txt
```

The dashboard uses PySide6 plus embedded Matplotlib panels in a light CERN control-page style.

## Run

```bash
.venv/bin/python main.py
```

## What you see

- **Page strip + blue banner** — CERN-inspired control-page framing with live clock
- **Summary cells** — grid RMS, DC link, active controller, THD, PF, and event state
- **Top Matplotlib panel** — grid voltage, load current, grid current, and reference traces
- **Middle Matplotlib panel** — harmonic and reactive compensation currents
- **Bottom Matplotlib panel** — harmonic spectrum before and after compensation
- **Right status board** — live power metrics, IEEE 519 status, controller mode, and comments

## Controls

| Control | Action |
|---------|--------|
| PI / PR / MPC buttons | Switch controller instantly |
| RUN / PAUSE | Start or pause the simulation |
| RESET | Restart from cycle 0 and clear event state |
| Speed slider | Adjust dashboard refresh speed |
| Inject Voltage Sag | Apply a 20% sag for 3 cycles |
| Channel buttons | Show or hide traces on the main waveform panel |

## File structure

```text
main.py                 entry point
requirements.txt

core/
  parameters.py         all system parameters
  controllers.py        PI, PR, MPC controller classes
  simulation.py         simulation engine

widgets/
  oscilloscope.py       Matplotlib waveform panel
  spectrum.py           Matplotlib spectrum panel
  metrics.py            light CERN-style metrics panel

ui/
  main_window.py        dashboard layout and event handling
```

## Tuning

All electrical and controller parameters are in `core/parameters.py`.
Change Kp, Kr, wc, lambda, or the harmonic content and rerun to inspect the updated control response.
