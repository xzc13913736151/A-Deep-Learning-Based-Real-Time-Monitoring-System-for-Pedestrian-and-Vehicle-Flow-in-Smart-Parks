# main_window.py
from PyQt5.QtWidgets import QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QGroupBox
from PyQt5.QtCore import Qt


class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能园区流量监控系统 (Pro版) - Powered by YOLOv8")
        self.setGeometry(100, 100, 1300, 800)

        # --- 核心美化区：QSS 样式表 ---
        # 这里定义了整个软件的 "暗黑科技风" 皮肤
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e; /* 深灰背景 */
            }
            QLabel {
                color: #e0e0e0; /* 文字银白色 */
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QGroupBox {
                border: 2px solid #333333;
                border-radius: 8px;
                margin-top: 20px;
                font-size: 16px;
                font-weight: bold;
                color: #00b894; /* 标题颜色 */
                background-color: #252525;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0984e3; /* 按钮蓝 */
                color: white;
                border-radius: 5px;
                font-size: 16px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74b9ff; /* 悬停变亮 */
            }
            QPushButton#btn_start {
                background-color: #00b894; /* 开始按钮绿色 */
            }
            QPushButton#btn_start:hover {
                background-color: #55efc4;
            }
        """)

        # 主部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 全局布局 (水平：左边视频，右边数据)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)  # 留点边距
        self.main_layout.setSpacing(20)  # 左右间距

        # --- 左侧：视频显示区 ---
        self.video_label = QLabel("Waiting for Video Input...\n\n请点击右侧 '加载视频' 按钮")
        self.video_label.setAlignment(Qt.AlignCenter)
        # 给视频区加一个深黑色的背景框
        self.video_label.setStyleSheet("""
            background-color: #000000; 
            color: #888888; 
            font-size: 20px; 
            border: 2px solid #444; 
            border-radius: 12px;
        """)
        self.video_label.setMinimumSize(960, 540)  # 16:9 比例
        self.main_layout.addWidget(self.video_label, stretch=3)  # 占比 3

        # --- 右侧：控制与数据区 ---
        self.right_panel = QVBoxLayout()

        # 1. 标题区
        self.title_label = QLabel("📊 实时监控看板")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 20px; color: #ffffff;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.right_panel.addWidget(self.title_label)

        # 2. 数据展示卡片 (用 GroupBox 包装)
        self.stats_box = QGroupBox("流量统计")
        self.stats_layout = QVBoxLayout()
        self.stats_layout.setSpacing(15)  # 数据行间距

        self.lbl_in = QLabel("⬆️ 进入人数: 0")
        self.lbl_in.setStyleSheet("color: #fab1a0; font-size: 22px; font-weight: bold;")  # 淡红色

        self.lbl_out = QLabel("⬇️ 离开人数: 0")
        self.lbl_out.setStyleSheet("color: #81ecec; font-size: 22px; font-weight: bold;")  # 青色

        self.lbl_curr = QLabel("👥 画面拥挤度: 0")
        self.lbl_curr.setStyleSheet("color: #dfe6e9; font-size: 20px;")  # 灰白色

        self.stats_layout.addWidget(self.lbl_in)
        self.stats_layout.addWidget(self.lbl_out)
        self.stats_layout.addWidget(self.lbl_curr)
        self.stats_box.setLayout(self.stats_layout)
        self.right_panel.addWidget(self.stats_box)

        # 3. 按钮区
        self.right_panel.addStretch()  # 弹簧，把上面顶上去

        self.btn_open = QPushButton("📂 加载演示视频")
        self.btn_open.setCursor(Qt.PointingHandCursor)  # 鼠标放上去变小手

        self.btn_start = QPushButton("▶️ 开始监控")
        self.btn_start.setObjectName("btn_start")  # 设置ID以便单独应用绿色样式
        self.btn_start.setCursor(Qt.PointingHandCursor)

        self.right_panel.addWidget(self.btn_open)
        self.right_panel.addSpacing(10)  # 按钮之间空一点
        self.right_panel.addWidget(self.btn_start)

        self.main_layout.addLayout(self.right_panel, stretch=1)  # 占比 1
