from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout
from PySide6.QtCore import Slot
from pathlib import Path

#annotation system
from core.dataset import scan_folder
from core.store import save_records, save_results
from core.detect import load_model,detect_plate

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        #buttons
        button = QPushButton("Scan")
        self.label = QLabel("No scan yet")
        detectButton = QPushButton("Detect Plate")

        #browse path buttons
        self.path_input = QLineEdit()
        browse_button = QPushButton("Browse...")

        self.model_input = QLineEdit()
        browse_detect_button = QPushButton("Browse...model")



        #layouts

        #horizontal layout for browing path ui
        row = QHBoxLayout()
        row.addWidget(self.path_input)
        row.addWidget(browse_button)

        row2 = QHBoxLayout()
        row2.addWidget(self.model_input)
        row2.addWidget(browse_detect_button)

        layout = QVBoxLayout()
        layout.addLayout(row) 
        layout.addLayout(row2) 
        layout.addWidget(button)
        layout.addWidget(detectButton)

        layout.addWidget(self.label)

        self.setLayout(layout)


        #connects
        button.clicked.connect(self.on_scan)
        browse_button.clicked.connect(self.on_browse)
        browse_detect_button.clicked.connect(self.on_browse_detect)
        detectButton.clicked.connect(self.on_detect)


    #user picks C:/data  >  path_input = "C:/data"
    def on_browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Select data folder")
        if folder:
            self.path_input.setText(folder)

    #make a path > call core.dataset.scan_folder. it puts stuff in a dict > call core.store.save_records write dict to an csv
    def on_scan(self):
        folder = Path(self.path_input.text())
        self.records = scan_folder(folder)    
        save_records(self.records, Path("results.csv"))
        self.label.setText(f"Found {len(self.records)} images")


    def on_browse_detect(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select model", "", "Model files (*.pt)")
        if path:
            self.model_input.setText(path)

    def on_detect(self): #get model and data folder path, load model, detect plates
        model_path = Path(self.model_input.text())
        folder = Path(self.path_input.text())
        crops_folder = Path("crops")
        
        yolo = load_model(model_path)
        detect_plate(yolo, folder, crops_folder)
        detections = detect_plate(yolo, folder, crops_folder)
        save_results(self.records, detections, Path("results.csv"))

