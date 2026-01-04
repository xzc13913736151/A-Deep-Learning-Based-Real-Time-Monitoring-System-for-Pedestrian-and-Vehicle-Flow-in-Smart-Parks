import cv2
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFrame, QFileDialog, QSizePolicy, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QImage, QPixmap, QCursor
from core.detector import SmartDetector


class MonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_logic()

    def init_ui(self):
        self.setStyleSheet("""
            QLabel#video_screen {
                background-color: #000;
                border: 2px solid #333;
                border-radius: 12px;
            }
            QFrame#stats_panel, QFrame#legend_panel {
                background-color: #1e1e24; 
                border-radius: 15px;
                border: 1px solid #333;
            }
            QLabel.stat_title {
                color: #aaa; font-size: 13px; font-weight: bold;
            }
            QLabel.stat_value {
                color: #fff; font-size: 28px; font-weight: bold; font-family: 'Arial';
            }
            /* 图例文字 */
            QLabel.legend_text {
                color: #ddd; font-size: 14px; font-weight: 500;
            }
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

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        self.setLayout(main_layout)

        # --- 视频区 ---
        video_layout = QVBoxLayout()
        self.video_label = QLabel("Waiting for Signal...")
        self.video_label.setObjectName("video_screen")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("color: #555; font-size: 20px;")
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.video_label.setMouseTracking(True)

        video_layout.addWidget(self.video_label)
        main_layout.addLayout(video_layout, stretch=3)

        # --- 右侧控制面板 ---
        self.right_panel = QVBoxLayout()
        self.right_panel.setSpacing(15)  # 稍微紧凑一点

        title = QLabel("👁️ TRAFFIC BRAIN")
        title.setStyleSheet("color: #00b894; font-size: 22px; font-weight: 900; letter-spacing: 1px;")
        self.right_panel.addWidget(title)

        # 1. 数据统计卡片
        stats_frame = QFrame()
        stats_frame.setObjectName("stats_panel")
        stats_layout = QVBoxLayout()
        stats_layout.setContentsMargins(20, 20, 20, 20)
        stats_layout.setSpacing(15)

        row1 = self.create_stat_row("⬇️ IN-FLOW (入流量)", "0", "#00cec9")
        self.lbl_in = row1[1]
        row2 = self.create_stat_row("⬆️ OUT-FLOW (出流量)", "0", "#fd79a8")
        self.lbl_out = row2[1]
        row3 = self.create_stat_row("🚗 ON-SCREEN (当前车辆)", "0", "#ffeaa7")
        self.lbl_curr = row3[1]

        stats_layout.addLayout(row1[0])
        stats_layout.addLayout(row2[0])
        stats_layout.addLayout(row3[0])
        stats_frame.setLayout(stats_layout)
        self.right_panel.addWidget(stats_frame)

        # 2. [新增] 图例说明面板 (Legend)
        legend_label = QLabel("🎨 全类别图例 (LEGEND)")
        legend_label.setStyleSheet("color: #aaa; font-weight: bold; margin-top: 10px;")
        self.right_panel.addWidget(legend_label)

        legend_frame = QFrame()
        legend_frame.setObjectName("legend_panel")
        legend_layout = QGridLayout()
        legend_layout.setContentsMargins(10, 10, 10, 10)
        legend_layout.setSpacing(8)

        # 左侧列 (col=0)
        self.add_legend_item(legend_layout, 0, 0, "#00FFFF", "AwningTri (棚车)")
        self.add_legend_item(legend_layout, 1, 0, "#FF9F43", "Bicycle (自行车)")
        self.add_legend_item(legend_layout, 2, 0, "#9B59B6", "Bus (公交车)")
        self.add_legend_item(legend_layout, 3, 0, "#FFD700", "Car (轿车)")
        self.add_legend_item(legend_layout, 4, 0, "#341f97", "Motor (摩托)")

        # 右侧列 (col=1)
        self.add_legend_item(legend_layout, 0, 1, "#FF6B6B", "Pedestrian (行人)")
        self.add_legend_item(legend_layout, 1, 1, "#fd79a8", "People (人群)")
        self.add_legend_item(legend_layout, 2, 1, "#55E6C1", "Tricycle (三轮)")
        self.add_legend_item(legend_layout, 3, 1, "#3498DB", "Truck (卡车)")
        self.add_legend_item(legend_layout, 4, 1, "#2ECC71", "Van (货车)")

        # 底部说明 (col=0)
        self.add_legend_item(legend_layout, 5, 0, "#FF0000", "———— 计数线")

        legend_frame.setLayout(legend_layout)
        self.right_panel.addWidget(legend_frame)

        self.right_panel.addStretch()  # 弹簧

        # 3. 画面控制 & 按钮
        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("🔍+")
        self.btn_zoom_out = QPushButton("🔍-")
        self.btn_zoom_in.setFixedSize(50, 40)
        self.btn_zoom_out.setFixedSize(50, 40)

        zoom_layout.addWidget(QLabel("画面缩放:"))
        zoom_layout.addWidget(self.btn_zoom_out)
        zoom_layout.addWidget(self.btn_zoom_in)
        self.right_panel.addLayout(zoom_layout)

        self.btn_open = QPushButton("📂 导入视频")
        self.btn_start = QPushButton("▶ 启动系统")
        self.btn_open.setCursor(Qt.PointingHandCursor)
        self.btn_start.setCursor(Qt.PointingHandCursor)

        self.right_panel.addWidget(self.btn_open)
        self.right_panel.addWidget(self.btn_start)

        main_layout.addLayout(self.right_panel, stretch=1)

        # 事件绑定
        self.btn_open.clicked.connect(self.open_file)
        self.btn_start.clicked.connect(self.toggle_video)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

    def create_stat_row(self, title_text, value_text, color):
        layout = QVBoxLayout()
        title = QLabel(title_text)
        title.setProperty("class", "stat_title")
        title.setStyleSheet("color: #888; font-size: 11px; font-weight: bold;")
        val = QLabel(value_text)
        val.setProperty("class", "stat_value")
        val.setStyleSheet(f"color: {color}; font-size: 26px; font-family: 'Arial Black';")
        layout.addWidget(title)
        layout.addWidget(val)
        return layout, val

    def add_legend_item(self, layout, row, col, color_code, text):
        container = QWidget()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        # 色块
        color_box = QLabel()
        color_box.setFixedSize(12, 12)
        color_box.setStyleSheet(f"background-color: {color_code}; border-radius: 3px;")

        # 文字
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #ddd; font-size: 11px;")

        h_layout.addWidget(color_box)
        h_layout.addWidget(lbl)
        h_layout.addStretch()

        container.setLayout(h_layout)

        # 关键点：这里要把组件加到 (row, col) 的位置
        layout.addWidget(container, row, col)

    # --- 逻辑部分 (保持你之前的拖拽逻辑不变) ---
    def init_logic(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.is_running = False

        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.last_mouse_pos = None
        self.is_dragging = False

        try:
            self.detector = SmartDetector(model_path='weights/yolov8m_cbam.pt', use_sahi=False)
            print("模型加载成功！")
        except Exception as e:
            print(f"模型加载失败: {e}")

    # --- 鼠标事件 (保持之前的不变) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.video_label.underMouse():
            self.is_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            self.offset_x -= delta.x() * 2
            self.offset_y -= delta.y() * 2

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.last_mouse_pos = None
            self.setCursor(QCursor(Qt.ArrowCursor))

    def zoom_in(self):
        if self.zoom_level < 4.0:
            self.zoom_level += 0.5

    def zoom_out(self):
        if self.zoom_level > 1.0:
            self.zoom_level -= 0.5
            if self.zoom_level == 1.0:
                self.offset_x = 0
                self.offset_y = 0

    # --- 显示与文件操作 (保持之前的不变) ---
    def display_image(self, img):
        h, w, _ = img.shape
        if self.zoom_level > 1.0:
            view_w = int(w / self.zoom_level)
            view_h = int(h / self.zoom_level)
            center_x = w // 2 + self.offset_x
            center_y = h // 2 + self.offset_y
            min_cx, max_cx = view_w // 2, w - view_w // 2
            min_cy, max_cy = view_h // 2, h - view_h // 2
            center_x = max(min_cx, min(center_x, max_cx))
            center_y = max(min_cy, min(center_y, max_cy))
            self.offset_x = center_x - w // 2
            self.offset_y = center_y - h // 2
            x1 = center_x - view_w // 2
            y1 = center_y - view_h // 2
            img = img[y1:y1 + view_h, x1:x1 + view_w]

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        qt_img = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "./data", "Videos (*.mp4 *.avi)")
        if path:
            if self.cap: self.cap.release()
            self.cap = cv2.VideoCapture(path)
            self.video_label.setText("✅ Ready")

    def toggle_video(self):
        if not self.cap: return
        if self.is_running:
            self.timer.stop()
            self.is_running = False
            self.btn_start.setText("▶ RESUME")
        else:
            self.timer.start(30)
            self.is_running = True
            self.btn_start.setText("⏸ PAUSE")

    def update_frame(self):
        if not self.cap or not self.cap.isOpened(): return
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return
        processed_frame, stats = self.detector.process_frame(frame)
        self.lbl_in.setText(str(stats.get('in_count', 0)))
        self.lbl_out.setText(str(stats.get('out_count', 0)))
        self.lbl_curr.setText(str(stats.get('current_people', 0)))
        self.display_image(processed_frame)

    def closeEvent(self, event):
        if self.cap: self.cap.release()