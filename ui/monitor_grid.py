# ui/monitor_grid.py
import cv2
import time
import os
import traceback
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QFrame, QFileDialog, QSizePolicy,
                             QGridLayout, QMessageBox, QSlider)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QCursor
from core.detector import SmartDetector

try:
    from utils.video_saver import VideoSaver
    from database.db_manager import DBManager
    from database.models import Event
    from configs.system_config import sys_config
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys_config = type('Config', (), {'get': lambda self, k, d: d, 'set': lambda self, k, v: None})()


class MonitorPage(QWidget):
    new_record_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        if not os.path.exists("records"): os.makedirs("records")
        if not os.path.exists("snapshots"): os.makedirs("snapshots")

        self.init_ui()
        self.init_logic()

    def init_ui(self):
        # ... (UI 样式保持不变，为了节省篇幅，这里复用你现有的 UI 代码) ...
        # ... (如果你怕覆盖错，可以直接复制下面完整的 init_ui) ...
        self.setStyleSheet("""
            QLabel#video_screen { background-color: #000; border: 2px solid #333; border-radius: 12px; }
            QFrame#panel { background-color: #1e1e24; border-radius: 15px; border: 1px solid #333; }
            QLabel.stat_title { color: #aaa; font-size: 14px; font-weight: bold; margin-bottom: 2px; }
            QLabel.stat_value { color: #fff; font-size: 36px; font-weight: bold; font-family: 'Arial Black'; }
            QPushButton { background-color: #2d3436; color: white; border: 1px solid #444; border-radius: 8px; padding: 0px; font-weight: bold; font-size: 15px; }
            QPushButton:hover { background-color: #00b894; border: 1px solid #00b894; color: #fff; }
            QSlider::groove:horizontal { height: 6px; background: #333; border-radius: 3px; }
            QSlider::handle:horizontal { background: #00b894; width: 14px; margin: -4px 0; border-radius: 7px; }
        """)

        main_layout = QHBoxLayout();
        main_layout.setContentsMargins(20, 20, 20, 20);
        main_layout.setSpacing(25)
        self.setLayout(main_layout)

        left_layout = QVBoxLayout()
        self.video_label = QLabel("Waiting for Signal...");
        self.video_label.setObjectName("video_screen")
        self.video_label.setAlignment(Qt.AlignCenter);
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored);
        self.video_label.setMouseTracking(True)
        left_layout.addWidget(self.video_label, stretch=1)

        progress_layout = QHBoxLayout()
        self.lbl_time_curr = QLabel("00:00");
        self.lbl_time_curr.setStyleSheet("color: #aaa; font-family: monospace;")
        self.slider_video = QSlider(Qt.Horizontal);
        self.slider_video.setEnabled(False);
        self.slider_video.setCursor(Qt.PointingHandCursor)
        self.slider_video.sliderPressed.connect(self.on_slider_pressed);
        self.slider_video.sliderReleased.connect(self.on_slider_released);
        self.slider_video.sliderMoved.connect(self.on_slider_moved)
        self.lbl_time_total = QLabel("00:00");
        self.lbl_time_total.setStyleSheet("color: #aaa; font-family: monospace;")
        progress_layout.addWidget(self.lbl_time_curr);
        progress_layout.addWidget(self.slider_video);
        progress_layout.addWidget(self.lbl_time_total)
        left_layout.addLayout(progress_layout)
        main_layout.addLayout(left_layout, stretch=3)

        self.right_panel = QVBoxLayout();
        self.right_panel.setSpacing(20)
        title = QLabel("👁️ TRAFFIC BRAIN");
        title.setStyleSheet("color: #00b894; font-size: 26px; font-weight: 900; letter-spacing: 1px;");
        title.setFixedHeight(40)
        self.right_panel.addWidget(title)

        stats_frame = QFrame();
        stats_frame.setObjectName("panel")
        stats_layout = QVBoxLayout();
        stats_layout.setContentsMargins(20, 25, 20, 25);
        stats_layout.setSpacing(20)
        row1 = self.create_stat_row("⬇️ IN-FLOW (入)", "0", "#00cec9");
        self.lbl_in = row1[1]
        row2 = self.create_stat_row("⬆️ OUT-FLOW (出)", "0", "#fd79a8");
        self.lbl_out = row2[1]
        row3 = self.create_stat_row("🚗 DENSITY (当前)", "0", "#ffeaa7");
        self.lbl_curr = row3[1]
        stats_layout.addLayout(row1[0]);
        stats_layout.addLayout(row2[0]);
        stats_layout.addLayout(row3[0])
        stats_frame.setLayout(stats_layout)
        self.right_panel.addWidget(stats_frame, stretch=2)

        legend_frame = QFrame();
        legend_frame.setObjectName("panel")
        legend_layout = QGridLayout();
        legend_layout.setContentsMargins(20, 20, 20, 20);
        legend_layout.setSpacing(15)
        self.add_legend_item(legend_layout, 0, 0, "#00FFFF", "AwningTri");
        self.add_legend_item(legend_layout, 0, 1, "#FF6B6B", "Pedestrian")
        self.add_legend_item(legend_layout, 1, 0, "#FF9F43", "Bicycle");
        self.add_legend_item(legend_layout, 1, 1, "#fd79a8", "People")
        self.add_legend_item(legend_layout, 2, 0, "#9B59B6", "Bus");
        self.add_legend_item(legend_layout, 2, 1, "#55E6C1", "Tricycle")
        self.add_legend_item(legend_layout, 3, 0, "#FFD700", "Car");
        self.add_legend_item(legend_layout, 3, 1, "#3498DB", "Truck")
        self.add_legend_item(legend_layout, 4, 0, "#341f97", "Motor");
        self.add_legend_item(legend_layout, 4, 1, "#2ECC71", "Van")
        legend_frame.setLayout(legend_layout)
        self.right_panel.addWidget(legend_frame, stretch=1)

        zoom_layout = QHBoxLayout()
        self.btn_zoom_in = QPushButton("🔍+");
        self.btn_zoom_in.setFixedSize(60, 50);
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out = QPushButton("🔍-");
        self.btn_zoom_out.setFixedSize(60, 50);
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(QLabel("视图缩放:"));
        zoom_layout.addWidget(self.btn_zoom_out);
        zoom_layout.addWidget(self.btn_zoom_in)
        self.right_panel.addLayout(zoom_layout)

        self.btn_open = QPushButton("📂 导入视频源");
        self.btn_open.setFixedHeight(55);
        self.btn_open.clicked.connect(self.open_file)
        self.btn_start = QPushButton("▶ 启动分析引擎");
        self.btn_start.setFixedHeight(55);
        self.btn_start.clicked.connect(self.toggle_video)
        self.right_panel.addWidget(self.btn_open);
        self.right_panel.addWidget(self.btn_start)
        main_layout.addLayout(self.right_panel, stretch=1)

    def create_stat_row(self, title_text, value_text, color):
        layout = QVBoxLayout()
        title = QLabel(title_text);
        title.setProperty("class", "stat_title")
        val = QLabel(value_text);
        val.setProperty("class", "stat_value");
        val.setStyleSheet(f"color: {color};")
        layout.addWidget(title);
        layout.addWidget(val)
        return layout, val

    def add_legend_item(self, layout, row, col, color_code, text):
        container = QWidget()
        h = QHBoxLayout();
        h.setContentsMargins(0, 0, 0, 0);
        h.setSpacing(8)
        box = QLabel();
        box.setFixedSize(14, 14);
        box.setStyleSheet(f"background-color: {color_code}; border-radius: 3px;")
        lbl = QLabel(text);
        lbl.setStyleSheet("color: #ddd; font-size: 12px; font-weight: bold;")
        h.addWidget(box);
        h.addWidget(lbl);
        h.addStretch()
        container.setLayout(h);
        layout.addWidget(container, row, col)

    # --- 逻辑核心 ---
    def init_logic(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.is_running = False

        self.zoom_level = 1.0;
        self.offset_x = 0;
        self.offset_y = 0
        self.last_mouse_pos = None;
        self.is_dragging = False
        self.is_slider_pressed = False

        # 🟢 [关键修复] 补上这一行！之前报错就是因为缺了这个
        self.frame_counter = 0

        try:
            self.detector = SmartDetector(model_path='weights/yolov8m_cbam.pt')
            self.saver = VideoSaver(save_dir="records", max_cache_frames=150)
            self.db = DBManager()
        except Exception as e:
            print(f"❌ 初始化失败: {e}")

        # 自动加载默认视频源
        default_source = sys_config.get("rtsp_url")
        if default_source and default_source != "0" and default_source.strip() != "":
            self.load_video_source(default_source)


    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "./data", "Videos (*.mp4 *.avi)")
        if path:
            # 更新设置里的记录 (可选)
            sys_config.set("rtsp_url", path)
            self.load_video_source(path)

    # 🟢 [提取] 独立的视频加载函数
    def load_video_source(self, path):
        if self.cap: self.cap.release()

        # 尝试打开
        if path.isdigit():
            self.cap = cv2.VideoCapture(int(path))  # 摄像头
        else:
            self.cap = cv2.VideoCapture(path)  # 文件或流

        # 初始化进度条
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            self.slider_video.setRange(0, total_frames)
            self.slider_video.setEnabled(True)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                seconds = total_frames / fps
                self.lbl_time_total.setText(f"{int(seconds // 60):02d}:{int(seconds % 60):02d}")
        else:
            self.slider_video.setEnabled(False)  # 直播流不可拖动

        if self.cap.isOpened():
            self.video_label.setText(f"✅ Ready: {os.path.basename(path)}")
        else:
            self.video_label.setText("❌ Failed to open source")

    def toggle_video(self):
        if not self.cap: return
        if self.is_running:
            self.timer.stop();
            self.is_running = False;
            self.btn_start.setText("▶ RESUME")
        else:
            self.timer.start(30);
            self.is_running = True;
            self.btn_start.setText("⏸ PAUSE")

    def on_slider_pressed(self):
        self.is_slider_pressed = True

    def on_slider_released(self):
        self.is_slider_pressed = False
        if self.cap: self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.slider_video.value())

    def on_slider_moved(self, pos):
        if self.cap:
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                seconds = pos / fps
                self.lbl_time_curr.setText(f"{int(seconds // 60):02d}:{int(seconds % 60):02d}")

    def update_frame(self):
        try:
            if not self.cap or not self.cap.isOpened(): return
            if self.is_slider_pressed: return

            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return

            self.frame_counter += 1

            # 更新进度条
            curr_pos = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.slider_video.setValue(curr_pos)

            fps = self.cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                sec = curr_pos / fps
                self.lbl_time_curr.setText(f"{int(sec // 60):02d}:{int(sec % 60):02d}")

            self.saver.update_frame(frame)

            # 获取设置
            use_sahi_btn = sys_config.get("use_sahi", False)
            speed_limit = sys_config.get("speed_limit", 60)

            # 🟢 [修改] 增加跳帧逻辑：每 10 帧才允许跑一次 SAHI
            # 如果电脑配置低，把这个数字改大（比如 30）
            real_use_sahi = False
            if use_sahi_btn:
                if self.frame_counter % 10 == 0:
                    real_use_sahi = True
                    print(f"⚡ 第 {self.frame_counter} 帧：尝试高精度检测...")  # 打印日志看看卡不卡

            # 计时，看看检测花了多久
            t1 = time.time()
            processed_frame, stats = self.detector.process_frame(
                frame,
                use_sahi_override=real_use_sahi,
                speed_limit=speed_limit
            )
            t2 = time.time()
            if real_use_sahi and (t2 - t1) > 0.5:
                print(f"⚠️ SAHI 检测耗时: {t2 - t1:.2f}秒 (如果这个时间太长，界面就会卡)")

            self.lbl_in.setText(str(stats.get('in_count', 0)))
            self.lbl_out.setText(str(stats.get('out_count', 0)))
            curr = stats.get('current_people', 0)
            self.lbl_curr.setText(str(curr))

            limit = sys_config.get("alarm_threshold", 10)
            alerts = stats.get('alerts', [])
            if curr > limit: alerts.append(f"拥堵: {curr}辆")
            if len(alerts) > 0: self.trigger_alert(alerts, processed_frame)

            self.display_image(processed_frame)

        except Exception as e:
            # 🔴 [关键修改] 报错后不再停止计时器 (self.timer.stop)，而是打印错误并继续播放
            print(f"\n❌ update_frame 发生错误 (视频保持播放): {e}")
            traceback.print_exc()
            # 如果出错，尝试显示原图，保证画面不黑屏
            try:
                if 'frame' in locals():
                    self.display_image(frame)
            except:
                pass

    def trigger_alert(self, alert_msgs, current_frame):
        if self.saver.is_recording: return
        print(f"🚨 {alert_msgs}")

        snapshot_name = f"snap_{int(time.time())}.jpg"
        snapshot_path = os.path.join(os.path.abspath("snapshots"), snapshot_name)
        cv2.imwrite(snapshot_path, current_frame)

        def on_record_finished(saved_video_path):
            try:
                if not self.isVisible() and not self.video_label: return
            except RuntimeError:
                return

            print(f"💾 [回调] 录像文件已就绪: {saved_video_path}")
            try:
                new_event = Event(
                    event_type="Traffic Alert",
                    camera_id="CAM_01",
                    description=str(alert_msgs),
                    video_path=saved_video_path
                )
                self.db.insert_event(new_event)
                print("✅ 事件已存入数据库")
                self.new_record_signal.emit()
            except Exception as e:
                print(f"❌ 数据库存储失败: {e}")

        self.saver.start_recording(duration=10, on_finish=on_record_finished)

    def display_image(self, img):
        if img is None: return
        h, w, _ = img.shape
        if self.zoom_level > 1.0:
            view_w, view_h = int(w / self.zoom_level), int(h / self.zoom_level)
            cx, cy = w // 2 + self.offset_x, h // 2 + self.offset_y
            cx = max(view_w // 2, min(cx, w - view_w // 2))
            cy = max(view_h // 2, min(cy, h - view_h // 2))
            self.offset_x, self.offset_y = cx - w // 2, cy - h // 2
            x1, y1 = cx - view_w // 2, cy - view_h // 2
            img = img[y1:y1 + view_h, x1:x1 + view_w]

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qt_img = QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.video_label.underMouse():
            self.is_dragging = True;
            self.last_mouse_pos = event.pos();
            self.setCursor(QCursor(Qt.ClosedHandCursor))

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos;
            self.last_mouse_pos = event.pos()
            if self.zoom_level > 1.0: self.offset_x -= delta.x() * 2; self.offset_y -= delta.y() * 2

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton: self.is_dragging = False; self.setCursor(QCursor(Qt.ArrowCursor))

    def zoom_in(self):
        if self.zoom_level < 4.0: self.zoom_level += 0.5

    def zoom_out(self):
        if self.zoom_level > 1.0: self.zoom_level -= 0.5;
        if self.zoom_level == 1.0: self.offset_x, self.offset_y = 0, 0

    def closeEvent(self, event):
        if self.cap: self.cap.release()