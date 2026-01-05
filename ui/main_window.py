# ui/main_window.py
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

# 引入页面
from ui.monitor_grid import MonitorPage
from ui.history_window import HistoryPage
from ui.settings_window import SettingsWindow


class MainWindow(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle(f"Smart Campus Pro [v2.0] - {user_info.get('username')}")
        self.resize(1300, 800)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        # --- 侧边栏 (Sidebar) ---
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(240)
        # 🟢 统一色调 #1e272e
        self.sidebar.setStyleSheet("""
            QFrame { 
                background-color: #1e272e; 
                border-right: 1px solid #333;
            }
            QPushButton {
                background-color: transparent; 
                color: #888; 
                border: none;
                text-align: left; 
                padding: 18px 30px; 
                font-size: 15px;
                font-family: 'Microsoft YaHei';
                font-weight: 500;
            }
            QPushButton:hover { 
                background-color: #2d3436; color: white; 
            }
            QPushButton:checked { 
                background-color: #2d3436; 
                color: #00b894; /* 选中变绿 */
                border-left: 4px solid #00b894; /* 左侧亮条 */
                font-weight: bold;
            }
            QLabel#app_title {
                color: #fff; font-size: 22px; font-weight: bold; font-family: 'Verdana';
            }
        """)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(5)
        self.sidebar.setLayout(sidebar_layout)

        # LOGO 区域
        logo_box = QFrame()
        logo_box.setFixedHeight(100)
        logo_layout = QVBoxLayout()
        logo_layout.setAlignment(Qt.AlignCenter)
        title_lbl = QLabel("SMART CAMPUS")
        title_lbl.setObjectName("app_title")
        subtitle_lbl = QLabel("INTELLIGENT SYSTEM")
        subtitle_lbl.setStyleSheet("color: #636e72; font-size: 10px; letter-spacing: 3px;")

        logo_layout.addWidget(title_lbl)
        logo_layout.addWidget(subtitle_lbl)
        logo_box.setLayout(logo_layout)
        sidebar_layout.addWidget(logo_box)

        # 导航按钮
        self.btn_monitor = self.create_nav_btn("📊  实时监控中心")
        self.btn_playback = self.create_nav_btn("📼  历史事件回放")
        self.btn_settings = self.create_nav_btn("⚙️  系统参数设置")

        self.btn_monitor.setChecked(True)  # 默认选中

        sidebar_layout.addWidget(self.btn_monitor)
        sidebar_layout.addWidget(self.btn_playback)
        sidebar_layout.addWidget(self.btn_settings)
        sidebar_layout.addStretch()

        # 用户信息区
        user_box = QLabel(f"👤  {self.user_info.get('username', 'Admin')}")
        user_box.setStyleSheet("color: #aaa; padding: 20px; font-size: 13px;")
        sidebar_layout.addWidget(user_box)

        # --- 内容区 ---
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #121212;")

        # 实例化页面
        self.page_monitor = MonitorPage()
        self.page_history = HistoryPage()
        self.page_settings = SettingsWindow()

        self.content_area.addWidget(self.page_monitor)
        self.content_area.addWidget(self.page_history)
        self.content_area.addWidget(self.page_settings)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)

        # 逻辑连接
        self.btn_monitor.clicked.connect(lambda: self.switch_page(0, self.btn_monitor))
        self.btn_playback.clicked.connect(lambda: self.switch_page(1, self.btn_playback))
        self.btn_settings.clicked.connect(lambda: self.switch_page(2, self.btn_settings))

        # 🟢🟢🟢 [最关键的一步] 信号连接 🟢🟢🟢
        # 确保这行代码存在！它负责让监控页通知历史页刷新
        try:
            self.page_monitor.new_record_signal.connect(self.page_history.load_history_data)
            print("✅ 信号连接成功：监控页 -> 历史页")
        except Exception as e:
            print(f"❌ 信号连接失败: {e}")

    def create_nav_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        return btn

    def switch_page(self, index, btn):
        self.content_area.setCurrentIndex(index)
        for b in [self.btn_monitor, self.btn_playback, self.btn_settings]:
            b.setChecked(False)
        btn.setChecked(True)