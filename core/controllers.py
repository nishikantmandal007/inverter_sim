"""
core/controllers.py
PI, PR (Tustin-discretized), and FCS-MPC controllers.
Each controller is a class with a reset() and step() method.
step() takes (I_ref, I_meas) and returns the control voltage u.
"""

import numpy as np
from .parameters import P


class PIController:
    """
    Conventional PI current controller.
    Baseline — no harmonic rejection capability.
    """
    name = "PI"
    color = "#E06C75"   # red

    def reset(self):
        self._integral = 0.0

    def step(self, I_ref: float, I_meas: float, Vg: float) -> float:
        error = I_ref - I_meas
        self._integral += error * P.dt
        # Anti-windup
        self._integral = np.clip(self._integral, -60.0, 60.0)
        u = Vg + P.PI_Kp * error + P.PI_Ki * self._integral
        return float(np.clip(u, -P.Vdc, P.Vdc))  # H-bridge output: ±Vdc


class PRController:
    """
    Proportional-Resonant controller with harmonic compensation.
    Resonant terms at 50, 150, 250, 350 Hz.

    Each resonant term uses Tustin (bilinear) discretization:
        H(s) = 2*K*wc*s / (s^2 + 2*wc*s + wn^2)
    maps to a 2nd-order IIR filter:
        y[k] = b0*e[k] + b1*e[k-1] + b2*e[k-2] - a1*y[k-1] - a2*y[k-2]
    """
    name = "PR"
    color = "#61AFEF"   # blue

    def __init__(self):
        self._coeffs = self._compute_tustin_coeffs()
        self.reset()

    def _compute_tustin_coeffs(self):
        coeffs = {}
        wd = 2.0 / P.dt   # bilinear prewarping factor
        wc = P.PR_wc

        freqs = {1: P.f_grid}
        freqs.update({h: h * P.f_grid for h in P.PR_Kh})

        gains = {1: P.PR_Kr}
        gains.update(P.PR_Kh)

        for order, freq in freqs.items():
            wn = 2 * np.pi * freq
            K  = gains[order]

            d0 = wd**2 + 2*wc*wd + wn**2
            d1 = -2*wd**2 + 2*wn**2
            d2 = wd**2 - 2*wc*wd + wn**2

            n0 =  2*K*wc*wd
            n1 =  0.0
            n2 = -2*K*wc*wd

            coeffs[order] = {
                'b': np.array([n0, n1, n2]) / d0,
                'a': np.array([d1, d2]) / d0,
            }
        return coeffs

    def reset(self):
        # Each resonant term needs 2 past inputs and 2 past outputs
        self._buf = {
            order: {'e': np.zeros(2), 'y': np.zeros(2)}
            for order in self._coeffs
        }

    def _iir2(self, e: float, order: int) -> float:
        c   = self._coeffs[order]
        buf = self._buf[order]
        y = (c['b'][0] * e
           + c['b'][1] * buf['e'][0]
           + c['b'][2] * buf['e'][1]
           - c['a'][0] * buf['y'][0]
           - c['a'][1] * buf['y'][1])
        buf['e'] = np.array([e, buf['e'][0]])
        buf['y'] = np.array([y, buf['y'][0]])
        return y

    def step(self, I_ref: float, I_meas: float, Vg: float) -> float:
        error = I_ref - I_meas
        u  = Vg + P.PR_Kp * error
        for order in self._coeffs:
            u += self._iir2(error, order)
        return float(np.clip(u, -P.Vdc, P.Vdc))  # H-bridge output: ±Vdc


class MPCController:
    """
    Finite Control Set - Model Predictive Control.
    At each step, evaluates 5 voltage levels and picks the one
    that minimises: J = (I_ref - I_pred)^2 + lambda * switching_cost
    Prediction uses the discrete inductor model:
        I(k+1) = I(k) + (dt/L1) * (V_applied - Rf*I(k) - Vg)
    """
    name = "MPC"
    color = "#98C379"   # green

    # Voltage levels available to the H-bridge (full bridge: ±Vdc)
    # 9 levels for fine-grained predictive control
    _V_levels = np.array([-1.0, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0]) * P.Vdc

    def reset(self):
        self._last_V = 0.0
        self._Vg_est = 0.0

    def step(self, I_ref: float, I_meas: float, Vg: float) -> float:
        self._Vg_est = Vg
        best_u    = 0.0
        best_cost = np.inf

        for V in self._V_levels:
            # One-step prediction
            I_p1 = I_meas + (P.dt / P.L1) * (V - P.Rf * I_meas - self._Vg_est)
            # Two-step prediction (horizon = 2)
            I_p2 = I_p1  + (P.dt / P.L1) * (V - P.Rf * I_p1  - self._Vg_est)

            track_cost  = (I_ref - I_p2) ** 2
            switch_cost = P.MPC_lambda * float(V != self._last_V)
            cost = track_cost + switch_cost

            if cost < best_cost:
                best_cost = cost
                best_u    = V

        self._last_V = best_u
        return float(best_u)


# Registry — add new controllers here and they appear in the UI automatically
CONTROLLERS = {
    "PI":  PIController,
    "PR":  PRController,
    "MPC": MPCController,
}
