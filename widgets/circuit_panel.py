"""
widgets/circuit_panel.py
Simulink-style annotated block-diagram view of the inverter circuit.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Component info shown beneath each block
_BLOCK_INFO = {
    "circuit_pv": "Vpv = 9–36V\nMPPT η ≈ 98.5%",
    "circuit_dc_link": "Vdc = 650V\nCapacitor bus",
    "circuit_inverter": "4× IGBT\nfsw = 10 kHz",
    "circuit_filter": "L₁=5mH  Cf=10µF\nL₂=2mH  Rf=0.1Ω",
    "circuit_pcc": "Point of\nCommon Coupling",
    "circuit_grid": "230V RMS\n50 Hz AC",
    "circuit_load": "Nonlinear\nTHD ≈ 37%",
    "circuit_sensors": "V and I\nmeasurement",
    "circuit_controller": "PI / PR / MPC\ndigital control",
}


class CircuitBlock(QPushButton):
    """A single block in the circuit diagram, styled to look like a Simulink block."""
    def __init__(self, key: str, label: str, info: str = "", parent=None):
        super().__init__(parent)
        self.key = key
        self.setCheckable(True)
        self.setObjectName("circuit_block")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        name_lbl = QLabel(label)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(
            "font-family: 'DejaVu Sans Mono'; font-size: 10px; font-weight: bold;"
            "color: inherit; background: transparent; border: none;"
        )
        name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(name_lbl)

        if info:
            info_lbl = QLabel(info)
            info_lbl.setAlignment(Qt.AlignCenter)
            info_lbl.setStyleSheet(
                "font-family: 'DejaVu Sans'; font-size: 8px; color: #555555;"
                "background: transparent; border: none;"
            )
            info_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
            layout.addWidget(info_lbl)

        self.setMinimumHeight(50)
        self.setMinimumWidth(90)


class CircuitPanel(QWidget):
    block_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: dict[str, list[QPushButton]] = {}
        self._selected_key = ""
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("CIRCUIT DIAGRAM  |  SIMULINK-STYLE BLOCK VIEW")
        title.setObjectName("panel_title")
        outer.addWidget(title)

        subtitle = QLabel(
            "Click any block to see what it does and how it improves power quality. "
            "Top row: power flow from PV to grid. Middle: load connection at PCC. Bottom: control feedback loop."
        )
        subtitle.setObjectName("panel_subtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        panel = QFrame()
        panel.setObjectName("panel")
        outer.addWidget(panel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Row label
        pwr_label = QLabel("⚡ POWER PATH (DC → AC conversion and filtering)")
        pwr_label.setStyleSheet(
            "font-family: 'DejaVu Sans'; font-size: 9px; font-weight: bold;"
            "color: #2036c7; background: transparent; border: none; padding: 0;"
        )
        layout.addWidget(pwr_label)
        layout.addLayout(self._build_power_path())

        layout.addSpacing(4)

        load_label = QLabel("🔌 LOAD PATH (nonlinear load connects at PCC)")
        load_label.setStyleSheet(
            "font-family: 'DejaVu Sans'; font-size: 9px; font-weight: bold;"
            "color: #bf2026; background: transparent; border: none; padding: 0;"
        )
        layout.addWidget(load_label)
        layout.addLayout(self._build_branch_path())

        layout.addSpacing(4)

        ctrl_label = QLabel("🧠 CONTROL PATH (sensors → controller → inverter)")
        ctrl_label.setStyleSheet(
            "font-family: 'DejaVu Sans'; font-size: 9px; font-weight: bold;"
            "color: #0f6f25; background: transparent; border: none; padding: 0;"
        )
        layout.addWidget(ctrl_label)
        layout.addLayout(self._build_control_path())

    def _build_power_path(self):
        layout = QHBoxLayout()
        layout.setSpacing(4)

        for key, label in (
            ("circuit_pv", "PV ARRAY"),
            ("circuit_dc_link", "DC LINK"),
            ("circuit_inverter", "H-BRIDGE\nINVERTER"),
            ("circuit_filter", "LCL\nFILTER"),
            ("circuit_pcc", "PCC"),
            ("circuit_grid", "GRID"),
        ):
            layout.addWidget(self._make_block(key, label), stretch=1)
            if key != "circuit_grid":
                layout.addWidget(self._arrow("→"))
        return layout

    def _build_branch_path(self):
        layout = QHBoxLayout()
        layout.setSpacing(4)

        layout.addWidget(self._make_block("circuit_load", "NONLINEAR\nLOAD"), stretch=1)
        layout.addWidget(self._arrow("→"))
        layout.addWidget(self._make_block("circuit_pcc", "PCC"), stretch=1)
        layout.addWidget(self._arrow("→"))

        result_lbl = QLabel("grid sees\ncleaned current")
        result_lbl.setAlignment(Qt.AlignCenter)
        result_lbl.setStyleSheet(
            "font-family: 'DejaVu Sans'; font-size: 9px; font-style: italic;"
            "color: #0f6f25; background: transparent; border: none;"
        )
        layout.addWidget(result_lbl, stretch=1)
        layout.addStretch(3)  # balance with power path
        return layout

    def _build_control_path(self):
        layout = QHBoxLayout()
        layout.setSpacing(4)

        layout.addWidget(self._make_block("circuit_sensors", "SENSORS\n(V, I)"), stretch=1)
        layout.addWidget(self._arrow("→"))
        layout.addWidget(self._make_block("circuit_controller", "DIGITAL\nCONTROLLER"), stretch=1)
        layout.addWidget(self._arrow("→"))
        layout.addWidget(self._make_block("circuit_inverter", "H-BRIDGE\nINVERTER"), stretch=1)
        layout.addStretch(3)  # balance with power path

        return layout

    def _make_block(self, key: str, label: str):
        info = _BLOCK_INFO.get(key, "")
        btn = CircuitBlock(key, label, info)
        btn.clicked.connect(lambda checked=False, k=key: self.block_selected.emit(k))
        self._buttons.setdefault(key, []).append(btn)
        return btn

    def _arrow(self, text: str):
        lbl = QLabel(text)
        lbl.setObjectName("circuit_arrow")
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2036c7;"
            "background: transparent; border: none; min-width: 18px;"
        )
        return lbl

    def set_selected_block(self, key: str):
        self._selected_key = key
        for block_key, buttons in self._buttons.items():
            for button in buttons:
                button.setChecked(block_key == key)
