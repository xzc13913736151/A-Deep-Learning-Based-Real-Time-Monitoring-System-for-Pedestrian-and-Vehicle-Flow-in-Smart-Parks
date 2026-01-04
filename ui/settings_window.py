# ui/settings_window.py
from PyQt5.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox, 
                             QCheckBox, QPushButton, QLabel, QVBoxLayout, QMessageBox, QFrame)
from PyQt5.QtCore import Qt

class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 60, 60, 60) # 增加留白，显得大气
        
        # --- 核心美化：极简主义暗黑风 ---
        self.setStyleSheet("""
            /* 1. 全局设定：深灰背景，无边框 */
            QWidget { 
                background-color: #1e1e1e; 
                color: #dfe6e9; 
                font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
                border: none; /* 关键：去掉所有默认边框 */
            }
            
            /* 2. 标签专用：背景透明！去掉那个讨厌的框框！ */
            QLabel {
                background-color: transparent; /* 关键：让字浮在背景上 */
                color: #b2bec3;                /* 稍微暗一点的灰色，不刺眼 */
                font-size: 15px;
                font-weight: 500;
                border: none;                  /* 确保没有边框 */
            }

            /* 3. 输入框：扁平化设计 */
            QLineEdit, QSpinBox { 
                background-color: #2d3436;     /* 比背景稍亮的灰色 */
                color: #ffffff; 
                padding: 10px;                 /* 内边距大一点，舒服 */
                border: 1px solid #444;        /* 极细的边框 */
                border-radius: 6px;            /* 圆角 */
                font-size: 14px;
            }
            /* 鼠标点进去时，边框变亮，而不是整个发光 */
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #00b894;     /* 激活色 */
                background-color: #353b48;
            }

            /* 4. 复选框 */
            QCheckBox {
                background-color: transparent; /* 去掉复选框文字的背景 */
                color: #dfe6e9;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px; 
                height: 18px;
                border: 1px solid #636e72;
                border-radius: 4px;
                background: #2d3436;
            }
            QCheckBox::indicator:checked {
                background-color: #00b894;
                border: 1px solid #00b894;
            }

            /* 5. 按钮：悬浮感 */
            QPushButton {
                background-color: #00b894; 
                color: white; 
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #55efc4;
                margin-top: -2px; /* 简单的上浮动画效果 */
            }
            QPushButton:pressed {
                background-color: #00cec9;
                margin-top: 2px;
            }
        """)

        # --- 标题区 ---
        title_box = QFrame()
        title_layout = QVBoxLayout()
        title = QLabel("System Configuration")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: bold; background: transparent;")
        subtitle = QLabel("在此配置摄像头源、报警阈值及录像存储策略")
        subtitle.setStyleSheet("color: #636e72; font-size: 14px; background: transparent;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        main_layout.addLayout(title_layout)
        
        main_layout.addSpacing(40) # 增加间距

        # --- 表单区 ---
        form_layout = QFormLayout()
        form_layout.setSpacing(25)       # 行距
        form_layout.setHorizontalSpacing(20) # 标签和输入框的间距
        form_layout.setLabelAlignment(Qt.AlignLeft) # 标签左对齐更现代

        # 1. RTSP 地址
        self.input_rtsp = QLineEdit()
        self.input_rtsp.setPlaceholderText("例如: rtsp://192.168.1.100/stream")
        self.input_rtsp.setMinimumWidth(450)
        # 给 Label 单独加样式，不需要背景色
        lbl_rtsp = QLabel("RTSP 视频源地址")
        form_layout.addRow(lbl_rtsp, self.input_rtsp)

        # 2. 阈值
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(5, 500)
        self.spin_threshold.setValue(20)
        self.spin_threshold.setSuffix(" 人 (People)")
        self.spin_threshold.setFixedWidth(150) # 只有数字框短一点
        lbl_limit = QLabel("拥挤报警阈值")
        form_layout.addRow(lbl_limit, self.spin_threshold)

        # 3. 录像开关
        self.check_save = QCheckBox("开启异常自动录像 (Auto Record)")
        self.check_save.setChecked(True)
        # 用一个空标签占位，让复选框对齐
        form_layout.addRow(QLabel("存储策略"), self.check_save)

        # 4. 声音开关
        self.check_sound = QCheckBox("启用蜂鸣器报警 (Buzzer)")
        form_layout.addRow(QLabel("硬件联动"), self.check_sound)

        main_layout.addLayout(form_layout)
        main_layout.addStretch()

        # --- 底部按钮 ---
        btn_layout = QVBoxLayout()
        self.btn_save = QPushButton("保存当前配置 (Save Changes)")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.clicked.connect(self.save_config)
        
        # 给按钮加个阴影效果（可选，增加层次感）
        # 这里用简单的 QSS 实现
        
        btn_layout.addWidget(self.btn_save)
        btn_layout.setAlignment(Qt.AlignRight) # 按钮靠右
        
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def save_config(self):
        QMessageBox.information(self, "系统提示", "配置已保存成功！\nConfiguration Saved.")