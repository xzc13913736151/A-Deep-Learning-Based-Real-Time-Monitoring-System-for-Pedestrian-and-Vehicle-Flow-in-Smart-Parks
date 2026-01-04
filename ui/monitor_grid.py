# ui/monitor_grid.py
import cv2
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QFrame, QFileDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from core.detector import SmartDetector

class MonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_logic()

    def init_ui(self):
        # 局部样式优化
        self.setStyleSheet("""
            /* 视频区边框 */
            QLabel#video_screen {
                background-color: #000;
                border: 2px solid #333;
                border-radius: 12px;
            }
            
            /* 数据卡片容器 */
            QFrame#stats_panel {
                background-color: #1e1e24; /* 卡片深色背景 */
                border-radius: 15px;
                border: 1px solid #333;
            }
            
            /* 数据项样式 */
            QLabel.stat_title {
                color: #aaa; font-size: 13px; font-weight: bold;
            }
            QLabel.stat_value {
                color: #fff; font-size: 28px; font-weight: bold; font-family: 'Arial';
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: #2d3436;
                color: white; border: 1px solid #444;
                border-radius: 8px; padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00b894; border: 1px solid #00b894;
                color: #fff;
            }
            QPushButton#btn_active {
                background-color: #ff7675; border: 1px solid #ff7675;
            }
        """)

        # 主布局
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        self.setLayout(main_layout)

        # --- 左侧：视频显示区 (占比 75%) ---
        video_layout = QVBoxLayout()
        self.video_label = QLabel("Waiting for Signal...")
        self.video_label.setObjectName("video_screen") # 设置ID以应用样式
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #555; font-size: 20px;")
        self.video_label.setSizePolicy(1, 1) # 尽可能填充
        video_layout.addWidget(self.video_label)
        main_layout.addLayout(video_layout, stretch=3)

        # --- 右侧：HUD 数据看板 (占比 25%) ---
        self.right_panel = QVBoxLayout()
        self.right_panel.setSpacing(20)

        # 1. 标题
        title = QLabel("👁️ MONITORING")
        title.setStyleSheet("color: #00b894; font-size: 20px; font-weight: 900; letter-spacing: 2px;")
        self.right_panel.addWidget(title)

        # 2. 数据统计卡片 (Data Card)
        stats_frame = QFrame()
        stats_frame.setObjectName("stats_panel")
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(20, 30, 20, 30)
        stats_layout.setSpacing(20)

        # 数据行 A
        row1 = self.create_stat_row("⬇️ ENTRY (进)", "0", "#00cec9")
        self.lbl_in = row1[1]
        
        # 数据行 B
        row2 = self.create_stat_row("⬆️ EXIT (出)", "0", "#fd79a8")
        self.lbl_out = row2[1]
        
        # 数据行 C (拥挤度)
        row3 = self.create_stat_row("👥 DENSITY", "0", "#ffeaa7")
        self.lbl_curr = row3[1]

        stats_layout.addLayout(row1[0])
        stats_layout.addLayout(row2[0])
        stats_layout.addLayout(row3[0])
        stats_frame.setLayout(stats_layout)
        
        self.right_panel.addWidget(stats_frame)

        # 3. 占位弹簧
        self.right_panel.addStretch()

        # 4. 控制区
        self.btn_open = QPushButton("📂 导入视频源")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        
        self.btn_start = QPushButton("▶ 启动分析引擎")
        self.btn_start.setCursor(Qt.PointingHandCursor)

        self.right_panel.addWidget(self.btn_open)
        self.right_panel.addWidget(self.btn_start)

        main_layout.addLayout(self.right_panel, stretch=1)

        # 信号绑定
        self.btn_open.clicked.connect(self.open_file)
        self.btn_start.clicked.connect(self.toggle_video)

    def create_stat_row(self, title_text, value_text, color):
        """辅助函数：创建漂亮的数据行"""
        layout = QVBoxLayout()
        title = QLabel(title_text)
        title.setProperty("class", "stat_title") # 用于QSS选择
        title.setStyleSheet("color: #888; font-size: 12px; font-weight: bold;")
        
        val = QLabel(value_text)
        val.setProperty("class", "stat_value")
        val.setStyleSheet(f"color: {color}; font-size: 32px; font-family: 'Impact';")
        
        layout.addWidget(title)
        layout.addWidget(val)
        return layout, val

    # --- 逻辑部分保持不变 ---
    def init_logic(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.is_running = False
        try:
            self.detector = SmartDetector(model_path='runs/train/visdrone_test/weights/best.pt')
        except:
            print("模型加载失败，仅用于UI演示")

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "./data", "Videos (*.mp4 *.avi)")
        if path:
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(path)
            self.video_label.setText("✅ SIGNAL READY")

    def toggle_video(self):
        if not self.cap: return
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.btn_start.setText("▶ RESUME")
            self.btn_start.setObjectName("") # 恢复默认样式
            self.btn_start.setStyle(self.btn_start.style()) # 刷新样式
        else:
            self.timer.start(30)
            self.is_running = True
            self.btn_start.setText("⏸ PAUSE")
            self.btn_start.setObjectName("btn_active") # 变成红色
            self.btn_start.setStyle(self.btn_start.style())

    def update_frame(self):
        if not self.cap or not self.cap.isOpened(): return
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        processed_frame, stats = self.detector.process_frame(frame)
        
        # 更新数据
        self.lbl_in.setText(str(stats['in_count']))
        self.lbl_out.setText(str(stats['out_count']))
        self.lbl_curr.setText(str(stats['current_people']))
        
        self.display_image(processed_frame)

    def display_image(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        qt_img = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        if self.cap: self.cap.release()