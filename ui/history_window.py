# ui/history_window.py
import os
import cv2
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget, 
                             QLabel, QPushButton, QSlider, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap

class HistoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.cap = None

    def init_ui(self):
        # 布局：左边列表，右边播放器
        layout = QHBoxLayout()
        
        # --- 左侧：录像文件列表 ---
        left_layout = QVBoxLayout()
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { background-color: #2d3436; color: white; border: 1px solid #636e72; }
            QListWidget::item:selected { background-color: #00b894; color: black; }
        """)
        # 模拟一些数据 (等同学C写好数据库后，这里改为读取数据库)
        self.file_list.addItems(["2025-01-04_14-30-00.mp4", "2025-01-04_15-00-00.mp4", "报警_摔倒.mp4"])
        self.file_list.itemClicked.connect(self.load_video) # 点击播放
        
        left_layout.addWidget(QLabel("📅 历史录像列表"))
        left_layout.addWidget(self.file_list)
        
        # --- 右侧：播放区域 ---
        right_layout = QVBoxLayout()
        
        # 视频屏幕
        self.video_screen = QLabel("选择左侧文件开始回放")
        self.video_screen.setAlignment(Qt.AlignCenter)
        self.video_screen.setStyleSheet("background-color: black; color: #666; font-size: 16px; border: 2px solid #444;")
        self.video_screen.setMinimumSize(640, 360)
        
        # 进度条 (暂时仅作展示)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setStyleSheet("QSlider::handle:horizontal { background-color: #00b894; }")
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        self.btn_play = QPushButton("▶ 播放/暂停")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("background-color: #0984e3; color: white; padding: 8px;")
        btn_layout.addWidget(self.btn_play)
        
        right_box = QGroupBox("📼 回放监视器")
        right_box.setStyleSheet("color: white; font-weight: bold;")
        
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.video_screen)
        container_layout.addWidget(self.slider)
        container_layout.addLayout(btn_layout)
        right_box.setLayout(container_layout)
        
        right_layout.addWidget(right_box)

        # 组装
        layout.addLayout(left_layout, stretch=1)
        layout.addLayout(right_layout, stretch=3)
        self.setLayout(layout)

    def load_video(self, item):
        filename = item.text()
        # 这里假设视频都在 data/ 目录下，你需要根据实际情况修改路径
        # 甚至可以先放一个真实的测试视频在项目根目录试试
        video_path = f"./data/{filename}" 
        
        # 为了演示，如果文件不存在，我们先不报错，只打印
        print(f"尝试播放: {video_path}")
        
        if self.cap: self.cap.release()
        self.cap = cv2.VideoCapture(video_path) # 这里如果读不到文件会黑屏
        
        if not self.cap.isOpened():
            self.video_screen.setText(f"❌ 无法打开文件:\n{filename}\n请确保文件在 data 目录下")
            return
            
        self.timer.start(30)
        self.btn_play.setText("⏸ 暂停")

    def toggle_play(self):
        if self.timer.isActive():
            self.timer.stop()
            self.btn_play.setText("▶ 继续")
        else:
            self.timer.start(30)
            self.btn_play.setText("⏸ 暂停")

    def update_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                qt_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                self.video_screen.setPixmap(QPixmap.fromImage(qt_img).scaled(
                    self.video_screen.width(), self.video_screen.height(), Qt.KeepAspectRatio))
            else:
                self.timer.stop()
                self.btn_play.setText("🔄 重播")
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)