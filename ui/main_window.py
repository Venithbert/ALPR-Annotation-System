from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout, QGroupBox, QLayout
from PySide6.QtCore import Slot, QTimer, QPointF, Qt
from PySide6.QtGui import QPainter, QColor, QPolygonF
from pathlib import Path

#annotation system
from core.dataset import scan_folder
from core.store import save_records, save_results
from core.detect import load_model,detect_plate
from core.fake_readers import fake_reader   ###place holder
from core.analyze import mergeCSV
from core.reorder import reorderData

#the window size the ui needs at scale 1.0. these are only rough fallbacks - the real
#numbers are measured from the widgets themselves on the first show (see _calibrate),
#so they stay correct even after adding or removing widgets.
REFERENCE_WIDTH  = 700
REFERENCE_HEIGHT = 1360

MIN_SCALE = 0.35   #how far the ui is allowed to shrink
MAX_SCALE = 2.00   #how far it is allowed to grow
FIT_MARGIN = 0.98  #shrink a hair past the exact fit, to absorb rounding

class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        #reference-resolution scaler. the scale is driven by the WINDOW size, not the
        #screen, so dragging the window smaller shrinks the whole ui (see resizeEvent).
        #the screen only decides the size the window opens at.
        screen = QApplication.primaryScreen()
        avail = screen.availableGeometry() if screen is not None else None
        if avail is not None:
            start_w = int(avail.width() * 0.5)
            start_h = int(avail.height() * 0.85)
        else:
            start_w, start_h = REFERENCE_WIDTH, REFERENCE_HEIGHT

        self._ref_w = None           #measured on first show by _calibrate()
        self._ref_h = None
        self._applied_scale = 0.0    #last scale pushed into the stylesheet
        self._rescaling = False      #re-entrancy guard for resizeEvent
        self._scaled_layouts = []    #(layout, spacing units, margin units) to re-scale
        self.scale = self._scale_for(start_w, start_h)

        #buttons
        self.label = QLabel("No scan yet")
        button = QPushButton("Scan")
        detectButton = QPushButton("Detect Plate")
        firstAIButton = QPushButton("First ai")
        secondAIButton = QPushButton("Second ai")
        thirdAIButton = QPushButton("Third ai")
        mergeButton= QPushButton("Merge csv files")
        reorderDataButton = QPushButton("Reorder Data")

        #path browse buttons
        self.data_folder_input = QLineEdit()
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

        #reorder
        self.merged_csv = QLineEdit()
        self.data_folder = QLineEdit()

        browse_merged_csv = QPushButton("Browse... merged csv")
        browse_data_folder = QPushButton("Browse... data folder")

        #layouts

        #horizontal layout for browing path uiand adding buttons to main layout

        #STEP 1 - get data (scan the folder)
        step1 = QVBoxLayout()
        step1.addLayout(self.row(self.data_folder_input, browse_button))
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

        #STEP 5 - merge the csv results
        step5 = QVBoxLayout()
        step5.addLayout(self.row(self.merged_csv, browse_merged_csv))
        step5.addLayout(self.row(self.data_folder, browse_data_folder))
        step5.addWidget(reorderDataButton)
        step5_box = self.step_box("Step 5  -  Reorder Data Folder", step5, "step5")


        layout = QVBoxLayout() #main layout
        #SetNoConstraint = the layout stops forcing a minimum size on the window,
        #so the user can actually drag it smaller. the rescale then makes it fit.
        layout.setSizeConstraint(QLayout.SetNoConstraint)
        self._register(layout, 16, 24)
        layout.addWidget(step1_box)
        layout.addWidget(step2_box)
        layout.addWidget(step3_box)
        layout.addWidget(step4_box)
        layout.addWidget(step5_box)
        layout.addWidget(self.label)
        self.setLayout(layout)

        #window + theme
        self.setWindowTitle("ALPR Annotation System")
        self.setMinimumSize(320, 260)   #hard floor, otherwise qt uses the content size
        self._apply_scale(self.scale)
        self.resize(start_w, start_h)
        if avail is not None:
            self.move(   #centre it inside the usable desktop area
                avail.x() + (avail.width() - self.width()) // 2,
                avail.y() + (avail.height() - self.height()) // 2,
            )

        #background animation (drifting diagonal stripes, painted behind the cards)
        self._bg_offset = 0.0
        self._bg_timer = QTimer(self)
        self._bg_timer.timeout.connect(self._tick_bg)
        self._bg_timer.start(40)  # ~25 fps, very light

        #connects

        button.clicked.connect(self.on_scan)
        browse_button.clicked.connect(lambda: self.on_browse_folder(self.data_folder_input))

        browse_merged_csv.clicked.connect(lambda: self.on_browse_csv(self.merged_csv))
        browse_data_folder.clicked.connect(lambda: self.on_browse_folder(self.data_folder))
        reorderDataButton.clicked.connect(self.on_reorder)

        browse_detect_button.clicked.connect(self.on_browse_detector)
        detectButton.clicked.connect(self.on_detect)

        ### on_ai place holder
        firstAIButton.clicked.connect(self.on_ai)
        secondAIButton.clicked.connect(self.on_ai)
        thirdAIButton.clicked.connect(self.on_ai)

        browse_ai1_csv.clicked.connect(lambda: self.on_browse_csv(self.ai1_csv_input))
        browse_ai2_csv.clicked.connect(lambda: self.on_browse_csv(self.ai2_csv_input))
        browse_ai3_csv.clicked.connect(lambda: self.on_browse_csv(self.ai3_csv_input))
        mergeButton.clicked.connect(self.on_merge)

    def s(self, value):
        """Design units -> pixels at the current scale."""
        return int(round(value * self.scale))

    def _scale_for(self, w, h):
        """How much to shrink/grow the ui so it fits a window of w x h."""
        ref_w = self._ref_w or REFERENCE_WIDTH
        ref_h = self._ref_h or REFERENCE_HEIGHT
        fit = min(w / ref_w, h / ref_h) * FIT_MARGIN
        return max(MIN_SCALE, min(MAX_SCALE, fit))

    def _needs(self, scale):
        """Room the ui needs at a given scale, measured for real.

        Width uses the layout minimum (the line edits can compress), height uses
        the natural hint (the controls are fixed height, they just stack).
        """
        self._apply_scale(scale)
        layout = self.layout()
        layout.activate()
        return max(1, layout.minimumSize().width()), max(1, layout.sizeHint().height())

    def _calibrate(self):
        """Measure the ui at both ends of its scale range.

        Done on the first show, when the stylesheet is applied and the size hints
        are real. Measuring beats hardcoded numbers, which go stale the moment a
        widget is added.
        """
        self._rescaling = True   #ignore the resizes this provokes
        try:
            #what it needs at full size -> the reference the scale is measured against
            self._ref_w, self._ref_h = self._needs(1.0)
            #what it needs at its smallest -> the window's minimum, so it can never
            #be dragged into a size where the last cards are cut off
            self.setMinimumSize(*self._needs(MIN_SCALE))
        finally:
            self._rescaling = False
        self._fit_to(self.width(), self.height())

    def _fit_to(self, w, h):
        """Scale the ui down until it really fits h.

        _scale_for gets close, but font sizes round to whole pixels so the fit is
        never exact. Measure the result and correct; this settles in a pass or two.
        """
        scale = self._scale_for(w, h)
        layout = self.layout()
        for _ in range(8):
            previous = scale
            self._apply_scale(scale)
            layout.activate()
            need = layout.sizeHint().height()
            if need <= h or scale <= MIN_SCALE:
                break
            scale = max(MIN_SCALE, scale * (h / need) * FIT_MARGIN)
            if abs(scale - previous) < 0.005:
                break

    def showEvent(self, event):
        super().showEvent(event)
        if self._ref_w is None:
            self._calibrate()

    def _register(self, layout, spacing, margin):
        """Remember a layout's spacing/margin in design units so it can be re-scaled."""
        self._scaled_layouts.append((layout, spacing, margin))
        layout.setSpacing(self.s(spacing))
        layout.setContentsMargins(*(self.s(m) for m in self._margins(margin)))
        return layout

    def _margins(self, margin):
        """A margin spec is one number, or (left, top, right, bottom)."""
        return margin if isinstance(margin, tuple) else (margin, margin, margin, margin)

    def _apply_scale(self, scale):
        """Push a new scale into the stylesheet and every registered layout."""
        if abs(scale - self._applied_scale) < 0.005:
            return
        self.scale = scale
        self._applied_scale = scale
        self.setStyleSheet(self.theme(scale))
        for layout, spacing, margin in self._scaled_layouts:
            layout.setSpacing(self.s(spacing))
            layout.setContentsMargins(*(self.s(m) for m in self._margins(margin)))
        self.update()   #stripes are scaled too

    def resizeEvent(self, event):
        """Drive the scale off the window size: drag it smaller, everything shrinks."""
        super().resizeEvent(event)
        if self._rescaling:
            return
        self._rescaling = True
        try:
            self._fit_to(self.width(), self.height())
        finally:
            self._rescaling = False

    def row(self, line_edit, button):
        row = QHBoxLayout()
        row.addWidget(line_edit)
        row.addWidget(button)
        self._register(row, 10, 0)
        return row

    def step_box(self, title, inner_layout, name):
        """Wrap a step's widgets in a titled card (square, brand-styled)."""
        box = QGroupBox(title)
        box.setObjectName(name)
        self._register(inner_layout, 10, (16, 24, 16, 16))
        box.setLayout(inner_layout)
        return box

    def _tick_bg(self):
        """Advance the background stripe offset and repaint."""
        self._bg_offset = (self._bg_offset + 0.4 * self.scale) % self.s(60)
        self.update()

    def paintEvent(self, event):
        """Paint the drifting diagonal stripe background (behind all cards)."""
        p = QPainter(self)
        r = self.rect()
        p.fillRect(r, QColor("#ffffff"))          # base
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 204, 0, 28))       # faint brand yellow
        h, w = r.height(), r.width()
        spacing, stripe = self.s(60), self.s(22)
        x = -h + self._bg_offset
        while x < w + spacing:
            poly = QPolygonF([
                QPointF(x, 0), QPointF(x + stripe, 0),
                QPointF(x + stripe + h, h), QPointF(x + h, h),
            ])
            p.drawPolygon(poly)
            x += spacing
        p.end()

    def theme(self, scale):
        """One stylesheet. Industrial black / white / yellow, sharp square blocks.
        Sizes are written in 1080p design units and multiplied by 'scale', so the
        ui keeps the same proportions on any screen.
        The window paints a moving stripe background behind the cards."""
        px = lambda v: int(round(v * scale))
        return f"""
            QWidget {{
                color: #111111;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: {px(22)}px;
            }}
            QGroupBox {{
                background: #ffffff;
                border: {px(2)}px solid #111111;
                border-radius: 0px;
                margin-top: {px(18)}px;
                padding-top: {px(10)}px;
                font-weight: 800;
                font-size: {px(15)}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 0px;
                margin-left: 0px;
                padding: {px(6)}px {px(18)}px;
                border-radius: 0px;
                background: #ffcc00;
                color: #111111;
                text-transform: uppercase;
                letter-spacing: {px(1)}px;
            }}

            QLineEdit {{
                background: #f5f5f5;
                border: {px(2)}px solid #d0d0d0;
                border-radius: 0px;
                min-height: {px(34)}px;
                padding: {px(9)}px {px(10)}px;
                color: #111111;
                selection-background-color: #ffcc00;
                selection-color: #111111;
            }}
            QLineEdit:focus {{ border: {px(2)}px solid #111111; background: #ffffff; }}

            QPushButton {{
                background: #111111;
                color: #ffffff;
                border: {px(2)}px solid #111111;
                border-radius: 0px;
                min-height: {px(38)}px;
                padding: {px(10)}px {px(18)}px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: {px(1)}px;
            }}
            QPushButton:hover {{
                background: #ffcc00;
                color: #111111;
                border: {px(2)}px solid #111111;
            }}
            QPushButton:pressed {{ background: #e6b800; color: #111111; }}

            QLabel {{
                padding: {px(12)}px {px(16)}px;
                background: #111111;
                color: #ffcc00;
                border: none;
                border-radius: 0px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: {px(1)}px;
            }}
        """

    #user picks C:/data  >  data_folder_input = "C:/data"
    def on_browse_folder(self, target):
        folder = QFileDialog.getExistingDirectory(self, "Select data folder")
        if folder:
            target.setText(folder)

    #make a path > call core.dataset.scan_folder. it puts stuff in a dict > call core.store.save_records write dict to an csv
    def on_scan(self):
        folder = Path(self.data_folder_input.text())
        self.records = scan_folder(folder)
        save_records(self.records, Path("results.csv"))
        self.label.setText(f"Found {len(self.records)} images")

    def on_browse_detector(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select model", "", "Model files (*.pt)")
        if path:
            self.model_input.setText(path)

    def on_detect(self): #get model and data folder path, load model, detect plates
        model_path = Path(self.model_input.text())
        folder = Path(self.data_folder_input.text())
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

    def on_reorder(self):
        folder = Path(self.data_folder.text())
        reordered_folder = Path("Reordered")

        reorderData(folder, Path(self.merged_csv.text()), reordered_folder)
