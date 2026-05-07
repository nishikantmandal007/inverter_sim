"""
core/simulation.py
Phase-aware power-quality simulation engine with explanation-ready metrics.

The dashboard now needs to tell a clear story:
- what the distorted load current looks like before compensation
- what current the inverter injects to cancel harmonics/reactive burden
- why PI / PR / MPC behave differently
- which values improve and why those improvements matter

To support that, the engine keeps the lightweight visual signal synthesis for the
incoming grid and nonlinear load, then runs a sample-level controller-truth pass
for PI, PR, and MPC so the cleaned waveforms, comparison cards, and explanation
drawer are all backed by actual controller behavior.
"""

from dataclasses import dataclass, field

import numpy as np

from .controllers import CONTROLLERS
from .parameters import P


@dataclass
class SimResult:
    t: np.ndarray
    Vg: np.ndarray
    I_load: np.ndarray
    I_grid: np.ndarray
    I_ref: np.ndarray
    I_comp: np.ndarray
    I_harm: np.ndarray
    I_react: np.ndarray

    THD_before: float = 0.0
    THD_after: float = 0.0
    PF_before: float = 0.0
    PF_after: float = 0.0
    P_out: float = 0.0
    Q_out: float = 0.0
    V_rms: float = 0.0
    P_load: float = 0.0
    Q_load: float = 0.0
    P_pv: float = 0.0
    irradiance: float = 0.0

    freqs: np.ndarray = field(default_factory=lambda: np.array([]))
    spectrum_before: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    spectrum_after: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))

    harmonic_orders: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    harmonics_before: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    harmonics_after: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    harmonic_reduction: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))
    dominant_harmonic: str = "--"
    comp_rms: float = 0.0
    grid_rms: float = 0.0
    load_rms: float = 0.0
    reactive_comp_ratio: float = 0.0
    sinusoid_score: float = 0.0
    efficiency: float = 0.0
    loss_breakdown: dict = field(default_factory=dict)
    controller_truth: dict = field(default_factory=dict)

    cycle: int = 0
    ctrl_name: str = "PI"
    phase_mode: str = "single"
    phase_labels: tuple[str, ...] = ("A",)


class SimulationEngine:
    SAMPLES_PER_CYCLE = int(round(1.0 / (P.f_grid * P.dt)))

    _SINGLE_LABELS = ("A",)
    _THREE_LABELS = ("A", "B", "C")
    _THREE_SHIFTS = (0.0, -2.0 * np.pi / 3.0, 2.0 * np.pi / 3.0)
    _HARMONIC_PHASES = {
        3: np.pi / 4.0,
        5: -np.pi / 3.0,
        7: np.pi / 5.0,
        9: -np.pi / 6.0,
        11: np.pi / 8.0,
    }
    _THREE_PHASE_HARMONICS = {5: 0.22, 7: 0.14, 11: 0.06}

    def __init__(self):
        self._ctrl_name = "PI"
        self._phase_mode = "single"

        self._cycle = 0
        self._t_abs = 0.0
        self._sag_active = False
        self._sag_depth = 0.0
        self._sag_cycles_left = 0
        self._irradiance = P.G_init

    @property
    def phase_mode(self) -> str:
        return self._phase_mode

    @property
    def phase_labels(self) -> tuple[str, ...]:
        return self._SINGLE_LABELS if self._phase_mode == "single" else self._THREE_LABELS

    @property
    def sag_active(self) -> bool:
        return self._sag_active

    def set_controller(self, name: str):
        if name in CONTROLLERS:
            self._ctrl_name = name

    def set_phase_mode(self, mode: str):
        if mode in {"single", "three"}:
            self._phase_mode = mode

    def trigger_voltage_sag(self, depth: float = 0.20, duration_cycles: int = 3):
        self._sag_active = True
        self._sag_depth = depth
        self._sag_cycles_left = duration_cycles

    def step_cycle(self) -> SimResult:
        phase_count, phase_labels, shifts, harmonic_map = self._phase_setup()

        n = self.SAMPLES_PER_CYCLE
        t_cycle = np.arange(n) * P.dt + self._t_abs

        Vg = np.zeros((phase_count, n))
        I_load = np.zeros((phase_count, n))
        I_ref = np.zeros((phase_count, n))
        I_harm = np.zeros((phase_count, n))
        I_react = np.zeros((phase_count, n))
        comp_target = np.zeros((phase_count, n))

        sag_factor = 1.0
        if self._sag_active:
            sag_factor = 1.0 - self._sag_depth
            self._sag_cycles_left -= 1
            if self._sag_cycles_left <= 0:
                self._sag_active = False

        base_active_coeff = P.I_load_fund * np.cos(P.load_phase)
        base_reactive_coeff = P.I_load_fund * np.sin(P.load_phase)

        for phase_idx in range(phase_count):
            shift = shifts[phase_idx]

            for sample_idx, t in enumerate(t_cycle):
                theta = P.omega * t + shift
                sin_t = np.sin(theta)
                cos_t = np.cos(theta)

                Vg[phase_idx, sample_idx] = sag_factor * (
                    P.Vg_peak * sin_t
                    + 0.008 * P.Vg_peak * np.sin(5.0 * theta)
                    + 0.004 * P.Vg_peak * np.sin(7.0 * theta)
                )

                active_fundamental = base_active_coeff * sin_t
                reactive_component = base_reactive_coeff * cos_t
                harmonic_component = 0.0

                for order, amp in harmonic_map.items():
                    harmonic_component += (
                        P.I_load_fund * amp
                        * np.sin(order * theta + self._HARMONIC_PHASES.get(order, 0.0))
                    )

                support_component = 0.0
                if self._sag_active:
                    support_component = 0.25 * self._sag_depth * P.I_load_fund * cos_t

                I_ref[phase_idx, sample_idx] = active_fundamental
                I_react[phase_idx, sample_idx] = reactive_component + support_component
                I_harm[phase_idx, sample_idx] = harmonic_component
                I_load[phase_idx, sample_idx] = active_fundamental + reactive_component + harmonic_component
                comp_target[phase_idx, sample_idx] = I_react[phase_idx, sample_idx] + I_harm[phase_idx, sample_idx]

        p_load_total, q_load_total, pf_before = self._power_metrics(Vg, I_load)
        thd_before = float(np.mean([self._thd(I_load[p]) for p in range(phase_count)]))

        controller_truth: dict[str, dict] = {}
        selected_response = None
        harmonic_orders = np.asarray(P.display_harmonics, dtype=int)

        for name in CONTROLLERS:
            response = self._simulate_controller_response(name, Vg, I_load, comp_target, harmonic_orders)
            response["control_effectiveness"] = float(np.clip(
                (thd_before - response["THD_after"]) * 1.6
                + (response["PF_after"] - pf_before) * 125.0,
                0.0,
                100.0,
            ))
            controller_truth[name] = response
            if name == self._ctrl_name:
                selected_response = response

        if selected_response is None:
            selected_response = controller_truth["PI"]

        I_comp = selected_response["I_comp"]
        I_grid = selected_response["I_grid"]

        self._t_abs += n * P.dt
        self._cycle += 1

        v_rms = float(np.mean(np.sqrt(np.mean(Vg ** 2, axis=1))))
        freqs, spectrum_before, spectrum_after = self._spectrum(I_load, I_grid)

        harmonics_before = self._harmonic_samples(I_load, harmonic_orders)
        harmonics_after = self._harmonic_samples(I_grid, harmonic_orders)
        harmonic_reduction = 100.0 * (harmonics_before - harmonics_after) / (harmonics_before + 1e-9)
        dominant_harmonic = self._dominant_harmonic_label(harmonic_orders, harmonics_before, harmonics_after)

        q_before_abs = abs(q_load_total)
        reactive_comp_ratio = float(np.clip(
            (q_before_abs - abs(selected_response["Q_out"])) / (q_before_abs + 1e-9),
            0.0,
            1.2,
        ))
        sinusoid_score = float(np.clip(
            100.0
            - selected_response["THD_after"] * 8.0
            - abs(1.0 - selected_response["PF_after"]) * 250.0,
            0.0,
            100.0,
        ))

        return SimResult(
            t=t_cycle,
            Vg=Vg,
            I_load=I_load,
            I_grid=I_grid,
            I_ref=I_ref,
            I_comp=I_comp,
            I_harm=I_harm,
            I_react=I_react,
            THD_before=thd_before,
            THD_after=selected_response["THD_after"],
            PF_before=pf_before,
            PF_after=selected_response["PF_after"],
            P_out=selected_response["P_out"],
            Q_out=selected_response["Q_out"],
            V_rms=v_rms,
            P_load=p_load_total,
            Q_load=q_load_total,
            P_pv=self._pv_power_available(),
            irradiance=self._irradiance,
            freqs=freqs,
            spectrum_before=spectrum_before,
            spectrum_after=spectrum_after,
            harmonic_orders=harmonic_orders,
            harmonics_before=harmonics_before,
            harmonics_after=harmonics_after,
            harmonic_reduction=harmonic_reduction,
            dominant_harmonic=dominant_harmonic,
            comp_rms=selected_response["comp_rms"],
            grid_rms=selected_response["grid_rms"],
            load_rms=selected_response["load_rms"],
            reactive_comp_ratio=reactive_comp_ratio,
            sinusoid_score=sinusoid_score,
            efficiency=selected_response["efficiency"],
            loss_breakdown=selected_response["loss_breakdown"],
            controller_truth={
                name: {
                    "THD_after": data["THD_after"],
                    "PF_after": data["PF_after"],
                    "Q_out": data["Q_out"],
                    "P_out": data["P_out"],
                    "comp_rms": data["comp_rms"],
                    "grid_rms": data["grid_rms"],
                    "efficiency": data["efficiency"],
                    "control_effectiveness": data["control_effectiveness"],
                    "dominant_harmonic": data["dominant_harmonic"],
                    "best_orders": data["best_orders"],
                    "method": self._controller_method_text(name),
                }
                for name, data in controller_truth.items()
            },
            cycle=self._cycle,
            ctrl_name=self._ctrl_name,
            phase_mode=self._phase_mode,
            phase_labels=phase_labels,
        )

    def _simulate_controller_response(
        self,
        ctrl_name: str,
        voltage: np.ndarray,
        load_current: np.ndarray,
        comp_target: np.ndarray,
        harmonic_orders: np.ndarray,
    ) -> dict:
        phase_count, n = voltage.shape
        comp_current = np.zeros_like(voltage)
        grid_current = np.zeros_like(voltage)
        u_cmd = np.zeros_like(voltage)

        for phase_idx in range(phase_count):
            controller = CONTROLLERS[ctrl_name]()
            controller.reset()
            i_meas = 0.0

            for pass_idx in range(5):  # enough for settling without unrealistic convergence
                for sample_idx in range(n):
                    ref = float(comp_target[phase_idx, sample_idx])
                    vg = float(voltage[phase_idx, sample_idx])
                    u = float(controller.step(ref, i_meas, vg))
                    di = (P.dt / P.L1) * (u - P.Rf * i_meas - vg)
                    i_meas += di

                    if pass_idx == 4:  # capture on the final settled pass
                        comp_current[phase_idx, sample_idx] = i_meas
                        u_cmd[phase_idx, sample_idx] = u

            grid_current[phase_idx] = load_current[phase_idx] - comp_current[phase_idx]

        p_out, q_out, pf_after = self._power_metrics(voltage, grid_current)
        thd_after = float(np.mean([self._thd(grid_current[p]) for p in range(phase_count)]))
        losses = self._estimate_losses(comp_current, grid_current, u_cmd, harmonic_orders)

        before_harm = self._harmonic_samples(load_current, harmonic_orders)
        after_harm = self._harmonic_samples(grid_current, harmonic_orders)
        reduction = 100.0 * (before_harm - after_harm) / (before_harm + 1e-9)
        comp_rms = float(np.mean(np.sqrt(np.mean(comp_current ** 2, axis=1))))
        grid_rms = float(np.mean(np.sqrt(np.mean(grid_current ** 2, axis=1))))
        load_rms = float(np.mean(np.sqrt(np.mean(load_current ** 2, axis=1))))
        efficiency = float(abs(p_out) / (abs(p_out) + losses["total"] + 1e-9))

        return {
            "I_comp": comp_current,
            "I_grid": grid_current,
            "u_cmd": u_cmd,
            "THD_after": thd_after,
            "PF_after": pf_after,
            "P_out": p_out,
            "Q_out": q_out,
            "comp_rms": comp_rms,
            "grid_rms": grid_rms,
            "load_rms": load_rms,
            "harmonics_after": after_harm,
            "harmonic_reduction": reduction,
            "dominant_harmonic": self._dominant_harmonic_label(harmonic_orders, before_harm, after_harm),
            "best_orders": self._best_orders_text(harmonic_orders, reduction),
            "loss_breakdown": losses,
            "efficiency": efficiency,
        }

    def _phase_setup(self) -> tuple[int, tuple[str, ...], tuple[float, ...], dict[int, float]]:
        if self._phase_mode == "three":
            return 3, self._THREE_LABELS, self._THREE_SHIFTS, self._THREE_PHASE_HARMONICS
        return 1, self._SINGLE_LABELS, (0.0,), dict(P.harm)

    def _pv_power_available(self) -> float:
        irradiance_pu = np.clip(self._irradiance / P.G_nom, 0.0, 1.2)
        return float(P.P_pv_nom * irradiance_pu * P.MPPT_eff)

    def _thd(self, signal: np.ndarray) -> float:
        n = len(signal)
        mag = np.abs(np.fft.rfft(signal)) / n * 2.0
        freqs = np.fft.rfftfreq(n, d=P.dt)
        i1 = int(np.argmin(np.abs(freqs - P.f_grid)))
        fundamental = mag[i1] + 1e-9

        harm_sq = 0.0
        for order in range(2, 16):
            idx = int(np.argmin(np.abs(freqs - order * P.f_grid)))
            if idx < len(mag):
                harm_sq += mag[idx] ** 2
        return 100.0 * np.sqrt(harm_sq) / fundamental

    def _power_metrics(self, voltage: np.ndarray, current: np.ndarray) -> tuple[float, float, float]:
        p_total = 0.0
        q_total = 0.0
        s_total = 0.0

        for phase_v, phase_i in zip(voltage, current):
            vrms = np.sqrt(np.mean(phase_v ** 2))
            irms = np.sqrt(np.mean(phase_i ** 2))
            p = np.mean(phase_v * phase_i)

            v1 = self._fundamental_phasor(phase_v)
            i1 = self._fundamental_phasor(phase_i)
            q = 0.5 * np.imag(v1 * np.conj(i1))

            p_total += p
            q_total += q
            s_total += vrms * irms

        pf = abs(p_total) / (s_total + 1e-9)
        return float(p_total), float(q_total), float(pf)

    def _fundamental_phasor(self, signal: np.ndarray) -> complex:
        n = len(signal)
        t = np.arange(n) * P.dt
        return (2.0 / n) * np.dot(signal, np.exp(-1j * P.omega * t))

    def _harmonic_samples(self, signals: np.ndarray, harmonic_orders: np.ndarray) -> np.ndarray:
        if signals.size == 0:
            return np.zeros((0, harmonic_orders.size))

        n = signals.shape[1]
        freqs = np.fft.rfftfreq(n, d=P.dt)
        spectrum = np.abs(np.fft.rfft(signals, axis=1)) / n * 2.0

        sampled = np.zeros((signals.shape[0], harmonic_orders.size))
        for order_idx, order in enumerate(harmonic_orders):
            target = order * P.f_grid
            bin_idx = int(np.argmin(np.abs(freqs - target)))
            sampled[:, order_idx] = spectrum[:, bin_idx]
        return sampled

    def _dominant_harmonic_label(
        self,
        harmonic_orders: np.ndarray,
        before_harm: np.ndarray,
        after_harm: np.ndarray,
    ) -> str:
        if before_harm.size == 0:
            return "--"

        if harmonic_orders.size <= 1:
            return "Fundamental only"

        removed = np.mean(before_harm - after_harm, axis=0)
        harmonic_slice = removed[1:]
        if not np.any(harmonic_slice > 0.0):
            return "Residual harmonics remain"

        best_idx = int(np.argmax(harmonic_slice)) + 1
        order = int(harmonic_orders[best_idx])
        return f"{self._ordinal(order)} harmonic"

    def _best_orders_text(self, harmonic_orders: np.ndarray, reduction: np.ndarray) -> str:
        if reduction.size == 0 or harmonic_orders.size <= 1:
            return "--"

        avg_reduction = np.mean(reduction, axis=0)
        ranked = [
            (float(avg_reduction[idx]), int(order))
            for idx, order in enumerate(harmonic_orders)
            if order != 1
        ]
        ranked.sort(reverse=True)
        winners = [order for score, order in ranked[:2] if score > 0.0]
        if not winners:
            return "General cleanup"
        return ", ".join(f"{self._ordinal(order)}" for order in winners)

    def _estimate_losses(
        self,
        comp_current: np.ndarray,
        grid_current: np.ndarray,
        u_cmd: np.ndarray,
        harmonic_orders: np.ndarray,
    ) -> dict:
        comp_phase_rms = np.sqrt(np.mean(comp_current ** 2, axis=1))
        grid_phase_rms = np.sqrt(np.mean(grid_current ** 2, axis=1))

        comp_harmonics = self._harmonic_samples(comp_current, harmonic_orders)
        comp_fund_rms = comp_harmonics[:, 0] / np.sqrt(2.0) if harmonic_orders.size else np.zeros_like(comp_phase_rms)
        comp_harm_rms = np.sqrt(np.maximum(comp_phase_rms ** 2 - comp_fund_rms ** 2, 0.0))

        conduction = float(np.sum(2.0 * comp_phase_rms ** 2 * P.switch_R_on))

        normalized_steps = np.mean(np.abs(np.diff(u_cmd, axis=1)), axis=1) / max(P.Vdc / 2.0, 1e-9)
        current_scale = np.maximum(comp_phase_rms / max(P.I_load_fund / np.sqrt(2.0), 1e-9), 0.2)
        switching = float(np.sum(normalized_steps * P.fs * P.switch_E_per_event * current_scale))

        l1_copper = float(np.sum(comp_phase_rms ** 2 * P.L1_cu_R))
        l2_copper = float(np.sum(grid_phase_rms ** 2 * P.L2_cu_R))
        capacitor_esr = float(np.sum((0.35 * comp_harm_rms) ** 2 * P.Cf_esr))
        total = conduction + switching + l1_copper + l2_copper + capacitor_esr

        return {
            "conduction": conduction,
            "switching": switching,
            "l1_copper": l1_copper,
            "l2_copper": l2_copper,
            "capacitor_esr": capacitor_esr,
            "total": total,
        }

    def _controller_method_text(self, name: str) -> str:
        if name == "PI":
            return "Tracks overall current error, but it is not frequency-selective, so harmonic cleanup is limited."
        if name == "PR":
            return "Uses resonant action at the fundamental and tuned harmonic frequencies, so targeted harmonic cancellation is stronger."
        return "Predicts the next current response and chooses the switching state that best reduces future error. (Note: The visible 'noise' or ripple in the MPC graph occurs because it switches dynamically to minimize error in real-time, creating high-frequency switching ripple that the filter partially absorbs)."

    def _ordinal(self, value: int) -> str:
        if 10 <= value % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
        return f"{value}{suffix}"

    def _spectrum(self, before: np.ndarray, after: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        n = before.shape[1]
        freqs = np.fft.rfftfreq(n, d=P.dt)
        mask = freqs <= 650.0

        def mag(signal: np.ndarray) -> np.ndarray:
            return np.abs(np.fft.rfft(signal, axis=1)) / n * 2.0

        return freqs[mask], mag(before)[:, mask], mag(after)[:, mask]
