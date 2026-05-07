"""
ui/settings_dialog.py
Dialog for configuring system parameters interactively.
"""

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QFormLayout, QDoubleSpinBox, QSpinBox
)

from core.parameters import P


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure System Parameters")
        self.setMinimumWidth(450)
        self.setStyleSheet("""
            QDialog { background-color: #f2f0e8; }
            QGroupBox { font-weight: bold; border: 1px solid #c9c9c0; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px 0 3px; color: #102d8f; }
            QLabel { color: #111111; }
            QPushButton { background-color: #111111; color: white; padding: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #333333; }
        """)

        main_layout = QVBoxLayout(self)

        # 1. Grid Parameters
        grid_group = QGroupBox("GRID PARAMETERS")
        grid_layout = QFormLayout(grid_group)
        
        self.f_grid_sp = QDoubleSpinBox()
        self.f_grid_sp.setRange(45.0, 55.0)
        self.f_grid_sp.setDecimals(2)
        self.f_grid_sp.setSingleStep(0.1)
        self.f_grid_sp.setValue(P.f_grid)
        grid_layout.addRow("Grid Frequency (Hz):", self.f_grid_sp)

        self.vg_rms_sp = QDoubleSpinBox()
        self.vg_rms_sp.setRange(100.0, 400.0)
        self.vg_rms_sp.setDecimals(1)
        self.vg_rms_sp.setSingleStep(10.0)
        self.vg_rms_sp.setValue(P.Vg_rms)
        grid_layout.addRow("Grid Expected RMS (V):", self.vg_rms_sp)
        
        main_layout.addWidget(grid_group)

        # 2. Load Profile (The Disturbance)
        load_group = QGroupBox("LOAD PROFILE (THE PROBLEM)")
        load_layout = QFormLayout(load_group)
        
        self.i_fund_sp = QDoubleSpinBox()
        self.i_fund_sp.setRange(2.0, 25.0)
        self.i_fund_sp.setDecimals(1)
        self.i_fund_sp.setSingleStep(1.0)
        self.i_fund_sp.setValue(P.I_load_fund)
        load_layout.addRow("Fundamental Current (A):", self.i_fund_sp)

        self.load_phase_sp = QDoubleSpinBox()
        self.load_phase_sp.setRange(-90.0, 90.0)
        self.load_phase_sp.setDecimals(1)
        self.load_phase_sp.setSingleStep(5.0)
        self.load_phase_sp.setValue(np.degrees(P.load_phase))
        load_layout.addRow("Reactive Phase Angle (°):", self.load_phase_sp)

        # Harmonics
        self.harm_spins = {}
        harm_layout = QHBoxLayout()
        for h in [3, 5, 7, 9]:
            vbox = QVBoxLayout()
            lbl = QLabel(f"H{h}(%)")
            sp = QDoubleSpinBox()
            sp.setRange(0.0, 100.0)
            sp.setDecimals(1)
            sp.setSingleStep(5.0)
            sp.setValue(P.harm.get(h, 0.0) * 100.0)
            vbox.addWidget(lbl, alignment=Qt.AlignCenter)
            vbox.addWidget(sp)
            self.harm_spins[h] = sp
            harm_layout.addLayout(vbox)
        
        load_layout.addRow("Harmonics:", harm_layout)
        main_layout.addWidget(load_group)

        # 3. Circuit Parameters
        circuit_group = QGroupBox("PHYSICAL CIRCUIT")
        circuit_layout = QFormLayout(circuit_group)

        self.vdc_sp = QDoubleSpinBox()
        self.vdc_sp.setRange(400.0, 1500.0)
        self.vdc_sp.setDecimals(1)
        self.vdc_sp.setSingleStep(50.0)
        self.vdc_sp.setValue(P.Vdc)
        circuit_layout.addRow("DC Link Voltage (V):", self.vdc_sp)

        self.l1_sp = QDoubleSpinBox()
        self.l1_sp.setRange(0.1, 20.0)
        self.l1_sp.setDecimals(2)
        self.l1_sp.setSingleStep(0.5)
        self.l1_sp.setValue(P.L1 * 1e3)
        circuit_layout.addRow("L1 Filter Inductance (mH):", self.l1_sp)

        self.l2_sp = QDoubleSpinBox()
        self.l2_sp.setRange(0.1, 20.0)
        self.l2_sp.setDecimals(2)
        self.l2_sp.setSingleStep(0.5)
        self.l2_sp.setValue(P.L2 * 1e3)
        circuit_layout.addRow("L2 Grid Inductance (mH):", self.l2_sp)

        main_layout.addWidget(circuit_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("CANCEL")
        btn_cancel.clicked.connect(self.reject)
        
        btn_apply = QPushButton("APPLY & RESTART SIM")
        btn_apply.setStyleSheet("background-color: #2036c7; color: white;")
        btn_apply.clicked.connect(self._apply_and_accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        main_layout.addLayout(btn_layout)

    def _apply_and_accept(self):
        # 1. Update Grid Params
        P.f_grid = self.f_grid_sp.value()
        P.omega = 2 * np.pi * P.f_grid
        P.Vg_rms = self.vg_rms_sp.value()
        P.Vg_peak = P.Vg_rms * np.sqrt(2.0)

        # 2. Update Load Profile
        P.I_load_fund = self.i_fund_sp.value()
        P.load_phase = np.radians(self.load_phase_sp.value())
        for h, sp in self.harm_spins.items():
            P.harm[h] = sp.value() / 100.0

        # 3. Update Circuit
        P.Vdc = self.vdc_sp.value()
        P.L1 = self.l1_sp.value() * 1e-3
        P.L2 = self.l2_sp.value() * 1e-3

        self.accept()
