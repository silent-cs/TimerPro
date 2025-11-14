import sys
import ctypes
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QSpinBox, QProgressBar, QComboBox, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QIcon, QPixmap
from PyQt5.QtMultimedia import QSound

class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setStyleSheet("background: #303030; border-radius: 10px;")
        
        self.logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png") 
        if not logo_pixmap.isNull():
            # 84 - 80 
            scaled_logo = logo_pixmap.scaled(84, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(scaled_logo)
        



        self.title = QLabel("Timer Pro")
        self.title.setStyleSheet("""
            color: #ffffff;
            font-size: 16px;
            font-family: "Segoe UI", sans-serif;
            font-weight: 600;
        """)
        
        self.min_btn = QPushButton("🗕")
        self.max_btn = QPushButton("☐")
        self.close_btn = QPushButton("✕")

        for btn in [self.min_btn, self.max_btn]:
            btn.setFixedSize(40, 28)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    font-size: 16px;
                    border: none;
                    border-radius: 5px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: rgba(255,255,255,0.1);
                }
            """)
        self.close_btn.setFixedSize(40, 28)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border-radius: 5px;
                color: #ffffff;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e81123;
                color: white;
            }
        """)

        layout = QHBoxLayout()
        layout.addWidget(self.logo_label)
        layout.addSpacing(8)
        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.min_btn)
        layout.addWidget(self.max_btn)
        layout.addWidget(self.close_btn)
        layout.setContentsMargins(15, 0, 10, 0)
        self.setLayout(layout)

        self.min_btn.clicked.connect(self.parent.showMinimized)
        self.max_btn.clicked.connect(self.toggle_maximize)
        self.close_btn.clicked.connect(self.parent.close)

        self.is_maximized = False

    def toggle_maximize(self):
        if self.is_maximized:
            self.parent.showNormal()
        else:
            self.parent.showMaximized()
        self.is_maximized = not self.is_maximized


class CountdownTimer(QWidget):
    def __init__(self):
        super().__init__()
        app_icon = QIcon("logo.png")  
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
            QApplication.instance().setWindowIcon(app_icon)
        self.time_label = QLabel("00:00:00")
        self.timer = QTimer(self)
        self.alarm_timer = QTimer(self)
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.is_running = False
        self.is_alarm_ringing = False
        self.offset = None
        self.presets = {
            "25 - minutes": 1500,
            " 5 - minutes": 300,
            "15 - minutes": 900,
            "One Hour": 3600,
            "Half an hour": 1800
        }

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        try:
            myappid = 'mycompany.timerpro.app.1'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except:
            pass
        
        hwnd = self.winId().__int__()
        accent_policy = ctypes.c_int(1)
        
        class ACCENTPOLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId", ctypes.c_int)
            ]
        
        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.POINTER(ACCENTPOLICY)),
                ("SizeOfData", ctypes.c_size_t)
            ]
            
        accent = ACCENTPOLICY()
        accent.AccentState = 3
        accent.GradientColor = 0x66FFFFFF
        data = WINCOMPATTRDATA()
        data.Attribute = 19
        data.Data = ctypes.pointer(accent)
        data.SizeOfData = ctypes.sizeof(accent)
        ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))

        self.initUI()

    def initUI(self):
        self.resize(650, 550)
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background-color: #f3f3f3;
                border: 1px solid #d0d0d0;
                border-radius: 12px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)

        self.title_bar = TitleBar(self)

        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            font-size: 80px;
            font-family: "Segoe UI", sans-serif;
            font-weight: bold;
            color: #222;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            padding: 30px;
        """)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border-radius: 10px;
                background-color: #3b3b3b;
                text-align: center;
                height: 25px;
                color: #222;
                font-weight: bold;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0078d4, stop:1 #00bcf2);
            }
        """)
        self.progress_bar.setValue(0)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("Choose a time that's ready...")
        self.preset_combo.addItems(self.presets.keys())
        self.preset_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                font-family: "Segoe UI", sans-serif;
                padding: 10px;
                background-color: #ffffff;
                color: #222;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                font-weight: 600;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        self.preset_combo.currentTextChanged.connect(self.apply_preset)

        self.hours_input = QSpinBox()
        self.minutes_input = QSpinBox()
        self.seconds_input = QSpinBox()

        for spin in [self.hours_input, self.minutes_input, self.seconds_input]:
            spin.setStyleSheet("""
                QSpinBox {
                    font-size: 16px;
                    font-weight: 600;
                    padding: 12px;
                    background-color: #ffffff;
                    color: #222;
                    border: 1px solid #d0d0d0;
                    border-radius: 8px;
                    min-width: 100px;
                }
                QSpinBox:hover {
                    border: 1px solid #0078d4;
                }
            """)

        self.hours_input.setRange(0, 23)
        self.minutes_input.setRange(0, 59)
        self.seconds_input.setRange(0, 59)

        input_layout = QHBoxLayout()
        
        hours_box = QVBoxLayout()
        hours_box.addWidget(self.hours_input)
        
        minutes_box = QVBoxLayout()
        minutes_box.addWidget(self.minutes_input)
        
        seconds_box = QVBoxLayout()
        seconds_box.addWidget(self.seconds_input)
        
        input_layout.addLayout(hours_box)
        input_layout.addLayout(minutes_box)
        input_layout.addLayout(seconds_box)

        self.start_button = QPushButton("▶ ")
        self.pause_button = QPushButton("⏸ ")
        self.reset_button = QPushButton("⟲")
        self.stop_alarm_button = QPushButton("🔕")
        self.stop_alarm_button.setVisible(False)

        self.start_button.setStyleSheet("""
            QPushButton {
                font-size: 26px;
                font-weight: bold;
                padding: 15px 5px;
                background-color: #303030;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)

        self.pause_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                background-color: #303030;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #e3e3e3;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton:disabled {
                background-color: rgba(48, 48, 48,0.3);
                color: #888;
            }
        """)

        self.reset_button.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                background-color: #303030;
                color: white;
                border: none;
                border-radius: 8px;
                min-width: 140px;
            }
            QPushButton:hover {
                background-color: #e81123;
            }
            QPushButton:pressed {
                background-color: #a80000;
            }
        """)

        self.stop_alarm_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                font-weight: bold;
                padding: 2px 1px;
                background-color: #e8e8e8;
                color: white;
                border: none;
                border-radius: 10px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #303030;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)

        self.pause_button.setEnabled(False)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.pause_button)
        btn_layout.addWidget(self.reset_button)

        stop_alarm_layout = QHBoxLayout()
        stop_alarm_layout.addStretch()
        stop_alarm_layout.addWidget(self.stop_alarm_button)
        stop_alarm_layout.addStretch()

        container_layout = QVBoxLayout(self.container)
        container_layout.addWidget(self.title_bar)
        container_layout.addSpacing(10)
        container_layout.addWidget(self.preset_combo)
        container_layout.addSpacing(20)
        container_layout.addWidget(self.time_label)
        container_layout.addWidget(self.progress_bar)
        container_layout.addSpacing(20)
        container_layout.addLayout(input_layout)
        container_layout.addSpacing(10)
        container_layout.addLayout(btn_layout)
        container_layout.addSpacing(10)
        container_layout.addLayout(stop_alarm_layout)
        container_layout.addStretch()
        container_layout.setContentsMargins(30, 0, 30, 30)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.container)
        main_layout.setContentsMargins(20, 20, 20, 20)

        self.start_button.clicked.connect(self.start_timer)
        self.pause_button.clicked.connect(self.pause_timer)
        self.reset_button.clicked.connect(self.reset_timer)
        self.stop_alarm_button.clicked.connect(self.stop_alarm)
        self.timer.timeout.connect(self.update_timer)
        self.alarm_timer.timeout.connect(self.ring_alarm)
        
    def apply_preset(self, preset_name):
        if preset_name in self.presets:
            seconds = self.presets[preset_name]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            
            self.hours_input.setValue(hours)
            self.minutes_input.setValue(minutes)
            self.seconds_input.setValue(secs)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        if self.offset is not None and event.buttons() == Qt.LeftButton:
            self.move(self.pos() + event.pos() - self.offset)
            
    def mouseReleaseEvent(self, event):
        self.offset = None
        
    def start_timer(self):
        if not self.is_running:
            hours = self.hours_input.value()
            minutes = self.minutes_input.value()
            seconds = self.seconds_input.value()
            self.remaining_seconds = hours * 3600 + minutes * 60 + seconds
            self.total_seconds = self.remaining_seconds
            if self.remaining_seconds > 0:
                self.timer.start(1000)
                self.is_running = True
                self.start_button.setEnabled(False)
                self.pause_button.setEnabled(True)
                
                self.hours_input.setEnabled(False)
                self.minutes_input.setEnabled(False)
                self.seconds_input.setEnabled(False)
                self.preset_combo.setEnabled(False)
                
    def pause_timer(self):
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.start_button.setEnabled(True)
            self.start_button.setText("▶")
            self.pause_button.setEnabled(False)
            
    def reset_timer(self):
        self.timer.stop()
        self.stop_alarm()
        self.remaining_seconds = 0
        self.total_seconds = 0
        self.is_running = False
        self.time_label.setText("00:00:00")
        self.progress_bar.setValue(0)
        self.start_button.setText("▶")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
        self.time_label.setStyleSheet("""
            font-size: 80px;
            font-family: "Segoe UI", sans-serif;
            font-weight: bold;
            color: #222;
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 15px;
            padding: 30px;
        """)
        self.hours_input.setEnabled(True)
        self.minutes_input.setEnabled(True)
        self.seconds_input.setEnabled(True)
        self.preset_combo.setEnabled(True)
        
    def stop_alarm(self):
        if self.is_alarm_ringing:
            self.alarm_timer.stop()
            self.is_alarm_ringing = False
            self.stop_alarm_button.setVisible(False)
            
    def ring_alarm(self):
        QApplication.beep()
        
    def update_timer(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            h = self.remaining_seconds // 3600
            m = (self.remaining_seconds % 3600) // 60
            s = self.remaining_seconds % 60
            self.time_label.setText(f"{h:02}:{m:02}:{s:02}")
            if self.total_seconds > 0:
                progress = int(((self.total_seconds - self.remaining_seconds) / self.total_seconds) * 100)
                self.progress_bar.setValue(progress)
            if self.remaining_seconds <= 10:
                self.time_label.setStyleSheet("""
                    font-size: 80px;
                    font-family: 'Segoe UI', sans-serif;
                    font-weight: bold;
                    color: #d13438;
                    background-color: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 15px;
                    padding: 30px;
                """)
        else:
            self.timer.stop()
            self.is_running = False
            self.time_label.setText(" - TIME'S UP! -")
            self.time_label.setStyleSheet("""
                font-size: 70px;
                font-family: "Segoe UI", sans-serif;
                font-weight: bold;
                color: #d13438;
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 15px;
                padding: 30px;
            """)
            self.progress_bar.setValue(100)
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.is_alarm_ringing = True
            self.stop_alarm_button.setVisible(True)
            self.alarm_timer.start(1000) 
            QApplication.beep() 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app_icon = QIcon("logo.png")
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    window = CountdownTimer()
    window.show()
    sys.exit(app.exec_())