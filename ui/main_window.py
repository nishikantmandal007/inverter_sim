"""
ui/main_window.py
Explainable dashboard for the smart-grid solar inverter simulator.
"""

import html

import numpy as np
from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.parameters import P
from core.simulation import SimulationEngine, SimResult
from ui.settings_dialog import SettingsDialog
from widgets.circuit_panel import CircuitPanel
from widgets.metrics import MetricsPanel
from widgets.oscilloscope import Channel, OscilloscopeWidget
from widgets.spectrum import SpectrumWidget


STYLE = """
QMainWindow, QWidget {
    background-color: #f2f0e8;
    color: #111111;
    font-family: "DejaVu Sans";
    font-size: 11px;
}
QFrame#page_strip, QFrame#status_strip {
    background-color: #0b0f1a;
    border: 1px solid #05070c;
}
QLabel#strip_tag, QLabel#strip_clock {
    background-color: #efe9dc;
    border: 1px solid #111111;
    color: #0b0f1a;
    font-family: "DejaVu Sans Mono";
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.8px;
    padding: 1px 6px;
}
QLabel#strip_footer {
    background-color: transparent;
    color: #efe9dc;
    font-family: "DejaVu Sans Mono";
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.8px;
}
QLabel#banner_title {
    background-color: #2036c7;
    border: 2px solid #111111;
    color: #ffffff;
    font-size: 22px;
    font-weight: bold;
    padding: 8px 12px;
}
QFrame#info_cell {
    background-color: #ffffff;
    border: 1px solid #111111;
}
QLabel#info_label {
    color: #111111;
    font-size: 9px;
    font-weight: bold;
    letter-spacing: 0.5px;
}
QLabel#info_value {
    font-family: "DejaVu Sans Mono";
    font-size: 16px;
    font-weight: bold;
    color: #102d8f;
}
QLabel#info_unit {
    color: #555555;
    font-size: 9px;
}
QFrame#panel {
    background-color: #ffffff;
    border: 1px solid #111111;
}
QLabel#panel_title {
    background-color: #2036c7;
    border: 1px solid #111111;
    color: #ffffff;
    font-family: "DejaVu Sans Mono";
    font-size: 11px;
    font-weight: bold;
    padding: 4px 8px;
    letter-spacing: 0.6px;
}
QLabel#panel_subtitle {
    background-color: #f7f4eb;
    border-left: 1px solid #111111;
    border-right: 1px solid #111111;
    color: #333333;
    font-size: 10px;
    padding: 6px 8px 4px 8px;
}
QLabel#panel_caption {
    background-color: #fffef8;
    border-left: 1px solid #111111;
    border-right: 1px solid #111111;
    border-bottom: 1px solid #111111;
    color: #333333;
    font-size: 10px;
    padding: 6px 8px 8px 8px;
}
QLabel#section_label {
    color: #2036c7;
    font-family: "DejaVu Sans Mono";
    font-size: 10px;
    font-weight: bold;
    padding-top: 2px;
}
QPushButton {
    background-color: #faf9f2;
    border: 1px solid #111111;
    color: #111111;
    padding: 8px 12px;
    font-family: "DejaVu Sans Mono";
    font-size: 11px;
    min-height: 18px;
}
QPushButton:hover {
    background-color: #ebf0ff;
}
QPushButton:pressed {
    background-color: #d8e1ff;
}
QPushButton:checked {
    background-color: #2036c7;
    color: #ffffff;
}
QPushButton#PI_btn:checked {
    background-color: #bf2026;
}
QPushButton#PR_btn:checked {
    background-color: #102d8f;
}
QPushButton#MPC_btn:checked {
    background-color: #0f6f25;
}
QPushButton#run_btn {
    background-color: #0f6f25;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#run_btn:checked {
    background-color: #d6c04a;
    color: #111111;
}
QPushButton#sag_btn {
    background-color: #fff4d7;
    color: #7f5200;
}
QPushButton#view_btn:checked {
    background-color: #2036c7;
    color: #ffffff;
}
QPushButton#circuit_block {
    min-height: 36px;
    padding: 4px 6px;
    font-size: 10px;
    background-color: #fffff5;
    border: 2px solid #333333;
    border-radius: 3px;
}
QPushButton#circuit_block:hover {
    background-color: #e8f0ff;
    border-color: #2036c7;
}
QPushButton#circuit_block:checked {
    background-color: #2036c7;
    color: #ffffff;
    border-color: #102080;
}
QSlider::groove:horizontal {
    height: 6px;
    border: 1px solid #111111;
    background: #f2f0e8;
}
QSlider::sub-page:horizontal {
    background: #2036c7;
}
QSlider::handle:horizontal {
    background: #111111;
    width: 12px;
    margin: -4px 0;
}
QLabel#metric_label {
    color: #111111;
    font-size: 9px;
    font-weight: bold;
}
QLabel#metric_value {
    font-family: "DejaVu Sans Mono";
    font-size: 16px;
    font-weight: bold;
}
QLabel#metric_unit {
    color: #555555;
    font-size: 9px;
}
QFrame#metric_cell {
    background-color: #fcfbf6;
    border: 1px solid #111111;
}
QFrame#status_table {
    background-color: #f8f7f1;
    border: 1px solid #111111;
}
QFrame#status_row {
    background-color: transparent;
    border: none;
}
QLabel#status_name {
    color: #111111;
    font-size: 10px;
}
QLabel#status_value {
    font-family: "DejaVu Sans Mono";
    font-size: 10px;
    font-weight: bold;
    border: 1px solid #111111;
    padding: 2px 8px;
}
QFrame#controller_card {
    background-color: #fcfbf6;
    border: 1px solid #111111;
}
QLabel#controller_card_title {
    font-family: "DejaVu Sans Mono";
    font-size: 12px;
    font-weight: bold;
}
QLabel#controller_card_headline {
    color: #111111;
    font-size: 10px;
    font-weight: bold;
}
QLabel#controller_card_body {
    color: #333333;
    font-size: 10px;
}
QTextBrowser#info_browser {
    background-color: #fffef8;
    border: 1px solid #111111;
    padding: 6px;
}
QLabel#circuit_arrow {
    color: #2036c7;
    font-family: "DejaVu Sans Mono";
    font-size: 12px;
    font-weight: bold;
}
"""


class InfoCell(QFrame):
    def __init__(self, label: str, value: str, unit: str, accent: str = "#102d8f", parent=None):
        super().__init__(parent)
        self.setObjectName("info_cell")
        self._accent = accent

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self._label = QLabel(label)
        self._label.setObjectName("info_label")
        layout.addWidget(self._label)

        self._value = QLabel(value)
        self._value.setObjectName("info_value")
        self._value.setAlignment(Qt.AlignCenter)
        self._value.setStyleSheet(f"color: {accent};")
        layout.addWidget(self._value, stretch=1)

        self._unit = QLabel(unit)
        self._unit.setObjectName("info_unit")
        self._unit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._unit)

    def set_value(self, value: str, accent: str | None = None):
        self._value.setText(value)
        color = accent or self._accent
        self._value.setStyleSheet(f"color: {color};")


class MainWindow(QMainWindow):
    _VOLTAGE_PLOT_SCALE = 32.527

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Grid Solar Inverter | Explainable Dashboard")
        self.resize(1660, 980)
        self.setStyleSheet(STYLE)

        self._ctrl_name = "PI"
        self._phase_mode = "single"
        self._selected_phase_idx = 0
        self._view_mode = "story"
        self._engine = SimulationEngine()
        self._running = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._display_phase = 0
        self._current_info_topic = "overview"
        self._last_result: SimResult | None = None

        self._build_ui()
        self._set_phase_mode("single")
        self._set_display_phase(0)
        self._set_controller("PI")
        self._set_view_mode("story")
        self._metrics.set_running_state(False)
        self._metrics.set_event_state(False)
        self._refresh_clock()
        self._refresh_info()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        root_layout.setSpacing(6)

        root_layout.addWidget(self._make_page_strip())
        root_layout.addWidget(self._make_banner())
        root_layout.addWidget(self._make_summary_row())

        main = QHBoxLayout()
        main.setSpacing(8)
        root_layout.addLayout(main, stretch=1)

        main.addWidget(self._make_control_panel(), stretch=0)
        main.addLayout(self._make_plot_area(), stretch=1)
        main.addWidget(self._make_metrics_panel(), stretch=0)

        root_layout.addWidget(self._make_status_bar())

    def _make_page_strip(self):
        frame = QFrame()
        frame.setObjectName("page_strip")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(16)

        for text in ("INVERTER PAGE 1", "Fs: 50 kHz", f"Vdc: {P.Vdc:.0f} V"):
            lbl = QLabel(text)
            lbl.setObjectName("strip_tag")
            layout.addWidget(lbl)

        layout.addStretch()

        self._lbl_clock = QLabel("")
        self._lbl_clock.setObjectName("strip_clock")
        layout.addWidget(self._lbl_clock)
        return frame

    def _make_banner(self):
        label = QLabel("SMART GRID SOLAR INVERTER | BEFORE, CIRCUIT ACTION, AFTER")
        label.setObjectName("banner_title")
        label.setAlignment(Qt.AlignCenter)
        return label

    def _make_summary_row(self):
        frame = QWidget()
        layout = QGridLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)

        self._info_grid = InfoCell("GRID RMS", f"{P.Vg_rms:.1f}", "V", "#102d8f")
        self._info_comp = InfoCell("COMP RMS", "--", "A", "#c97d00")
        self._info_mode = InfoCell("PHASE MODE", "1PH-A", "MODE", "#102d8f")
        self._info_controller = InfoCell("CONTROLLER", "PI", "MODE", "#bf2026")
        self._info_thd_before = InfoCell("THD BEFORE", "--", "%", "#bf2026")
        self._info_thd_after = InfoCell("THD AFTER", "--", "%", "#0f6f25")
        self._info_pf = InfoCell("PF AFTER", "--", "PF", "#102d8f")
        self._info_event = InfoCell("GRID EVENT", "NORMAL", "STATE", "#102d8f")

        cells = [
            self._info_grid,
            self._info_comp,
            self._info_mode,
            self._info_controller,
            self._info_thd_before,
            self._info_thd_after,
            self._info_pf,
            self._info_event,
        ]

        for idx, cell in enumerate(cells):
            layout.addWidget(cell, 0, idx)

        return frame

    def _create_panel(self, title: str):
        panel = QFrame()
        panel.setObjectName("panel")

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("panel_title")
        outer.addWidget(title_lbl)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(10, 10, 10, 10)
        body_layout.setSpacing(8)
        outer.addWidget(body)

        return panel, body_layout

    def _section_label(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("section_label")
        return lbl

    def _make_control_panel(self):
        panel, layout = self._create_panel("CONTROL MATRIX")
        panel.setFixedWidth(250)

        layout.addWidget(self._section_label("NETWORK MODE"))
        self._btn_single = QPushButton("SINGLE PHASE")
        self._btn_three = QPushButton("THREE PHASE")
        for btn in (self._btn_single, self._btn_three):
            btn.setCheckable(True)
            layout.addWidget(btn)
        self._btn_single.clicked.connect(lambda: self._set_phase_mode("single"))
        self._btn_three.clicked.connect(lambda: self._set_phase_mode("three"))

        layout.addSpacing(4)
        layout.addWidget(self._section_label("CONTROLLER BANK"))

        self._btn_PI = QPushButton("PI | CONVENTIONAL")
        self._btn_PR = QPushButton("PR | RESONANT")
        self._btn_MPC = QPushButton("MPC | PREDICTIVE")

        self._btn_PI.setObjectName("PI_btn")
        self._btn_PR.setObjectName("PR_btn")
        self._btn_MPC.setObjectName("MPC_btn")

        for btn in (self._btn_PI, self._btn_PR, self._btn_MPC):
            btn.setCheckable(True)
            layout.addWidget(btn)

        self._btn_PI.clicked.connect(lambda: self._set_controller("PI"))
        self._btn_PR.clicked.connect(lambda: self._set_controller("PR"))
        self._btn_MPC.clicked.connect(lambda: self._set_controller("MPC"))

        layout.addSpacing(4)
        layout.addWidget(self._section_label("DISPLAY STORY"))

        self._btn_story = QPushButton("STORY VIEW")
        self._btn_step = QPushButton("STEP BY STEP")
        self._btn_story.setObjectName("view_btn")
        self._btn_step.setObjectName("view_btn")
        for btn in (self._btn_story, self._btn_step):
            btn.setCheckable(True)
            layout.addWidget(btn)
        self._btn_story.clicked.connect(lambda: self._set_view_mode("story"))
        self._btn_step.clicked.connect(lambda: self._set_view_mode("step"))

        layout.addSpacing(4)
        layout.addWidget(self._section_label("SIMULATION CONTROL"))

        self._btn_run = QPushButton("RUN")
        self._btn_run.setObjectName("run_btn")
        self._btn_run.setCheckable(True)
        self._btn_run.clicked.connect(self._toggle_run)
        layout.addWidget(self._btn_run)

        btn_reset = QPushButton("RESET")
        btn_reset.clicked.connect(self._reset)
        layout.addWidget(btn_reset)

        speed_label = QLabel("SWEEP SPEED")
        speed_label.setObjectName("section_label")
        layout.addWidget(speed_label)

        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(1, 10)
        self._speed_slider.setValue(5)
        self._speed_slider.valueChanged.connect(self._update_speed)
        layout.addWidget(self._speed_slider)

        layout.addSpacing(4)
        layout.addWidget(self._section_label("DISTURBANCE"))

        btn_sag = QPushButton("INJECT VOLTAGE SAG")
        btn_sag.setObjectName("sag_btn")
        btn_sag.clicked.connect(self._inject_sag)
        layout.addWidget(btn_sag)

        btn_config = QPushButton("⚙ CONFIGURE PARAMETERS")
        btn_config.setStyleSheet("background-color: #2036c7; color: white;")
        btn_config.clicked.connect(self._open_settings)
        layout.addWidget(btn_config)

        layout.addSpacing(4)
        layout.addWidget(self._section_label("DISPLAY PHASE"))

        self._phase_btns = []
        for idx, label in enumerate(("PHASE A", "PHASE B", "PHASE C")):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=idx: self._set_display_phase(i))
            layout.addWidget(btn)
            self._phase_btns.append(btn)

        layout.addStretch()
        return panel

    def _make_plot_area(self):
        from PySide6.QtWidgets import QScrollArea

        layout = QVBoxLayout()
        layout.setSpacing(0)

        # Wrap everything in a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(8)

        self._circuit = CircuitPanel()
        self._circuit.block_selected.connect(self._set_info_topic)
        inner.addWidget(self._circuit, stretch=0)

        self._plot_stack = QStackedWidget()
        self._plot_stack.addWidget(self._build_story_page())
        self._plot_stack.addWidget(self._build_step_page())
        inner.addWidget(self._plot_stack, stretch=1)

        self._spectrum = SpectrumWidget(
            title="HARMONIC SPECTRUM | BEFORE VS AFTER",
            subtitle="This panel compares the strongest harmonic orders in the distorted current and the cleaned source current.",
            caption="Red bars are before compensation. Green bars are after the selected controller and inverter stage act on the same cycle.",
            info_key="graph:spectrum",
        )
        self._spectrum.panel_selected.connect(self._set_info_topic)
        self._spectrum.setMinimumHeight(240)
        inner.addWidget(self._spectrum, stretch=0)

        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)

        return layout

    def _build_story_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._scope_before_story = OscilloscopeWidget(
            title="BEFORE | INCOMING VOLTAGE AND DISTORTED CURRENT",
            subtitle="This is the raw electrical signal before our inverter does anything.",
            caption="Blue = grid voltage (clean sine wave). Red = distorted load current (notice the bumps from harmonics).",
            info_key="graph:before",
        )
        self._scope_before_story.add_channel(Channel("Vg", "Grid Voltage", "V", 1.0))
        self._scope_before_story.add_channel(Channel("I_load", "Distorted Load Current", "A", 1.0))
        self._scope_before_story.panel_selected.connect(self._set_info_topic)
        self._scope_before_story.setMinimumHeight(270)
        layout.addWidget(self._scope_before_story, stretch=1)

        self._scope_after_story = OscilloscopeWidget(
            title="AFTER | CLEANED GRID CURRENT",
            subtitle="The same cycle after our inverter injected correcting current.",
            caption="Green = cleaned grid current (much smoother). Dashed gray = ideal target. Closer match = better controller.",
            info_key="graph:after",
        )
        self._scope_after_story.add_channel(Channel("Vg", "Grid Voltage", "V", 1.0))
        self._scope_after_story.add_channel(Channel("I_grid", "Cleaned Grid Current", "A", 1.0))
        self._scope_after_story.add_channel(Channel("I_ref", "Active Current Target", "A", 1.0))
        self._scope_after_story.panel_selected.connect(self._set_info_topic)
        self._scope_after_story.setMinimumHeight(240)
        layout.addWidget(self._scope_after_story, stretch=1)

        self._scope_error_story = OscilloscopeWidget(
            title="TRACKING ERROR | ACTUAL DEVIATION FROM TARGET",
            subtitle="The literal discrepancy between the ideal target and the cleaned grid current (I_ref - I_grid).",
            caption="Purple = Instantaneous Tracking Error. A flat line at zero means mathematically perfect control.",
            info_key="graph:error",
        )
        self._scope_error_story.add_channel(Channel("I_error", "Tracking Error", "A", 1.0, color="#7a42b8"))
        self._scope_error_story.panel_selected.connect(self._set_info_topic)
        self._scope_error_story.setMinimumHeight(200)
        layout.addWidget(self._scope_error_story, stretch=1)

        return page

    def _build_step_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._scope_raw_step = OscilloscopeWidget(
            title="STEP 1 | RAW WAVEFORM",
            subtitle="What the source would see without compensation.",
            caption="This is the problem waveform: voltage stays near sinusoidal, but current is distorted by harmonic and reactive demand.",
            info_key="graph:before",
        )
        self._scope_raw_step.add_channel(Channel("Vg", "Grid Voltage", "V", 1.0))
        self._scope_raw_step.add_channel(Channel("I_load", "Distorted Load Current", "A", 1.0))
        self._scope_raw_step.panel_selected.connect(self._set_info_topic)
        self._scope_raw_step.setMinimumHeight(200)
        layout.addWidget(self._scope_raw_step, stretch=1)

        self._scope_comp_step = OscilloscopeWidget(
            title="STEP 2 | INVERTER COMPENSATION CURRENT",
            subtitle="This is the circuit action that cancels the unwanted part of the load current.",
            caption="Orange is the total injected current. Purple represents harmonic cancellation demand. Cyan represents reactive compensation demand.",
            info_key="graph:compensation",
        )
        self._scope_comp_step.add_channel(Channel("I_comp", "Injected Inverter Current", "A", 1.0))
        self._scope_comp_step.add_channel(Channel("I_harm", "Harmonic Component", "A", 1.0))
        self._scope_comp_step.add_channel(Channel("I_react", "Reactive Component", "A", 1.0))
        self._scope_comp_step.panel_selected.connect(self._set_info_topic)
        self._scope_comp_step.setMinimumHeight(200)
        layout.addWidget(self._scope_comp_step, stretch=1)

        self._scope_clean_step = OscilloscopeWidget(
            title="STEP 3 | CLEANED SOURCE CURRENT",
            subtitle="What remains on the grid side after the inverter and filter finish the job.",
            caption="Green current should become smoother and closer to the dashed active-current target. That is the improvement the metrics quantify.",
            info_key="graph:after",
        )
        self._scope_clean_step.add_channel(Channel("Vg", "Grid Voltage", "V", 1.0))
        self._scope_clean_step.add_channel(Channel("I_grid", "Cleaned Grid Current", "A", 1.0))
        self._scope_clean_step.add_channel(Channel("I_ref", "Active Current Target", "A", 1.0))
        self._scope_clean_step.panel_selected.connect(self._set_info_topic)
        self._scope_clean_step.setMinimumHeight(200)
        layout.addWidget(self._scope_clean_step, stretch=1)

        return page

    def _make_metrics_panel(self):
        self._metrics = MetricsPanel()
        self._metrics.metric_selected.connect(self._set_info_topic)
        self._metrics.controller_selected.connect(self._set_info_topic)
        self._metrics.setFixedWidth(440)
        return self._metrics

    def _make_status_bar(self):
        frame = QFrame()
        frame.setObjectName("status_strip")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(18)

        self._lbl_ctrl = QLabel("CTRL: PI")
        self._lbl_mode = QLabel("MODE: 1PH-A")
        self._lbl_cycle = QLabel("CYCLE: 0")
        self._lbl_ieee = QLabel("IEEE 519: READY")
        self._lbl_thd = QLabel("THD: --")
        self._lbl_pf = QLabel("PF: --")
        self._lbl_eta = QLabel("ETA: --")

        for lbl in (
            self._lbl_ctrl,
            self._lbl_mode,
            self._lbl_cycle,
            self._lbl_ieee,
            self._lbl_thd,
            self._lbl_pf,
            self._lbl_eta,
        ):
            lbl.setObjectName("strip_tag")
            layout.addWidget(lbl)

        layout.addStretch()

        lbl_footer = QLabel("Circuit: PV -> DC Link -> VSI -> LCL Filter -> PCC -> Grid | Click any panel for explanation")
        lbl_footer.setObjectName("strip_footer")
        layout.addWidget(lbl_footer)
        return frame

    def _set_controller(self, name: str):
        self._ctrl_name = name
        self._engine.set_controller(name)

        for btn, ctrl in (
            (self._btn_PI, "PI"),
            (self._btn_PR, "PR"),
            (self._btn_MPC, "MPC"),
        ):
            btn.setChecked(ctrl == name)

        self._lbl_ctrl.setText(f"CTRL: {name}")
        ctrl_color = {"PI": "#bf2026", "PR": "#102d8f", "MPC": "#0f6f25"}.get(name, "#111111")
        self._info_controller.set_value(name, ctrl_color)
        self._refresh_info()

    def _set_phase_mode(self, mode: str):
        self._phase_mode = mode
        self._btn_single.setChecked(mode == "single")
        self._btn_three.setChecked(mode == "three")
        if mode == "single":
            self._selected_phase_idx = 0
        self._rebuild_engine()
        self._update_phase_buttons()
        self._update_titles()
        self._update_mode_labels()
        self._clear_plots()
        self._refresh_info()

    def _set_display_phase(self, idx: int):
        self._selected_phase_idx = idx
        self._update_phase_buttons()
        self._update_titles()
        self._update_mode_labels()
        self._refresh_info()

    def _set_view_mode(self, mode: str):
        self._view_mode = mode
        self._btn_story.setChecked(mode == "story")
        self._btn_step.setChecked(mode == "step")
        self._plot_stack.setCurrentIndex(0 if mode == "story" else 1)

    def _current_phase_label(self) -> str:
        labels = self._engine.phase_labels
        idx = min(self._selected_phase_idx, len(labels) - 1)
        return labels[idx]

    def _update_phase_buttons(self):
        active_count = 1 if self._phase_mode == "single" else 3
        for idx, btn in enumerate(self._phase_btns):
            enabled = idx < active_count
            btn.setEnabled(enabled)
            btn.setChecked(enabled and idx == min(self._selected_phase_idx, active_count - 1))

    def _update_mode_labels(self):
        mode_text = f"{'1PH' if self._phase_mode == 'single' else '3PH'}-{self._current_phase_label()}"
        self._info_mode.set_value(mode_text)
        self._metrics.set_phase_context(self._phase_mode, self._current_phase_label())
        self._lbl_mode.setText(f"MODE: {mode_text}")

    def _update_titles(self):
        phase = self._current_phase_label()
        prefix = f"{'1PH' if self._phase_mode == 'single' else '3PH'} | PHASE {phase}"

        self._scope_before_story.set_title(f"{prefix} | BEFORE | VOLTAGE + DISTORTED CURRENT")
        self._scope_after_story.set_title(f"{prefix} | AFTER | CLEANED SOURCE CURRENT")
        self._scope_error_story.set_title(f"{prefix} | TRACKING ERROR (TARGET - ACTUAL)")
        self._scope_raw_step.set_title(f"{prefix} | STEP 1 | RAW WAVEFORM")
        self._scope_comp_step.set_title(f"{prefix} | STEP 2 | INVERTER COMPENSATION")
        self._scope_clean_step.set_title(f"{prefix} | STEP 3 | CLEANED SOURCE CURRENT")
        self._spectrum.set_title(f"{prefix} | HARMONIC SPECTRUM BEFORE AND AFTER")

    def _rebuild_engine(self):
        self._engine = SimulationEngine()
        self._engine.set_phase_mode(self._phase_mode)
        self._engine.set_controller(self._ctrl_name)
        self._display_phase = 0
        self._last_result = None

    def _clear_plots(self):
        zeros = np.zeros(SimulationEngine.SAMPLES_PER_CYCLE)
        self._scope_before_story.update_all({"Vg": zeros, "I_load": zeros})
        self._scope_after_story.update_all({"Vg": zeros, "I_grid": zeros, "I_ref": zeros})
        self._scope_error_story.update_all({"I_error": zeros})
        self._scope_raw_step.update_all({"Vg": zeros, "I_load": zeros})
        self._scope_comp_step.update_all({"I_comp": zeros, "I_harm": zeros, "I_react": zeros})
        self._scope_clean_step.update_all({"Vg": zeros, "I_grid": zeros, "I_ref": zeros})
        self._spectrum.update_spectrum(np.array([]), np.array([]), np.array([]))

    def _toggle_run(self, checked: bool):
        if checked:
            self._running = True
            self._btn_run.setText("PAUSE")
            self._update_speed()
            self._timer.start()
        else:
            self._running = False
            self._btn_run.setText("RUN")
            self._timer.stop()

        self._metrics.set_running_state(self._running)

    def _update_speed(self):
        speed = self._speed_slider.value()
        interval = max(20, 250 - speed * 22)
        self._timer.setInterval(interval)

    def _reset(self):
        self._timer.stop()
        self._running = False
        self._btn_run.setChecked(False)
        self._btn_run.setText("RUN")
        self._rebuild_engine()

        self._lbl_cycle.setText("CYCLE: 0")
        self._lbl_ieee.setText("IEEE 519: READY")
        self._lbl_thd.setText("THD: --")
        self._lbl_pf.setText("PF: --")
        self._lbl_eta.setText("ETA: --")
        self._lbl_ieee.setStyleSheet(
            "background-color: #efe9dc; border: 1px solid #111111; padding: 1px 6px; "
            "color: #0b0f1a; font-family: 'DejaVu Sans Mono'; font-size: 10px; font-weight: bold;"
        )

        self._info_grid.set_value(f"{P.Vg_rms:.1f}")
        self._info_comp.set_value("--")
        self._info_thd_before.set_value("--")
        self._info_thd_after.set_value("--")
        self._info_pf.set_value("--")
        self._info_event.set_value("NORMAL", "#102d8f")

        self._metrics.set_running_state(False)
        self._metrics.set_event_state(False)
        self._metrics.set_phase_context(self._phase_mode, self._current_phase_label())
        self._clear_plots()
        self._set_info_topic("overview")

    def _open_settings(self):
        was_running = self._running
        if was_running:
            self._toggle_run(False)
            
        dialog = SettingsDialog(self)
        if dialog.exec():
            self._rebuild_engine()
            
        if was_running:
            self._btn_run.setChecked(True)
            self._toggle_run(True)

    def _inject_sag(self):
        # 30% drop for 20 cycles gives enough time to clearly see the visual drop and recovery
        self._engine.trigger_voltage_sag(depth=0.30, duration_cycles=20)
        self._info_event.set_value("SAG", "#bf2026")
        self._metrics.set_event_state(True)
        self._refresh_info()

    def _refresh_clock(self):
        stamp = QDateTime.currentDateTime().toString("dd-MM-yy hh:mm:ss")
        self._lbl_clock.setText(stamp)

    def _tick(self):
        result = self._engine.step_cycle()
        self._last_result = result

        phase_idx = min(self._selected_phase_idx, result.Vg.shape[0] - 1)
        phase_v = result.Vg[phase_idx]
        phase_load = result.I_load[phase_idx]
        phase_grid = result.I_grid[phase_idx]
        phase_ref = result.I_ref[phase_idx]
        phase_comp = result.I_comp[phase_idx]
        phase_harm = result.I_harm[phase_idx]
        phase_react = result.I_react[phase_idx]

        n = len(phase_v)
        phase_step = max(1, n // 40)
        self._display_phase = (self._display_phase + phase_step) % n

        def free_run(signal):
            return np.roll(signal, -self._display_phase)

        scaled_v = free_run(phase_v / self._VOLTAGE_PLOT_SCALE)

        self._scope_before_story.update_all({
            "Vg": scaled_v,
            "I_load": free_run(phase_load),
        })
        self._scope_after_story.update_all({
            "Vg": scaled_v,
            "I_grid": free_run(phase_grid),
            "I_ref": free_run(phase_ref),
        })
        self._scope_error_story.update_all({
            "I_error": free_run(phase_ref - phase_grid)
        })
        self._scope_raw_step.update_all({
            "Vg": scaled_v,
            "I_load": free_run(phase_load),
        })
        self._scope_comp_step.update_all({
            "I_comp": free_run(phase_comp),
            "I_harm": free_run(phase_harm),
            "I_react": free_run(phase_react),
        })
        self._scope_clean_step.update_all({
            "Vg": scaled_v,
            "I_grid": free_run(phase_grid),
            "I_ref": free_run(phase_ref),
        })

        alert = self._engine.sag_active
        self._scope_before_story.set_alert(alert)
        self._scope_after_story.set_alert(alert)
        self._scope_error_story.set_alert(alert)
        self._scope_raw_step.set_alert(alert)
        self._scope_comp_step.set_alert(alert)
        self._scope_clean_step.set_alert(alert)

        self._spectrum.update_spectrum(
            result.freqs,
            result.spectrum_before[phase_idx],
            result.spectrum_after[phase_idx],
        )

        self._metrics.update_metrics(result)
        self._metrics.set_event_state(self._engine.sag_active)
        self._metrics.set_phase_context(result.phase_mode, result.phase_labels[phase_idx])

        grid_rms = np.sqrt(np.mean(phase_v ** 2))
        self._info_grid.set_value(f"{grid_rms:.1f}")
        self._info_comp.set_value(f"{result.comp_rms:.2f}", "#c97d00")
        self._info_mode.set_value(
            f"{'1PH' if result.phase_mode == 'single' else '3PH'}-{result.phase_labels[phase_idx]}"
        )
        self._info_thd_before.set_value(f"{result.THD_before:.2f}", "#bf2026")
        self._info_thd_after.set_value(f"{result.THD_after:.2f}", "#0f6f25" if result.THD_after < 5.0 else "#bf2026")
        self._info_pf.set_value(f"{result.PF_after:.4f}")
        if self._engine.sag_active:
            self._info_event.set_value("SAG", "#bf2026")
        else:
            self._info_event.set_value("NORMAL", "#102d8f")

        self._lbl_mode.setText(
            f"MODE: {'1PH' if result.phase_mode == 'single' else '3PH'}-{result.phase_labels[phase_idx]}"
        )
        self._lbl_cycle.setText(f"CYCLE: {result.cycle}")
        self._lbl_thd.setText(f"THD: {result.THD_after:.2f}%")
        self._lbl_pf.setText(f"PF: {result.PF_after:.4f}")
        self._lbl_eta.setText(f"ETA: {result.efficiency * 100.0:.1f}%")

        if result.THD_after < 5.0:
            self._lbl_ieee.setText("IEEE 519: PASS")
            self._lbl_ieee.setStyleSheet(
                "background-color: #d7f0db; border: 1px solid #111111; padding: 1px 6px; "
                "color: #0b4a14; font-family: 'DejaVu Sans Mono'; font-size: 10px; font-weight: bold;"
            )
        else:
            self._lbl_ieee.setText("IEEE 519: FAIL")
            self._lbl_ieee.setStyleSheet(
                "background-color: #f3d1d1; border: 1px solid #111111; padding: 1px 6px; "
                "color: #7d0d0d; font-family: 'DejaVu Sans Mono'; font-size: 10px; font-weight: bold;"
            )

        self._refresh_clock()
        self._refresh_info()

    def _set_info_topic(self, topic: str):
        self._current_info_topic = topic
        self._sync_focus_states()
        self._refresh_info()

    def _sync_focus_states(self):
        graph_topic = self._current_info_topic
        for widget, key in (
            (self._scope_before_story, "graph:before"),
            (self._scope_after_story, "graph:after"),
            (self._scope_error_story, "graph:error"),
            (self._scope_raw_step, "graph:before"),
            (self._scope_comp_step, "graph:compensation"),
            (self._scope_clean_step, "graph:after"),
        ):
            widget.set_selected(graph_topic == key)

        self._spectrum.set_selected(graph_topic == "graph:spectrum")
        self._circuit.set_selected_block(
            self._current_info_topic if self._current_info_topic.startswith("circuit_") else ""
        )

    def _refresh_info(self):
        title, summary_html, detail_html = self._build_info_payload(self._current_info_topic)
        self._metrics.set_info_payload(title, summary_html, detail_html)

    def _build_info_payload(self, topic: str):
        result = self._last_result
        if result is None:
            return self._compose_payload(
                "SYSTEM OVERVIEW",
                [
                    ("What It Is", "This dashboard compares the distorted source/load current before compensation with the cleaned current after the inverter injects cancelling current."),
                    ("Current Value", "Run the simulation to populate THD, PF, reactive power, and compensation current values."),
                    ("Target / Better Direction", "Lower THD, higher PF, lower reactive power, and a smoother green source-current trace."),
                    ("Why Improving This Helps", "Cleaner current means less waveform pollution, less heating, better utilization of the source, and easier compliance with power-quality limits."),
                    ("How PI / PR / MPC Affect It", "PI gives baseline correction, PR targets specific harmonic frequencies, and MPC predicts future current error to reduce distortion more aggressively."),
                    ("How the Circuit Contributes", "The inverter bridge and LCL filter inject correcting current at the PCC so the grid sees a cleaner waveform."),
                ],
                [
                    ("Engineering Detail", "The model synthesizes a nonlinear load waveform, then drives a controller-truth current loop so the cleaned current and controller comparison are not only labels."),
                ],
            )

        phase_idx = min(self._selected_phase_idx, result.Vg.shape[0] - 1)
        phase_label = result.phase_labels[phase_idx]
        harmonic_lines = self._harmonic_lines(result, phase_idx)

        if topic == "overview":
            cards = self._controller_summary_table(result)
            return self._compose_payload(
                "SYSTEM OVERVIEW",
                [
                    ("What It Is", f"Phase {phase_label} shows the full story: <b><font color='#bf2026'>Red</font></b> is the distorted load current, <b><font color='#c97d00'>Orange</font></b> is the inverter's injected correction, and <b><font color='#0f6f25'>Green</font></b> is the final cleaned grid current."),
                    ("Current Value", f"THD moves from <b>{result.THD_before:.2f}%</b> to <b>{result.THD_after:.2f}%</b>. PF moves from <b>{result.PF_before:.4f}</b> to <b>{result.PF_after:.4f}</b>. Reactive compensation reaches <b>{result.reactive_comp_ratio * 100.0:.1f}%</b> of the unwanted reactive burden."),
                    ("Target / Better Direction", "Make the source current look as close as possible to the dashed active-current target while reducing harmonic bars and improving power factor."),
                    ("Why Improving This Helps", "Lower THD means cleaner current and lower heating. Higher PF means less non-working current. Lower reactive power means the source carries more useful power and less unwanted burden."),
                    ("How PI / PR / MPC Affect It", result.controller_truth.get(result.ctrl_name, {}).get("method", "")),
                    ("How the Circuit Contributes", "The nonlinear load creates distortion. Sensors measure it. The controller computes cancelling current. The VSI generates it. The LCL filter smooths it before the PCC sends cleaner current back to the grid."),
                    ("Grid Event Response", "During a sag, the controller detects the low voltage and immediately calculates a reactive current support command, forcing the inverter to inject leading reactive power to prop up the PCC voltage."),
                ],
                [
                    ("Controller comparison", cards),
                    ("Harmonic breakdown", harmonic_lines),
                    ("Power losses", self._loss_text(result)),
                ],
            )

        if topic == "graph:before":
            return self._compose_payload(
                "BEFORE | The Problem",
                [
                    ("What It Is", f"This graph shows the raw electrical condition at phase {phase_label} before compensation. The <b><font color='#102d8f'>Blue trace</font></b> is the ideal supply voltage reference. The <b><font color='#bf2026'>Red trace</font></b> is the dirty, distorted current drawn by the load."),
                    ("Current Value", f"Before compensation the current THD is <b>{result.THD_before:.2f}%</b> and PF is <b>{result.PF_before:.4f}</b>. Dominant unwanted content is currently <b>{html.escape(result.dominant_harmonic)}</b>."),
                    ("Target / Better Direction", "The source current should become smoother, closer to a sine wave, and closer to the active current target instead of carrying reactive and harmonic content."),
                    ("Why Improving This Helps", "If this raw current is left untouched, the source supplies harmonic pollution and reactive burden. That means poorer power quality and more useless current flow."),
                    ("How PI / PR / MPC Affect It", "All controllers see this same raw waveform as the starting point. PI corrects general error, PR is stronger at tuned harmonic orders, and MPC predicts future error before selecting the inverter voltage state."),
                    ("How the Circuit Contributes", "The problem begins at the nonlinear load and becomes visible at the PCC. Sensors detect this current so the controller can compute the correction."),
                ],
                [
                    ("Engineering Detail", f"Voltage is scaled for display so it can be compared on the same plot with current. Harmonic magnitudes before compensation are: {harmonic_lines}"),
                ],
            )

        if topic == "graph:after":
            return self._compose_payload(
                "AFTER GRAPH | CLEANED SOURCE CURRENT",
                [
                    ("What It Is", f"This graph shows what remains on the source side. The <b><font color='#0f6f25'>Green trace</font></b> is the cleaned grid current and the <b><font color='#444444'>Dashed Gray trace</font></b> is the ideal target sine wave."),
                    ("Current Value", f"After compensation, THD is <b>{result.THD_after:.2f}%</b>, PF is <b>{result.PF_after:.4f}</b>, reactive power drops to <b>{result.Q_out:.1f} var</b>, and the compensation current RMS is <b>{result.comp_rms:.2f} A</b>."),
                    ("Target / Better Direction", "The green current should align more closely with the dashed target and keep harmonic bars small, ideally below IEEE 519 limits."),
                    ("Why Improving This Helps", "This is the proof that the circuit is doing something different: the grid no longer carries the full harmonic/reactive burden of the load."),
                    ("How PI / PR / MPC Affect It", result.controller_truth.get(result.ctrl_name, {}).get("method", "")),
                    ("How the Circuit Contributes", "The inverter bridge creates the correcting waveform, and the LCL filter smooths it so the PCC delivers a cleaner current to the grid."),
                ],
                [
                    ("Engineering Detail", f"Estimated power-stage efficiency is <b>{result.efficiency * 100.0:.1f}%</b>. Harmonic reduction by order: {harmonic_lines}"),
                ],
            )

        if topic == "graph:error":
            return self._compose_payload(
                "ERROR GRAPH | TRACKING PERFORMANCE",
                [
                    ("What It Is", "This graph mathematically subtracts the actual grid current from the target reference to show you the instantaneous tracking error."),
                    ("Current Value", f"The peak error is roughly <b>{np.max(np.abs(result.I_ref[phase_idx] - result.I_grid[phase_idx])):.2f} A</b>. The RMS compensation injected was <b>{result.comp_rms:.2f} A</b>."),
                    ("Target / Better Direction", "A perfectly flat purple line exactly at zero means the controller achieved 100% ideal waveform tracking."),
                    ("Why Improving This Helps", "The tighter the error bounds, the lower your THD% will be. It directly measures controller capability."),
                    ("How PI / PR / MPC Affect It", "PI will show a steady sinusoidal error (unable to track AC well). PR will crush error at resonance frequencies. MPC will show high-frequency noise but tightly bound the overall error near zero."),
                    ("How the Circuit Contributes", "The controller commands correction, but physical limitations like switching speed and filter inductor size determine how fast the error can be driven to zero."),
                ],
                [
                    ("Engineering Detail", f"Error amplitude dynamically demonstrates the phase delay and attenuation of the closed-loop system."),
                ],
            )

        if topic == "graph:compensation":
            return self._compose_payload(
                "COMPENSATION GRAPH | WHAT THE CIRCUIT INJECTS",
                [
                    ("What It Is", "This graph isolates the inverter's action. <b><font color='#c97d00'>Orange</font></b> is the total injected current. <b><font color='#7a42b8'>Purple</font></b> is the harmonic cancellation part. <b><font color='#1a7da8'>Cyan</font></b> is the reactive compensation part."),
                    ("Current Value", f"The inverter is currently injecting <b>{result.comp_rms:.2f} A RMS</b>. Reactive burden reduction is <b>{result.reactive_comp_ratio * 100.0:.1f}%</b> and the dominant harmonic being reduced is <b>{html.escape(result.dominant_harmonic)}</b>."),
                    ("Target / Better Direction", "Inject only the unwanted part of the current so the grid side is left with mostly active fundamental current."),
                    ("Why Improving This Helps", "This is the exact mechanism of harmonic reduction: the inverter creates a cancelling current that opposes the unwanted harmonic and reactive parts of the load current."),
                    ("How PI / PR / MPC Affect It", "PI follows the overall error, PR strongly reinforces tuned frequencies, and MPC chooses the switching level that best reduces predicted future error."),
                    ("How the Circuit Contributes", "Sensors measure the error, the controller computes the current command, the inverter generates the voltage needed to track it, and the filter shapes that command into a usable current."),
                ],
                [
                    ("Engineering Detail", f"Loss breakdown while producing the compensation current: {self._loss_text(result)}"),
                ],
            )

        if topic == "graph:spectrum":
            return self._compose_payload(
                "HARMONIC SPECTRUM | WHICH ORDERS WERE REMOVED",
                [
                    ("What It Is", "This spectrum compares the strongest harmonic orders before and after compensation. It tells you which parts of the distortion were actually reduced."),
                    ("Current Value", f"Current dominant reduction is <b>{html.escape(result.dominant_harmonic)}</b>. The selected controller is {result.ctrl_name}, and the most improved orders are <b>{html.escape(result.controller_truth.get(result.ctrl_name, {}).get('best_orders', '--'))}</b>."),
                    ("Target / Better Direction", "Smaller green bars after compensation, especially on the dominant harmonic orders."),
                    ("Why Improving This Helps", "Each bar removed from the spectrum means less harmonic current in the source, which directly improves THD and waveform quality."),
                    ("How PI / PR / MPC Affect It", "PR and MPC should pull down tuned or predicted harmonic orders more strongly than PI. That is why the controller comparison is meaningful."),
                    ("How the Circuit Contributes", "The controller and inverter decide the cancelling waveform, while the LCL filter keeps that response usable at the PCC."),
                ],
                [
                    ("Engineering Detail", harmonic_lines),
                ],
            )

        if topic.startswith("metric:"):
            metric_key = topic.split(":", 1)[1]
            return self._metric_payload(metric_key, result, phase_label, harmonic_lines)

        if topic.startswith("controller:"):
            ctrl_name = topic.split(":", 1)[1]
            return self._controller_payload(ctrl_name, result)

        if topic.startswith("circuit_"):
            return self._circuit_payload(topic, result)

        return self._build_info_payload("overview")

    def _metric_payload(self, metric_key: str, result: SimResult, phase_label: str, harmonic_lines: str):
        if metric_key == "THD_before":
            return self._compose_payload(
                "METRIC | THD BEFORE",
                [
                    ("What It Is", f"THD before is the harmonic distortion in the raw current on phase {phase_label}, before our circuit injects compensation."),
                    ("Current Value", f"Current THD before compensation is <b>{result.THD_before:.2f}%</b>."),
                    ("Target / Better Direction", "This value should be reduced as much as possible, ideally below 5% after compensation."),
                    ("Why Improving This Helps", "Lower THD means the source current is closer to a pure sine wave, which reduces heating, losses, and waveform pollution."),
                    ("How PI / PR / MPC Affect It", "This value is the starting point for all controllers; it tells you how difficult the cleanup problem is."),
                    ("How the Circuit Contributes", "The load creates the distortion. The controller-inverter-filter path is what reduces it afterwards."),
                ],
                [("Engineering Detail", harmonic_lines)],
            )
        if metric_key == "THD_after":
            return self._compose_payload(
                "METRIC | THD AFTER",
                [
                    ("What It Is", "THD after measures how much distortion is left in the source current after our inverter and filter act."),
                    ("Current Value", f"Current THD after compensation is <b>{result.THD_after:.2f}%</b>. IEEE 519 status is currently <b>{'PASS' if result.THD_after < 5.0 else 'FAIL'}</b>."),
                    ("Target / Better Direction", "Lower is better. Below 5% is the practical quality target used in this dashboard."),
                    ("Why Improving This Helps", "This is the clearest proof that our design is different: the source sees a cleaner current than the raw load would have drawn by itself."),
                    ("How PI / PR / MPC Affect It", result.controller_truth.get(result.ctrl_name, {}).get("method", "")),
                    ("How the Circuit Contributes", "The controller tells the inverter what cancelling current to inject. The filter smooths it. The PCC then shows the cleaned result."),
                ],
                [("Engineering Detail", harmonic_lines)],
            )
        if metric_key == "PF_before":
            return self._compose_payload(
                "METRIC | PF BEFORE",
                [
                    ("What It Is", "PF before is the raw power factor before compensation."),
                    ("Current Value", f"Current PF before compensation is <b>{result.PF_before:.4f}</b>."),
                    ("Target / Better Direction", "Power factor should move closer to 1.0."),
                    ("Why Improving This Helps", "A poor power factor means the source is supplying extra non-working current in addition to useful power."),
                    ("How PI / PR / MPC Affect It", "All controllers start from this same raw PF. The stronger the reactive cancellation, the higher the corrected PF becomes."),
                    ("How the Circuit Contributes", "Reactive-current compensation is one major part of the inverter current injection."),
                ],
                [("Engineering Detail", f"Load reactive power before compensation is <b>{result.Q_load:.1f} var</b>.")],
            )
        if metric_key == "PF_after":
            return self._compose_payload(
                "METRIC | PF AFTER",
                [
                    ("What It Is", "PF after shows how closely the cleaned source current is aligned with useful power transfer."),
                    ("Current Value", f"Current PF after compensation is <b>{result.PF_after:.4f}</b>."),
                    ("Target / Better Direction", "Power factor should be as close to unity as possible."),
                    ("Why Improving This Helps", "A higher PF means the source is spending less current on reactive burden and more on useful power delivery."),
                    ("How PI / PR / MPC Affect It", result.controller_truth.get(result.ctrl_name, {}).get("method", "")),
                    ("How the Circuit Contributes", "The controller and inverter cancel the reactive component so the remaining source current becomes more useful."),
                ],
                [("Engineering Detail", f"Reactive compensation ratio is <b>{result.reactive_comp_ratio * 100.0:.1f}%</b>.")],
            )
        if metric_key == "P_out":
            return self._compose_payload(
                "METRIC | ACTIVE POWER",
                [
                    ("What It Is", "Active power is the useful real power still delivered on the source side after compensation."),
                    ("Current Value", f"Current active power is <b>{result.P_out:.1f} W</b>."),
                    ("Target / Better Direction", "Keep useful power delivery visible while reducing harmonic and reactive pollution."),
                    ("Why Improving This Helps", "It shows we are cleaning the waveform without removing the useful power transfer the load still needs."),
                    ("How PI / PR / MPC Affect It", "Better controllers usually preserve useful power while reducing the unwanted components more efficiently."),
                    ("How the Circuit Contributes", "The inverter is not trying to cancel useful active current. It targets the unwanted harmonic and reactive portions."),
                ],
                [("Engineering Detail", f"PV-side available power in this demo is <b>{result.P_pv:.1f} W</b>.")],
            )
        if metric_key == "Q_out":
            return self._compose_payload(
                "METRIC | REACTIVE POWER",
                [
                    ("What It Is", "Reactive power tells you how much non-working current burden is still present after compensation."),
                    ("Current Value", f"Current reactive power after compensation is <b>{result.Q_out:.1f} var</b>."),
                    ("Target / Better Direction", "Move this value toward zero."),
                    ("Why Improving This Helps", "Lower reactive power means the source carries less current that does not contribute to useful work."),
                    ("How PI / PR / MPC Affect It", "Controllers that track the compensating current better usually reduce reactive burden more strongly."),
                    ("How the Circuit Contributes", "The cyan reactive component in the compensation graph is specifically the current used to reduce this value."),
                ],
                [("Engineering Detail", f"Before compensation the load reactive power is <b>{result.Q_load:.1f} var</b>.")],
            )
        if metric_key == "comp_rms":
            return self._compose_payload(
                "METRIC | COMPENSATION CURRENT",
                [
                    ("What It Is", "This is the RMS magnitude of the current our inverter injects to cancel the unwanted part of the load current."),
                    ("Current Value", f"Current injected compensation is <b>{result.comp_rms:.2f} A RMS</b>."),
                    ("Target / Better Direction", "Inject enough current to clean the source side, but not more than needed."),
                    ("Why Improving This Helps", "This value tells the viewer what our circuit is actually doing differently. The inverter is actively shaping current, not only observing it."),
                    ("How PI / PR / MPC Affect It", "Different controllers produce the needed compensation with different tracking quality and switching behavior."),
                    ("How the Circuit Contributes", "The inverter bridge creates this current and the LCL filter makes it suitable for injection at the PCC."),
                ],
                [("Engineering Detail", self._loss_text(result))],
            )
        return self._compose_payload(
            "METRIC | ESTIMATED EFFICIENCY",
            [
                ("What It Is", "Estimated efficiency compares useful conditioned power with the modeled loss burden of the inverter and filter stage."),
                ("Current Value", f"Current estimated efficiency is <b>{result.efficiency * 100.0:.1f}%</b>."),
                ("Target / Better Direction", "Higher is better, provided THD and PF are still improving."),
                ("Why Improving This Helps", "A good controller should improve power quality without forcing excessive switching or conduction losses."),
                ("How PI / PR / MPC Affect It", "Controllers that achieve lower THD with similar or lower injected current can appear more efficient in this model."),
                ("How the Circuit Contributes", "Losses come from the switching devices and passive filter components used to generate the compensation current."),
            ],
            [("Engineering Detail", self._loss_text(result))],
        )

    def _controller_payload(self, ctrl_name: str, result: SimResult):
        snapshot = result.controller_truth.get(ctrl_name, {})
        return self._compose_payload(
            f"CONTROLLER | {ctrl_name}",
            [
                ("What It Is", f"{ctrl_name} is one of the controller choices used to force the inverter current to follow the compensation demand."),
                ("Current Value", f"For the current cycle, {ctrl_name} achieves THD <b>{snapshot.get('THD_after', 0.0):.2f}%</b>, PF <b>{snapshot.get('PF_after', 0.0):.4f}</b>, compensation current <b>{snapshot.get('comp_rms', 0.0):.2f} A</b>, and estimated efficiency <b>{snapshot.get('efficiency', 0.0) * 100.0:.1f}%</b>."),
                ("Target / Better Direction", "Reduce THD, raise PF, lower residual reactive power, and do it with a reasonable loss burden."),
                ("Why Improving This Helps", "Controller quality decides how well the inverter can turn the circuit hardware into actual waveform cleanup."),
                ("How PI / PR / MPC Affect It", snapshot.get("method", "")),
                ("How the Circuit Contributes", "The controller uses sensor measurements to command the inverter bridge, which then pushes current through the LCL filter into the PCC."),
            ],
            [
                ("Engineering Detail", f"Best harmonic cleanup is on <b>{html.escape(snapshot.get('best_orders', '--'))}</b>. Dominant removed harmonic is <b>{html.escape(snapshot.get('dominant_harmonic', '--'))}</b>. Control effectiveness score is <b>{snapshot.get('control_effectiveness', 0.0):.1f}/100</b>."),
            ],
        )

    def _circuit_payload(self, topic: str, result: SimResult):
        load_harmonics = self._harmonic_lines(result, min(self._selected_phase_idx, result.Vg.shape[0] - 1))
        payloads = {
            "circuit_pv": (
                "CIRCUIT | PV SOURCE",
                [
                    ("What It Is", "This is the DC energy source feeding the inverter stage."),
                    ("Current Value", f"Available PV-side power in the demo is <b>{result.P_pv:.1f} W</b>."),
                    ("Target / Better Direction", "Keep enough DC support available for the inverter to generate the required compensation current."),
                    ("Why Improving This Helps", "The inverter cannot inject corrective current without an energy source and a stable DC bus behind it."),
                    ("How PI / PR / MPC Affect It", "The controller does not change the PV source itself; it changes how effectively the inverter uses the DC source to shape current."),
                    ("How the Circuit Contributes", "PV feeds the DC link, and the DC link feeds the inverter bridge that creates the compensation waveform."),
                ],
                [("Engineering Detail", "This demo focuses on grid-current conditioning, not MPPT dynamics. The PV block is shown mainly to explain the real hardware energy path.")],
            ),
            "circuit_dc_link": (
                "CIRCUIT | DC LINK",
                [
                    ("What It Is", "The DC link is the energy buffer between the PV side and the inverter bridge."),
                    ("Current Value", f"The DC-link level is modeled at <b>{P.Vdc:.0f} V</b>."),
                    ("Target / Better Direction", "Keep the DC link stable enough that the inverter can generate the commanded correction voltage."),
                    ("Why Improving This Helps", "Without a stiff DC link, the controller command cannot become a reliable compensation current."),
                    ("How PI / PR / MPC Affect It", "All controllers rely on the DC link because they ultimately command inverter voltage."),
                    ("How the Circuit Contributes", "The DC link is the immediate energy reservoir that the VSI uses when producing the cancelling waveform."),
                ],
                [("Engineering Detail", "A stable DC bus improves current-tracking headroom, especially during stronger compensation demand.")],
            ),
            "circuit_inverter": (
                "CIRCUIT | VSI / H-BRIDGE",
                [
                    ("What It Is", "This is the stage that turns the controller command into an actual correcting current waveform."),
                    ("Current Value", f"It is currently producing <b>{result.comp_rms:.2f} A RMS</b> of compensation current."),
                    ("Target / Better Direction", "Track the compensation demand accurately without excessive switching loss."),
                    ("Why Improving This Helps", "This block is the direct reason the after-graph looks different from the before-graph."),
                    ("How PI / PR / MPC Affect It", "Each controller changes how the inverter voltage is chosen to force the compensation current to follow the demand."),
                    ("How the Circuit Contributes", "The inverter is the actuator of the whole correction process."),
                ],
                [("Engineering Detail", self._loss_text(result))],
            ),
            "circuit_filter": (
                "CIRCUIT | LCL FILTER",
                [
                    ("What It Is", "The LCL filter smooths the inverter output so the current injected at the PCC is cleaner than the raw switching waveform."),
                    ("Current Value", f"L1 = <b>{P.L1 * 1e3:.1f} mH</b>, L2 = <b>{P.L2 * 1e3:.1f} mH</b>, Cf = <b>{P.Cf * 1e6:.1f} uF</b>."),
                    ("Target / Better Direction", "Pass the useful compensation current while reducing switching ripple."),
                    ("Why Improving This Helps", "Without filtering, the inverter could fix one problem while injecting another high-frequency disturbance."),
                    ("How PI / PR / MPC Affect It", "Better controllers still depend on the filter to deliver a grid-friendly current shape."),
                    ("How the Circuit Contributes", "This is the stage that makes the compensation current practical at the PCC."),
                ],
                [("Engineering Detail", "The estimated loss model includes copper losses in L1/L2 and ESR loss in the filter capacitor.")],
            ),
            "circuit_pcc": (
                "CIRCUIT | PCC",
                [
                    ("What It Is", "The point of common coupling is where the nonlinear load, grid, and inverter compensation meet."),
                    ("Current Value", f"At the PCC, THD moves from <b>{result.THD_before:.2f}%</b> to <b>{result.THD_after:.2f}%</b>."),
                    ("Target / Better Direction", "Make the source current leaving the PCC look cleaner than the raw load current entering it."),
                    ("Why Improving This Helps", "The PCC is the proof point of the design because it shows the net effect of the entire circuit."),
                    ("How PI / PR / MPC Affect It", "Different controllers change how much of the unwanted current is canceled before it reaches the source side."),
                    ("How the Circuit Contributes", "Every block in the circuit acts to improve what the PCC delivers to the grid."),
                ],
                [("Engineering Detail", "The PCC is where the distorted load current and the inverter compensation current algebraically combine.")],
            ),
            "circuit_grid": (
                "CIRCUIT | GRID",
                [
                    ("What It Is", "This represents what the upstream source actually sees after compensation."),
                    ("Current Value", f"The grid-side current after compensation has THD <b>{result.THD_after:.2f}%</b> and PF <b>{result.PF_after:.4f}</b>."),
                    ("Target / Better Direction", "Make the source current cleaner and closer to the active-current target."),
                    ("Why Improving This Helps", "The whole purpose of the design is to keep the grid from carrying the load's full harmonic and reactive burden."),
                    ("How PI / PR / MPC Affect It", result.controller_truth.get(result.ctrl_name, {}).get("method", "")),
                    ("How the Circuit Contributes", "The inverter, filter, and PCC work together so the grid sees the cleaned result instead of the raw nonlinear-load waveform."),
                ],
                [("Engineering Detail", "Grid-side power factor and THD are the two quickest indicators that the design is improving source-side power quality.")],
            ),
            "circuit_load": (
                "CIRCUIT | NONLINEAR LOAD",
                [
                    ("What It Is", "This is the source of the distortion problem in the demo."),
                    ("Current Value", f"The load current before compensation has THD <b>{result.THD_before:.2f}%</b> and reactive power <b>{result.Q_load:.1f} var</b>."),
                    ("Target / Better Direction", "The load may stay nonlinear, but the source should not have to supply the full distorted current profile."),
                    ("Why Improving This Helps", "This makes the demo realistic: many real systems cannot change the load, so they clean the source current instead."),
                    ("How PI / PR / MPC Affect It", "Controllers do not make the load linear. They make the inverter cancel the load's unwanted current components."),
                    ("How the Circuit Contributes", "The rest of the circuit exists to stop the distorted load current from appearing unchanged at the source side."),
                ],
                [("Engineering Detail", load_harmonics)],
            ),
            "circuit_sensors": (
                "CIRCUIT | SENSORS",
                [
                    ("What It Is", "Sensors provide the measured voltage and current that the controller uses to compute the compensation command."),
                    ("Current Value", "In the dashboard they are represented by the live waveform and metric updates each cycle."),
                    ("Target / Better Direction", "The controller needs an accurate enough picture of the waveform to decide what must be canceled."),
                    ("Why Improving This Helps", "Without sensing, the controller has no idea what is wrong with the current or whether its action improved anything."),
                    ("How PI / PR / MPC Affect It", "All three controllers use measured current error differently, but all depend on the same feedback path."),
                    ("How the Circuit Contributes", "Sensors close the loop between the electrical problem at the PCC and the digital control action."),
                ],
                [("Engineering Detail", "In the model, controller-truth analysis uses the same synthesized cycle waveform to evaluate PI, PR, and MPC on equal footing.")],
            ),
            "circuit_controller": self._controller_payload(result.ctrl_name, result),
        }
        payload = payloads.get(topic)
        if payload is None:
            return self._build_info_payload("overview")
        if isinstance(payload, tuple) and len(payload) == 3 and isinstance(payload[1], list):
            return self._compose_payload(payload[0], payload[1], payload[2])
        return payload

    def _controller_summary_table(self, result: SimResult) -> str:
        parts = []
        for ctrl_name in ("PI", "PR", "MPC"):
            snapshot = result.controller_truth.get(ctrl_name, {})
            parts.append(
                f"<p><b>{ctrl_name}</b>: THD {snapshot.get('THD_after', 0.0):.2f}% | "
                f"PF {snapshot.get('PF_after', 0.0):.4f} | "
                f"eta {snapshot.get('efficiency', 0.0) * 100.0:.1f}% | "
                f"best orders {html.escape(snapshot.get('best_orders', '--'))}</p>"
            )
        return "".join(parts)

    def _harmonic_lines(self, result: SimResult, phase_idx: int) -> str:
        if result.harmonics_before.size == 0:
            return "No harmonic data yet."

        rows = []
        for idx, order in enumerate(result.harmonic_orders):
            if int(order) == 1:
                continue
            before = float(result.harmonics_before[phase_idx, idx])
            after = float(result.harmonics_after[phase_idx, idx])
            reduction = float(result.harmonic_reduction[phase_idx, idx])
            rows.append((before, order, after, reduction))
        rows.sort(reverse=True)

        if not rows:
            return "No harmonic orders available."

        text = []
        for before, order, after, reduction in rows[:4]:
            text.append(
                f"<p><b>{int(order)}h</b>: {before:.2f} A before -> {after:.2f} A after "
                f"({reduction:.1f}% reduction)</p>"
            )
        return "".join(text)

    def _loss_text(self, result: SimResult) -> str:
        loss = result.loss_breakdown
        if not loss:
            return "Loss estimate not available yet."
        return (
            f"Conduction <b>{loss.get('conduction', 0.0):.2f} W</b>, "
            f"switching <b>{loss.get('switching', 0.0):.2f} W</b>, "
            f"L1 copper <b>{loss.get('l1_copper', 0.0):.2f} W</b>, "
            f"L2 copper <b>{loss.get('l2_copper', 0.0):.2f} W</b>, "
            f"capacitor ESR <b>{loss.get('capacitor_esr', 0.0):.2f} W</b>, "
            f"total <b>{loss.get('total', 0.0):.2f} W</b>."
        )

    def _compose_payload(self, title: str, sections: list[tuple[str, str]], detail_sections: list[tuple[str, str]]):
        def render(items):
            return "".join(
                f"<h3>{html.escape(header)}</h3><p>{body}</p>"
                for header, body in items
            )

        return title, render(sections), render(detail_sections)
