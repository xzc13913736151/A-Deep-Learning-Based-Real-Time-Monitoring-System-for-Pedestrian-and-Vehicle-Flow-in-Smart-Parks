# ui/settings_window.py
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QCheckBox, QSpinBox, QPushButton,
                             QFormLayout, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from configs.system_config import sys_config


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(25)  # 增加组件间距

        title = QLabel("⚙️ 系统参数设置")
        title.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # 🟢 [关键修改] 样式表里增加了 padding-top: 30px
        group_box_style = """
            QGroupBox { 
                color: #00b894; font-weight: bold; border: 1px solid #444; 
                margin-top: 15px; 
                padding-top: 30px; /* 让出标题位置，防止遮挡 */
                padding-bottom: 10px;
                padding-left: 10px;
                padding-right: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
        """

        # --- 算法设置组 ---
        algo_group = QGroupBox("🧠 智能算法配置")
        algo_group.setStyleSheet(group_box_style)
        algo_layout = QFormLayout()
        algo_layout.setSpacing(15)

        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(1, 100);
        self.spin_threshold.setSuffix(" 辆")
        self.spin_threshold.setFixedWidth(150);
        self.spin_threshold.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        algo_layout.addRow(QLabel("👥 拥堵报警阈值:"), self.spin_threshold)

        self.spin_speed = QSpinBox()
        self.spin_speed.setRange(20, 200);
        self.spin_speed.setSuffix(" km/h")
        self.spin_speed.setFixedWidth(150);
        self.spin_speed.setStyleSheet("background-color: #333; color: white; padding: 5px;")
        algo_layout.addRow(QLabel("⚡ 车辆限速阈值:"), self.spin_speed)

        self.chk_sahi = QCheckBox("🚀 启用 SAHI 高精度切片检测")
        self.chk_sahi.setStyleSheet("color: #ddd; font-size: 14px;")
        algo_layout.addRow(QLabel("精度模式:"), self.chk_sahi)

        algo_group.setLayout(algo_layout)
        layout.addWidget(algo_group)

        # --- 系统设置组 ---
        sys_group = QGroupBox("🖥️ 视频源与存储")
        # 复用修改后的样式
        sys_group.setStyleSheet(group_box_style.replace("#00b894", "#0984e3"))
        sys_layout = QFormLayout()
        sys_layout.setSpacing(15)

        self.input_rtsp = QLineEdit()
        self.input_rtsp.setPlaceholderText("0 或 RTSP地址")
        self.input_rtsp.setStyleSheet("background-color: #333; color: white; padding: 8px; border: 1px solid #555;")
        sys_layout.addRow(QLabel("默认视频源:"), self.input_rtsp)

        self.chk_record = QCheckBox("报警时自动录像并保存 (Auto Record)")
        self.chk_record.setStyleSheet("color: #ddd;")
        sys_layout.addRow(QLabel("安防策略:"), self.chk_record)

        sys_group.setLayout(sys_layout)
        layout.addWidget(sys_group)

        layout.addStretch()

        self.btn_save = QPushButton("💾 保存并应用配置")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setFixedSize(200, 50)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #00b894; color: white; 
                font-size: 16px; font-weight: bold; border-radius: 8px;
            }
            QPushButton:hover { background-color: #019E7E; }
        """)
        self.btn_save.clicked.connect(self.save_settings)

        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(self.btn_save)
        layout.addLayout(btn_container)

        self.setLayout(layout)

    def load_settings(self):
        self.spin_threshold.setValue(int(sys_config.get("alarm_threshold", 20)))
        self.spin_speed.setValue(int(sys_config.get("speed_limit", 60)))
        self.chk_sahi.setChecked(bool(sys_config.get("use_sahi", False)))
        self.input_rtsp.setText(str(sys_config.get("rtsp_url", "0")))
        self.chk_record.setChecked(bool(sys_config.get("auto_record", False)))

    def save_settings(self):
        try:
            sys_config.set("alarm_threshold", self.spin_threshold.value())
            sys_config.set("speed_limit", self.spin_speed.value())
            sys_config.set("use_sahi", self.chk_sahi.isChecked())
            sys_config.set("rtsp_url", self.input_rtsp.text().strip())
            sys_config.set("auto_record", self.chk_record.isChecked())
            QMessageBox.information(self, "成功", "✅ 配置已更新！\n监控页面将立即使用新参数。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")