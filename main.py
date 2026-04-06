"""
Smart Grid Solar Inverter — Real-Time Simulation
Department of Electrical Engineering, B.I.T. Sindri

Entry point. Run this file.
    python main.py
"""

import os
import sys
import tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


# Matplotlib needs a writable config/cache directory in sandboxed environments.
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "inverter-sim-mpl"))

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Smart Grid Inverter Simulation")
    app.setOrganizationName("BIT Sindri")

    # High DPI
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
