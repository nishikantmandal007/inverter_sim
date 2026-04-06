"""
widgets/spectrum.py
Explainable harmonic spectrum panel with selectable focus.
"""

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


PANEL_BG = "#f2f0e8"
AX_BG = "#fffef8"
GRID = "#c9c9c0"
BORDER = "#111111"
FOCUS = "#2036c7"
TEXT = "#111111"
COLOR_BEFORE = "#bf2026"
COLOR_AFTER = "#0f6f25"


class SpectrumWidget(QWidget):
    panel_selected = Signal(str)

    def __init__(self, title: str = "", subtitle: str = "", caption: str = "", info_key: str = "", parent=None):
        super().__init__(parent)
        self._freqs = np.array([])
        self._before = np.array([])
        self._after = np.array([])
        self._f_grid = 50.0
        self._orders = np.array([1, 3, 5, 7, 9, 11])
        self._info_key = info_key or title or "spectrum"
        self._is_selected = False
        self._subtitle_text = subtitle
        self._caption_text = caption

        self._figure = Figure(figsize=(7.0, 2.6), facecolor=PANEL_BG)
        self._canvas = FigureCanvas(self._figure)
        self._axis = self._figure.add_subplot(111)

        self._title = QLabel(title or "HARMONIC STORY")
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

        self.setMinimumSize(320, 200)
        self._configure_axes()
        self._apply_panel_state()

        for widget in (self, self._title, self._subtitle, self._caption, self._canvas):
            widget.installEventFilter(self)
            widget.setCursor(Qt.PointingHandCursor)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            self.panel_selected.emit(self._info_key)
        return super().eventFilter(obj, event)

    def set_title(self, title: str):
        self._title.setText(title)

    def set_subtitle(self, subtitle: str):
        self._subtitle_text = subtitle
        self._subtitle.setText(subtitle)
        self._apply_panel_state()

    def set_caption(self, caption: str):
        self._caption_text = caption
        self._caption.setText(caption)
        self._apply_panel_state()

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._apply_panel_state()

    def _apply_panel_state(self):
        border = FOCUS if self._is_selected else BORDER
        width = 2 if self._is_selected else 1
        self._canvas.setStyleSheet(
            f"background-color: #fffef8; border: {width}px solid {border};"
        )
        self._subtitle.setVisible(bool(self._subtitle_text))
        self._caption.setVisible(bool(self._caption_text))

    def _configure_axes(self):
        self._figure.subplots_adjust(left=0.08, right=0.985, top=0.92, bottom=0.2)
        self._axis.set_facecolor(AX_BG)
        self._axis.grid(True, axis="y", color=GRID, linewidth=0.7)
        self._axis.set_axisbelow(True)

        for spine in self._axis.spines.values():
            spine.set_color(BORDER)
            spine.set_linewidth(1.0)

        self._axis.tick_params(axis="both", colors=TEXT, labelsize=8)
        self._axis.set_xlabel("Harmonic Order", fontsize=8, color=TEXT, labelpad=4)
        self._axis.set_ylabel("Magnitude [A]", fontsize=8, color=TEXT, labelpad=4)
        self._axis.yaxis.set_major_locator(MaxNLocator(5))

    def update_spectrum(self, freqs, before, after):
        self._freqs = np.asarray(freqs)
        self._before = np.asarray(before)
        self._after = np.asarray(after)
        self._redraw()

    def _sample_harmonics(self, spectrum: np.ndarray) -> np.ndarray:
        if self._freqs.size == 0 or spectrum.size == 0:
            return np.zeros_like(self._orders, dtype=float)

        sampled = []
        for order in self._orders:
            target = order * self._f_grid
            idx = int(np.argmin(np.abs(self._freqs - target)))
            sampled.append(float(spectrum[idx]) if idx < spectrum.size else 0.0)
        return np.asarray(sampled, dtype=float)

    def _redraw(self):
        self._axis.clear()
        self._configure_axes()

        x = np.arange(self._orders.size)
        before_vals = self._sample_harmonics(self._before)
        after_vals = self._sample_harmonics(self._after)
        width = 0.36

        self._axis.bar(
            x - width / 2,
            before_vals,
            width=width,
            color=COLOR_BEFORE,
            alpha=0.85,
            edgecolor=BORDER,
            linewidth=0.8,
            label="Before",
        )
        self._axis.bar(
            x + width / 2,
            after_vals,
            width=width,
            color=COLOR_AFTER,
            alpha=0.85,
            edgecolor=BORDER,
            linewidth=0.8,
            label="After",
        )

        ymax = max(float(np.max(before_vals)), float(np.max(after_vals)), 1.0)
        self._axis.set_ylim(0.0, ymax * 1.2)
        self._axis.set_xticks(x, [f"{order}h" for order in self._orders])

        legend = self._axis.legend(
            loc="upper right",
            fontsize=7,
            frameon=True,
            facecolor="#ffffff",
            edgecolor="#111111",
            fancybox=False,
            framealpha=1.0,
        )
        legend.get_frame().set_linewidth(0.8)

        self._canvas.draw_idle()
