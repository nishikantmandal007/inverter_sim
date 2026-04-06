"""
widgets/metrics.py
Metrics, controller comparison, and context-sensitive explanation drawer.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class MetricCell(QFrame):
    clicked = Signal(str)

    def __init__(self, key: str, label: str, unit: str, accent: str, parent=None):
        super().__init__(parent)
        self._key = key
        self._accent = accent
        self.setObjectName("metric_cell")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        self._label = QLabel(label)
        self._label.setObjectName("metric_label")
        layout.addWidget(self._label)

        self._value = QLabel("0.000")
        self._value.setObjectName("metric_value")
        self._value.setAlignment(Qt.AlignCenter)
        self._value.setStyleSheet(f"color: {accent};")
        layout.addWidget(self._value, stretch=1)

        self._unit = QLabel(unit)
        self._unit.setObjectName("metric_unit")
        self._unit.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._unit)

    def mousePressEvent(self, event):
        self.clicked.emit(f"metric:{self._key}")
        super().mousePressEvent(event)

    def set_value(self, text: str):
        self._value.setText(text)


class StatusRow(QFrame):
    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("status_row")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        self._label = QLabel(label)
        self._label.setObjectName("status_name")
        layout.addWidget(self._label, stretch=1)

        self._value = QLabel("READY")
        self._value.setObjectName("status_value")
        self._value.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._value, stretch=0)

    def set_value(self, text: str, color: str):
        self._value.setText(text)
        self._value.setStyleSheet(
            "border: 1px solid #111111; padding: 2px 8px; "
            f"background-color: {color}; color: #111111; font-weight: bold;"
        )


class ControllerCard(QFrame):
    clicked = Signal(str)

    def __init__(self, ctrl_name: str, accent: str, parent=None):
        super().__init__(parent)
        self._ctrl_name = ctrl_name
        self._accent = accent
        self.setObjectName("controller_card")
        self.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        self._title = QLabel(ctrl_name)
        self._title.setObjectName("controller_card_title")
        self._title.setStyleSheet(f"color: {accent};")
        layout.addWidget(self._title)

        self._headline = QLabel("THD -- | PF --")
        self._headline.setObjectName("controller_card_headline")
        layout.addWidget(self._headline)

        self._body = QLabel("Waiting for controller comparison data.")
        self._body.setObjectName("controller_card_body")
        self._body.setWordWrap(True)
        layout.addWidget(self._body)

    def mousePressEvent(self, event):
        self.clicked.emit(f"controller:{self._ctrl_name}")
        super().mousePressEvent(event)

    def set_snapshot(self, snapshot: dict, selected: bool):
        self._headline.setText(
            f"THD {snapshot['THD_after']:.2f}% | PF {snapshot['PF_after']:.4f} | eta {snapshot['efficiency'] * 100.0:.1f}%"
        )
        self._body.setText(
            f"Best cleanup: {snapshot['best_orders']}. {snapshot['method']}"
        )
        self.setStyleSheet(
            "QFrame#controller_card {"
            f"background-color: {'#ebf0ff' if selected else '#fcfbf6'};"
            f"border: {'2px' if selected else '1px'} solid {'#2036c7' if selected else '#111111'};"
            "}"
        )


class InfoDrawer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._summary_html = "<p>Select a graph, metric, or circuit block to explain it here.</p>"
        self._detail_html = ""
        self._detail_visible = False
        self._build_ui()
        self._render()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("I | WHY THIS DEMO MATTERS")
        title.setObjectName("panel_title")
        outer.addWidget(title)

        body = QFrame()
        body.setObjectName("panel")
        outer.addWidget(body)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self._topic = QLabel("SYSTEM OVERVIEW")
        self._topic.setObjectName("section_label")
        toolbar.addWidget(self._topic, stretch=1)

        self._toggle = QPushButton("SHOW ENGINEERING DETAIL")
        self._toggle.clicked.connect(self._toggle_detail)
        toolbar.addWidget(self._toggle, stretch=0)

        layout.addLayout(toolbar)

        self._browser = QTextBrowser()
        self._browser.setObjectName("info_browser")
        self._browser.setOpenExternalLinks(False)
        self._browser.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self._browser, stretch=1)

    def _toggle_detail(self):
        self._detail_visible = not self._detail_visible
        self._toggle.setText(
            "HIDE ENGINEERING DETAIL" if self._detail_visible else "SHOW ENGINEERING DETAIL"
        )
        self._render()

    def set_payload(self, title: str, summary_html: str, detail_html: str = ""):
        self._topic.setText(title)
        self._summary_html = self._coerce_html(summary_html)
        self._detail_html = self._coerce_html(detail_html)
        self._render()

    def _render(self):
        html = self._summary_html
        if self._detail_visible and self._detail_html:
            html += "<hr><h3>Engineering Detail</h3>" + self._detail_html
        self._browser.setHtml(html)

    def _coerce_html(self, value) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            parts = []
            for item in value:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    header, body = item
                    parts.append(f"<h3>{header}</h3><p>{body}</p>")
                else:
                    parts.append(f"<p>{item}</p>")
            return "".join(parts)
        return str(value)


class MetricsPanel(QWidget):
    metric_selected = Signal(str)
    controller_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase_context = "1PH | A"
        self._build_ui()
        self.set_running_state(False)
        self.set_event_state(False)

    def _build_ui(self):
        from PySide6.QtWidgets import QScrollArea

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        title = QLabel("VALUES, COMPARISON, AND EXPLANATION")
        title.setObjectName("panel_title")
        outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        body = QFrame()
        body.setObjectName("panel")
        scroll.setWidget(body)
        outer.addWidget(scroll, stretch=1)

        layout = QVBoxLayout(body)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        grid = QGridLayout()
        grid.setSpacing(8)
        self._cells = {
            "THD_before": MetricCell("THD_before", "THD BEFORE", "%", "#bf2026"),
            "THD_after": MetricCell("THD_after", "THD AFTER", "%", "#0f6f25"),
            "PF_before": MetricCell("PF_before", "PF BEFORE", "PF", "#8a5c00"),
            "PF_after": MetricCell("PF_after", "PF AFTER", "PF", "#102d8f"),
            "P_out": MetricCell("P_out", "ACTIVE POWER", "W", "#102d8f"),
            "Q_out": MetricCell("Q_out", "REACTIVE POWER", "VAR", "#8a5c00"),
            "comp_rms": MetricCell("comp_rms", "COMP CURRENT", "A", "#c97d00"),
            "efficiency": MetricCell("efficiency", "EST. EFFICIENCY", "%", "#0f6f25"),
        }

        for row, pair in enumerate((
            ("THD_before", "THD_after"),
            ("PF_before", "PF_after"),
            ("P_out", "Q_out"),
            ("comp_rms", "efficiency"),
        )):
            for col, key in enumerate(pair):
                grid.addWidget(self._cells[key], row, col)
                self._cells[key].clicked.connect(self.metric_selected.emit)

        layout.addLayout(grid)

        self._cards_title = QLabel("CONTROLLER COMPARISON")
        self._cards_title.setObjectName("panel_title")
        layout.addWidget(self._cards_title)

        self._controller_cards = {
            "PI": ControllerCard("PI", "#bf2026"),
            "PR": ControllerCard("PR", "#102d8f"),
            "MPC": ControllerCard("MPC", "#0f6f25"),
        }
        for ctrl_name, card in self._controller_cards.items():
            card.clicked.connect(self.controller_selected.emit)
            layout.addWidget(card)

        status_box = QFrame()
        status_box.setObjectName("status_table")
        status_layout = QVBoxLayout(status_box)
        status_layout.setContentsMargins(8, 8, 8, 8)
        status_layout.setSpacing(6)

        self._status_rows = {
            "running": StatusRow("Simulation"),
            "ieee": StatusRow("IEEE 519"),
            "controller": StatusRow("Selected Ctrl"),
            "mode": StatusRow("Phase Mode"),
            "event": StatusRow("Grid Event"),
            "harmonic": StatusRow("Dominant Harmonic"),
            "quality": StatusRow("Waveform Score"),
        }

        for row in self._status_rows.values():
            status_layout.addWidget(row)

        layout.addWidget(status_box)

        self._info_drawer = InfoDrawer()
        layout.addWidget(self._info_drawer, stretch=1)

    def set_running_state(self, running: bool):
        self._status_rows["running"].set_value("RUNNING" if running else "PAUSED", "#bfe8c3" if running else "#ece6b2")

    def set_event_state(self, active: bool):
        self._status_rows["event"].set_value("SAG ACTIVE" if active else "NORMAL", "#f5c4ae" if active else "#dfe6f9")

    def set_phase_context(self, phase_mode: str, phase_label: str):
        label = "1PH | A" if phase_mode == "single" else f"3PH | {phase_label}"
        color = "#dfe6f9" if phase_mode == "single" else "#d4e0fb"
        self._phase_context = label
        self._status_rows["mode"].set_value(label, color)

    def set_info_payload(self, title: str, summary_html: str, detail_html: str = ""):
        self._info_drawer.set_payload(title, summary_html, detail_html)

    def update_metrics(self, result):
        self._cells["THD_before"].set_value(f"{result.THD_before:.2f}")
        self._cells["THD_after"].set_value(f"{result.THD_after:.2f}")
        self._cells["PF_before"].set_value(f"{result.PF_before:.4f}")
        self._cells["PF_after"].set_value(f"{result.PF_after:.4f}")
        self._cells["P_out"].set_value(f"{result.P_out:.1f}")
        self._cells["Q_out"].set_value(f"{result.Q_out:.1f}")
        self._cells["comp_rms"].set_value(f"{result.comp_rms:.2f}")
        self._cells["efficiency"].set_value(f"{result.efficiency * 100.0:.1f}")

        self._status_rows["ieee"].set_value("PASS" if result.THD_after < 5.0 else "FAIL", "#bfe8c3" if result.THD_after < 5.0 else "#f0b8b8")
        self._status_rows["controller"].set_value(result.ctrl_name, {"PI": "#f0d2d2", "PR": "#d4e0fb", "MPC": "#c9ebcb"}.get(result.ctrl_name, "#e5e5e5"))
        self._status_rows["harmonic"].set_value(result.dominant_harmonic.upper(), "#f4ead1")
        self._status_rows["quality"].set_value(f"{result.sinusoid_score:.0f}/100", "#bfe8c3" if result.sinusoid_score >= 85.0 else "#ece6b2" if result.sinusoid_score >= 65.0 else "#f0b8b8")

        for ctrl_name, card in self._controller_cards.items():
            snapshot = result.controller_truth.get(ctrl_name)
            if snapshot:
                card.set_snapshot(snapshot, ctrl_name == result.ctrl_name)
