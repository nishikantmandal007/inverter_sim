"""
core/parameters.py
All system parameters in one place.
Change values here — everything else updates automatically.
"""

import numpy as np


class SystemParameters:
    # Grid
    Vg_rms   = 230.0          # V
    Vg_peak  = 230.0 * np.sqrt(2)
    f_grid   = 50.0           # Hz
    omega    = 2 * np.pi * 50.0

    # DC link
    Vdc      = 650.0          # V  (√2 × 2 × Vgrid ≈ 650V for full modulation)

    # LCL filter
    L1       = 5e-3           # H  inverter side
    L2       = 2e-3           # H  grid side
    Cf       = 10e-6          # F
    Rf       = 0.1            # Ω  damping

    # Reference current
    I_ref_peak = 10.0         # A

    # PV-side supervisory model
    G_nom      = 1000.0       # W/m^2
    G_init     = 1000.0       # W/m^2
    P_pv_nom   = 650.0        # W  average PV power dispatched to the grid-side stage
    MPPT_eff   = 0.985        # per-unit, idealized supervisory MPPT efficiency
    P_grid_min = 180.0        # W  keep a visible non-zero grid exchange in the demo

    # Load harmonics (fraction of fundamental)
    harm = {3: 0.30, 5: 0.17, 7: 0.11, 9: 0.05, 11: 0.04}  # tuned to ~36.84% THD
    I_load_fund = 8.0         # A  fundamental magnitude
    load_phase  = -np.pi / 6  # rad  lagging (inductive)

    # Simulation
    dt       = 2e-5           # s   50 kHz
    fs       = 1.0 / 2e-5    # Hz

    # Signal extraction and supervisory control
    SOGI_k               = np.sqrt(2.0)
    pq_lpf_hz            = 12.0
    vrms_lpf_hz          = 10.0
    q_support_gain_var_v = 55.0
    q_support_limit      = 450.0
    PR_harmonics         = (3, 5, 7)
    MPC_harmonics        = (3, 5, 7, 9, 11)

    # PI gains
    PI_Kp    = 15.0            # same as PR_Kp for fair comparison
    PI_Ki    = 500.0

    # PR gains (Tustin discretized inside controller)
    PR_Kp    = 15.0
    PR_Kr    = 600.0          # fundamental resonant gain
    PR_wc    = 10.0           # bandwidth rad/s
    PR_Kh    = {3: 420.0, 5: 340.0, 7: 250.0, 9: 60.0, 11: 40.0}  # harmonic resonant gains

    # MPC
    MPC_lambda = 0.002        # switching penalty weight

    # Explanation-focused harmonic set shown in the UI
    display_harmonics = (1, 3, 5, 7, 9, 11)

    # Estimated loss model for the explainable dashboard
    switch_R_on = 0.18        # ohm, lumped semiconductor on-state resistance estimate
    switch_E_per_event = 7.5e-5   # J, estimated switching energy per normalized event
    L1_cu_R = 0.18            # ohm, inverter-side inductor copper loss estimate
    L2_cu_R = 0.12            # ohm, grid-side inductor copper loss estimate
    Cf_esr = 0.45             # ohm, capacitor ESR estimate


P = SystemParameters()
