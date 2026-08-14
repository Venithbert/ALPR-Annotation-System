from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout
from PySide6.QtCore import Slot
from pathlib import Path

#annotation system
from core.dataset import scan_folder
from core.store import save_records, save_results
from core.detect import load_model,detect_plate
from core.fake_readers import fake_reader   ###place holder
from core.analyze import mergeCSV

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        #buttons
        self.label = QLabel("No scan yet")
        button = QPushButton("Scan")
        detectButton = QPushButton("Detect Plate")
        firstAIButton = QPushButton("First ai")
        secondAIButton = QPushButton("Second ai")
        thirdAIButton = QPushButton("Third ai")
        mergeCSV= QPushButton("Merge csv files")

        #path browse buttons
        self.path_input = QLineEdit()
        browse_button = QPushButton("Browse...data")

        self.model_input = QLineEdit()
        browse_detect_button = QPushButton("Browse...detection model")

        #ai
        self.first_ai_input = QLineEdit()
        self.second_ai_input = QLineEdit()
        self.third_ai_input = QLineEdit()

        browse_first_ai = QPushButton("Browse...first ai")
        browse_second_ai = QPushButton("Browse...second ai")
        browse_third_ai = QPushButton("Browse...third ai")

        #csv  
        self.ai1_csv_input = QLineEdit()
        self.ai2_csv_input = QLineEdit()
        self.ai3_csv_input = QLineEdit()

        browse_ai1_csv = QPushButton("Browse...ai1 csv")
        browse_ai2_csv = QPushButton("Browse...ai2 csv")
        browse_ai3_csv = QPushButton("Browse...ai3 csv")


        #layouts

        #horizontal layout for browing path uiand adding buttons to main layout

        layout = QVBoxLayout() #main layout
        layout.addLayout(self.row(self.path_input, browse_button)) 
        layout.addLayout(self.row(self.model_input, browse_detect_button)) 
        layout.addLayout(self.row(self.first_ai_input, browse_first_ai)) 
        layout.addLayout(self.row(self.second_ai_input, browse_second_ai)) 
        layout.addLayout(self.row(self.third_ai_input, browse_third_ai)) 
        layout.addLayout(self.row(self.ai1_csv_input, browse_ai1_csv)) 
        layout.addLayout(self.row(self.ai2_csv_input, browse_ai2_csv)) 
        layout.addLayout(self.row(self.ai3_csv_input, browse_ai3_csv)) 

        layout.addWidget(button)
        layout.addWidget(detectButton)
        layout.addWidget(firstAIButton)
        layout.addWidget(secondAIButton)
        layout.addWidget(thirdAIButton)
        layout.addWidget(mergeCSV)
        layout.addWidget(self.label)
        self.setLayout(layout)

        #connects
        button.clicked.connect(self.on_scan)
        browse_button.clicked.connect(self.on_browse)
        browse_detect_button.clicked.connect(self.on_browse_detect)
        detectButton.clicked.connect(self.on_detect)

        ### on_ai place holder
        firstAIButton.clicked.connect(self.on_ai)
        secondAIButton.clicked.connect(self.on_ai)
        thirdAIButton.clicked.connect(self.on_ai)

        browse_ai1_csv.clicked.connect(lambda: self.on_browse_csv(self.ai1_csv_input))
        browse_ai2_csv.clicked.connect(lambda: self.on_browse_csv(self.ai2_csv_input))
        browse_ai3_csv.clicked.connect(lambda: self.on_browse_csv(self.ai3_csv_input))
        mergeCSV.clicked.connect(self.on_merge)





    def row(self, line_edit, button):
        row = QHBoxLayout()
        row.addWidget(line_edit)
        row.addWidget(button)
        return row

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

    ### place holder for fake data
    def on_ai(self):
        fake_reader(self.records, "paddle", Path("results_paddle.csv"))
        fake_reader(self.records, "parseq", Path("results_parseq.csv"))
        fake_reader(self.records, "vlm", Path("results_vlm.csv"))

    def on_browse_csv(self, target):
        """ Open the file picker window.(QFileDialog.getOpenFileName) Put the picked path in the box.

            'target' = which box. The lambda in connect() decides which one.
        """
        path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV files (*.csv)")
        if path:
            target.setText(path)

    def on_merge(self):
        mergeCSV( Path("results.csv") ,self.ai1_csv_input.text(), self.ai2_csv_input.text(), self.ai3_csv_input.text())
         