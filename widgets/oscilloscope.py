"""
widgets/oscilloscope.py
Explainable Matplotlib waveform panel with selectable focus and captions.
"""

from dataclasses import dataclass, field

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


COLORS = {
    "Vg": "#102d8f",
    "I_load": "#bf2026",
    "I_grid": "#0f6f25",
    "I_ref": "#444444",
    "I_comp": "#c97d00",
    "I_harm": "#7a42b8",
    "I_react": "#1a7da8",
}

PANEL_BG = "#f2f0e8"
AX_BG = "#fffef8"
GRID = "#c9c9c0"
BORDER = "#111111"
FOCUS = "#2036c7"
TEXT = "#111111"


@dataclass
class Channel:
    key: str
    label: str
    unit: str
    scale: float
    visible: bool = True
    color: str | None = None
    data: np.ndarray = field(default_factory=lambda: np.array([]))
    line: object = None

    def __post_init__(self):
        if self.color is None:
            self.color = COLORS.get(self.key, "#111111")


class OscilloscopeWidget(QWidget):
    panel_selected = Signal(str)

    def __init__(
        self,
        title: str = "",
        subtitle: str = "",
        caption: str = "",
        info_key: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.title = title
        self._subtitle_text = subtitle
        self._caption_text = caption
        self._info_key = info_key or title
        self._is_selected = False
        self.channels: list[Channel] = []

        self._figure = Figure(figsize=(7.0, 2.8), facecolor=PANEL_BG)
        self._canvas = FigureCanvas(self._figure)
        self._axis = self._figure.add_subplot(111)

        self._title = QLabel(title)
        self._title.setObjectName("panel_title")

        self._subtitle = QLabel(subtitle)
        self._subtitle.setObjectName("panel_subtitle")
        self._subtitle.setWordWrap(True)

        self._caption = QLabel(caption)
        self._caption.setObjectName("panel_caption")
        self._caption.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._canvas, stretch=1)
        layout.addWidget(self._caption)

        self.setMinimumSize(420, 240)
        self._configure_axes()
        self._apply_panel_state()

        for widget in (self, self._title, self._subtitle, self._caption, self._canvas):
            widget.installEventFilter(self)
            widget.setCursor(Qt.PointingHandCursor)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.panel_selected.emit(self._info_key)
        return super().eventFilter(obj, event)

    def _configure_axes(self):
        self._figure.subplots_adjust(left=0.08, right=0.985, top=0.94, bottom=0.19)
        self._axis.set_facecolor(AX_BG)
        self._axis.grid(True, color=GRID, linewidth=0.7)
        self._axis.set_axisbelow(True)

        for spine in self._axis.spines.values():
            spine.set_color(BORDER)
            spine.set_linewidth(1.0)

        self._axis.tick_params(axis="both", colors=TEXT, labelsize=8)
        self._axis.set_xlabel("Cycle Window [ms]", fontsize=8, color=TEXT, labelpad=4)
        self._axis.set_ylabel("Amplitude", fontsize=8, color=TEXT, labelpad=4)
        self._axis.xaxis.set_major_locator(MaxNLocator(6))
        self._axis.yaxis.set_major_locator(MaxNLocator(5))

    def _apply_panel_state(self):
        border = FOCUS if self._is_selected else BORDER
        width = 2 if self._is_selected else 1
        self._canvas.setStyleSheet(
            f"background-color: #fffef8; border: {width}px solid {border};"
        )
        self._subtitle.setVisible(bool(self._subtitle_text))
        self._caption.setVisible(bool(self._caption_text))

    def set_title(self, title: str):
        self.title = title
        self._title.setText(title)

    def set_subtitle(self, subtitle: str):
        self._subtitle_text = subtitle
        self._subtitle.setText(subtitle)
        self._apply_panel_state()

    def set_caption(self, caption: str):
        self._caption_text = caption
        self._caption.setText(caption)
        self._apply_panel_state()

    def set_info_key(self, info_key: str):
        self._info_key = info_key

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_panel_state()

    def add_channel(self, ch: Channel):
        (line,) = self._axis.plot(
            [],
            [],
            color=ch.color,
            linewidth=1.45,
            label=ch.label,
            linestyle="--" if ch.key == "I_ref" else "-",
        )
        ch.line = line
        self.channels.append(ch)
        self._update_legend()

    def update_data(self, key: str, data: np.ndarray):
        for ch in self.channels:
            if ch.key == key:
                ch.data = data
        self._redraw()

    def update_all(self, data_dict: dict):
        for ch in self.channels:
            if ch.key in data_dict:
                ch.data = np.asarray(data_dict[ch.key])
        self._redraw()

    def _update_legend(self):
        visible_lines = [
            ch.line for ch in self.channels
            if ch.line is not None and ch.visible
        ]
        if not visible_lines:
            legend = self._axis.get_legend()
            if legend is not None:
                legend.remove()
            return

        legend = self._axis.legend(
            handles=visible_lines,
            labels=[line.get_label() for line in visible_lines],
            loc="upper right",
            fontsize=7,
            frameon=True,
            facecolor="#ffffff",
            edgecolor="#111111",
            fancybox=False,
            framealpha=1.0,
            ncol=min(2, len(visible_lines)),
        )
        legend.get_frame().set_linewidth(0.8)

    def _redraw(self):
        valid_channels = [
            ch for ch in self.channels
            if ch.visible and ch.data.size >= 2 and ch.line is not None
        ]

        if not valid_channels:
            self._axis.set_xlim(0.0, 20.0)
            self._axis.set_ylim(-1.0, 1.0)
            for ch in self.channels:
                if ch.line is not None:
                    ch.line.set_data([], [])
                    ch.line.set_visible(False)
            self._update_legend()
            self._canvas.draw_idle()
            return

        n_samples = max(ch.data.size for ch in valid_channels)
        x_ms = np.linspace(0.0, 20.0, n_samples)
        y_limits = []

        for ch in self.channels:
            if ch.line is None:
                continue
            if ch.visible and ch.data.size >= 2:
                y = np.asarray(ch.data) * ch.scale
                x = np.linspace(0.0, 20.0, y.size)
                ch.line.set_data(x, y)
                ch.line.set_visible(True)
                y_limits.append(y)
            else:
                ch.line.set_data([], [])
                ch.line.set_visible(False)

        peak = max(float(np.max(np.abs(y))) for y in y_limits) if y_limits else 1.0
        peak = max(peak, 1e-3)

        self._axis.set_xlim(float(x_ms[0]), float(x_ms[-1]))
        self._axis.set_ylim(-1.15 * peak, 1.15 * peak)
        self._update_legend()
        self._canvas.draw_idle()
