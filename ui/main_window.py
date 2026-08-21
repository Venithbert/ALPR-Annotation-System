from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout, QGroupBox
from PySide6.QtCore import Slot, QTimer, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPolygonF
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
        mergeButton= QPushButton("Merge csv files")

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

        #STEP 1 - get data (scan the folder)
        step1 = QVBoxLayout()
        step1.addLayout(self.row(self.path_input, browse_button))
        step1.addWidget(button)
        step1_box = self.step_box("Step 1  -  Get Data", step1, "step1")

        #STEP 2 - detect plates
        step2 = QVBoxLayout()
        step2.addLayout(self.row(self.model_input, browse_detect_button))
        step2.addWidget(detectButton)
        step2_box = self.step_box("Step 2  -  Detect Plates", step2, "step2")

        #STEP 3 - read with the three ai readers
        step3 = QVBoxLayout()
        step3.addLayout(self.row(self.first_ai_input, browse_first_ai))
        step3.addLayout(self.row(self.second_ai_input, browse_second_ai))
        step3.addLayout(self.row(self.third_ai_input, browse_third_ai))
        step3.addWidget(firstAIButton)
        step3.addWidget(secondAIButton)
        step3.addWidget(thirdAIButton)
        step3_box = self.step_box("Step 3  -  Read (3 AI readers)", step3, "step3")

        #STEP 4 - merge the csv results
        step4 = QVBoxLayout()
        step4.addLayout(self.row(self.ai1_csv_input, browse_ai1_csv))
        step4.addLayout(self.row(self.ai2_csv_input, browse_ai2_csv))
        step4.addLayout(self.row(self.ai3_csv_input, browse_ai3_csv))
        step4.addWidget(mergeButton)
        step4_box = self.step_box("Step 4  -  Merge CSV Files", step4, "step4")

        layout = QVBoxLayout() #main layout
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(step1_box)
        layout.addWidget(step2_box)
        layout.addWidget(step3_box)
        layout.addWidget(step4_box)
        layout.addWidget(self.label)
        self.setLayout(layout)

        #window + theme
        self.setWindowTitle("ALPR Annotation System")
        self.resize(720, 900)
        self.setStyleSheet(self.theme())

        #background animation (drifting diagonal stripes, painted behind the cards)
        self._bg_offset = 0.0
        self._bg_timer = QTimer(self)
        self._bg_timer.timeout.connect(self._tick_bg)
        self._bg_timer.start(40)  # ~25 fps, very light

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
        mergeButton.clicked.connect(self.on_merge)





    def row(self, line_edit, button):
        row = QHBoxLayout()
        row.addWidget(line_edit)
        row.addWidget(button)
        return row

    def step_box(self, title, inner_layout, name):
        """Wrap a step's widgets in a titled card (square, brand-styled)."""
        box = QGroupBox(title)
        box.setObjectName(name)
        inner_layout.setSpacing(10)
        inner_layout.setContentsMargins(16, 24, 16, 16)
        box.setLayout(inner_layout)
        return box

    def _tick_bg(self):
        """Advance the background stripe offset and repaint."""
        self._bg_offset = (self._bg_offset + 0.4) % 60
        self.update()

    def paintEvent(self, event):
        """Paint the drifting diagonal stripe background (behind all cards)."""
        p = QPainter(self)
        r = self.rect()
        p.fillRect(r, QColor("#ffffff"))          # base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 204, 0, 28))       # faint brand yellow
        h, w = r.height(), r.width()
        spacing, stripe = 60, 22
        x = -h + self._bg_offset
        while x < w + spacing:
            poly = QPolygonF([
                QPointF(x, 0), QPointF(x + stripe, 0),
                QPointF(x + stripe + h, h), QPointF(x + h, h),
            ])
            p.drawPolygon(poly)
            x += spacing
        p.end()

    def theme(self):
        """One stylesheet. Industrial black / white / yellow, sharp square blocks.
        The window paints a moving stripe background behind the cards."""
        return """
            QWidget {
                color: #111111;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QGroupBox {
                background: #ffffff;
                border: 2px solid #111111;
                border-radius: 0px;
                margin-top: 18px;
                padding-top: 10px;
                font-weight: 800;
                font-size: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 0px;
                margin-left: 0px;
                padding: 6px 18px;
                border-radius: 0px;
                background: #ffcc00;
                color: #111111;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            QLineEdit {
                background: #f5f5f5;
                border: 2px solid #d0d0d0;
                border-radius: 0px;
                padding: 9px 10px;
                color: #111111;
                selection-background-color: #ffcc00;
                selection-color: #111111;
            }
            QLineEdit:focus { border: 2px solid #111111; background: #ffffff; }

            QPushButton {
                background: #111111;
                color: #ffffff;
                border: 2px solid #111111;
                border-radius: 0px;
                padding: 10px 18px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #ffcc00;
                color: #111111;
                border: 2px solid #111111;
            }
            QPushButton:pressed { background: #e6b800; color: #111111; }

            QLabel {
                padding: 12px 16px;
                background: #111111;
                color: #ffcc00;
                border: none;
                border-radius: 0px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        """

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
         