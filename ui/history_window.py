# ui/history_window.py
import os
import cv2
import time
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton, QSlider,
                             QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from database.db_manager import DBManager


class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None
        self.is_slider_pressed = False

        self.init_ui()
        self.load_history_data()

    def init_ui(self):
        layout = QHBoxLayout()

        # --- 左侧：列表 ---
        left_layout = QVBoxLayout()
        title_label = QLabel("📅 历史报警/录像记录")
        title_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        left_layout.addWidget(title_label)

        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { 
                background-color: #2d3436; color: white; border: 1px solid #636e72; font-size: 14px;
            }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { 
                background-color: #00b894; color: black; border-radius: 3px;
            }
        """)
        self.file_list.itemClicked.connect(self.play_selected_video)
        left_layout.addWidget(self.file_list)

        # --- 右侧：播放器 ---
        right_layout = QVBoxLayout()

        self.video_screen = QLabel("请在左侧选择记录进行回放")
        self.video_screen.setAlignment(Qt.AlignCenter)
        self.video_screen.setStyleSheet("""
            background-color: black; color: #888; font-size: 16px; border: 2px solid #444; border-radius: 5px;
        """)
        self.video_screen.setMinimumSize(640, 360)
        self.video_screen.setScaledContents(True)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 8px; background: #2d3436; border-radius: 4px; }
            QSlider::handle:horizontal { background: #00b894; width: 16px; margin: -4px 0; border-radius: 8px; }
        """)
        self.slider.sliderPressed.connect(self.on_slider_pressed)
        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.sliderMoved.connect(self.on_slider_moved)

        btn_layout = QHBoxLayout()

        self.btn_play = QPushButton("▶ 播放/暂停")
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("""
            QPushButton {
                background-color: #0984e3; color: white; padding: 10px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #74b9ff; }
        """)

        self.btn_delete = QPushButton("🗑️ 删除此记录")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.clicked.connect(self.delete_current_video)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #d63031; color: white; padding: 10px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #ff7675; }
        """)

        btn_layout.addWidget(self.btn_play)
        btn_layout.addSpacing(10)
        btn_layout.addWidget(self.btn_delete)

        right_box = QGroupBox("📼 现场回放终端")
        right_box.setStyleSheet("QGroupBox { color: white; font-weight: bold; font-size: 14px; }")

        c_layout = QVBoxLayout()
        c_layout.addWidget(self.video_screen)
        c_layout.addWidget(self.slider)
        c_layout.addLayout(btn_layout)
        right_box.setLayout(c_layout)

        right_layout.addWidget(right_box)

        layout.addLayout(left_layout, stretch=1)
        layout.addLayout(right_layout, stretch=2)
        self.setLayout(layout)

    def load_history_data(self):
        print("🔄 刷新历史列表...")
        self.file_list.clear()
        events = self.db.get_all_events()

        if not events:
            self.file_list.addItem("暂无历史记录")
            return

        for event in events:
            display_text = f"[{event.timestamp}] {event.event_type} - {event.description}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, event.video_path)
            self.file_list.addItem(item)

    def play_selected_video(self, item):
        video_path = item.data(Qt.UserRole)

        # 先停止当前播放，防止冲突
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None

        if not video_path: return

        if not os.path.exists(video_path):
            self.video_screen.setText(f"❌ 文件不存在 (可点击删除清理):\n{video_path}")
            self.video_screen.setStyleSheet("background-color: #2d3436; color: #ff7675; font-size: 14px;")
            return

        print(f"正在加载视频: {video_path}")
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            self.video_screen.setText("❌ 无法解码视频文件")
            return

        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames > 0:
            self.slider.setRange(0, total_frames)
            self.slider.setValue(0)
            self.slider.setEnabled(True)
        else:
            self.slider.setEnabled(False)

        self.timer.start(30)
        self.btn_play.setText("⏸ 暂停")
        self.video_screen.setStyleSheet("background-color: black; border: 2px solid #00b894;")

    # 🔴🔴🔴 [核心修复] 强力删除逻辑：防闪退 + 强制清列表
    def delete_current_video(self):
        current_item = self.file_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择一条记录！")
            return

        video_path = current_item.data(Qt.UserRole)

        # 1. 弹出确认框
        reply = QMessageBox.question(self, '确认删除',
                                     "确定要删除吗？\n即使文件不存在，该记录也会被强制移除。",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply != QMessageBox.Yes:
            return

        # 🟢 2. [防闪退第一步] 绝对停止所有播放任务
        if self.timer.isActive():
            self.timer.stop()

        # 🟢 3. [防闪退第二步] 彻底释放视频资源
        if self.cap:
            self.cap.release()
            self.cap = None

        # 清空屏幕显示
        self.video_screen.clear()
        self.video_screen.setText("记录已删除")
        self.slider.setValue(0)

        # 🟢 4. 尝试删除物理文件 (加了 try-except 防止报错)
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                print(f"✅ 文件已删除: {video_path}")
            except Exception as e:
                print(f"⚠️ 文件删除出错 (可能是被占用): {e}")
        else:
            print("⚠️ 文件本身不存在，跳过物理删除")

        # 🟢 5. 尝试删除数据库记录 (失败也无所谓)
        if video_path:
            self.db.delete_event(video_path)

        # 🟢 6. [强制执行] 不管上面成不成功，直接从列表里把这一行删掉！
        # 这就是解决“坏记录删不掉”的关键
        row = self.file_list.row(current_item)
        self.file_list.takeItem(row)

        QMessageBox.information(self, "成功", "记录已清理。")

    def toggle_play(self):
        if not self.cap or not self.cap.isOpened(): return
        if self.timer.isActive():
            self.timer.stop();
            self.btn_play.setText("▶ 继续")
        else:
            self.timer.start(30);
            self.btn_play.setText("⏸ 暂停")

    def on_slider_pressed(self):
        self.is_slider_pressed = True;
        self.timer.stop()

    def on_slider_released(self):
        self.is_slider_pressed = False
        if self.cap: self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.slider.value()); self.timer.start(30)

    def on_slider_moved(self, pos):
        pass

    def update_frame(self):
        # 🟢 [防闪退第三步] 再次检查 cap 是否存在
        if self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if ret:
                    if not self.is_slider_pressed:
                        self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    qt_img = QImage(frame.data, w := frame.shape[1], h := frame.shape[0], w * 3, QImage.Format_RGB888)
                    self.video_screen.setPixmap(QPixmap.fromImage(qt_img).scaled(
                        self.video_screen.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    self.timer.stop();
                    self.btn_play.setText("🔄 重播");
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0);
                    self.slider.setValue(0)
            except Exception:
                self.timer.stop()
        else:
            self.timer.stop()