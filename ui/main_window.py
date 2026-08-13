from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout
from PySide6.QtCore import Slot
from pathlib import Path

#annotation system
from core.dataset import scan_folder
from core.store import save_records


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.path_input = QLineEdit()

        #buttons
        button = QPushButton("Scan")
        self.label = QLabel("No scan yet")
        browse_button = QPushButton("Browse...")

        #layouts

        #horizontal layout for browing path ui
        row = QHBoxLayout()
        row.addWidget(self.path_input)
        row.addWidget(browse_button)

        layout = QVBoxLayout()
        layout.addLayout(row) 
        layout.addWidget(button)
        layout.addWidget(self.label)
        self.setLayout(layout)

        #connects
        button.clicked.connect(self.on_scan)
        browse_button.clicked.connect(self.on_browse)

    #user picks C:/data  >  path_input = "C:/data"
    def on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select data folder")
        if folder:
            self.path_input.setText(folder)

    #make a path > call core.dataset.scan_folder 
    def on_scan(self):
        folder = Path(self.path_input.text())
        records = scan_folder(folder)    
        save_records(records, Path("results.csv"))
        self.label.setText(f"Found {len(records)} images")