# ui/login_window.py
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QHBoxLayout, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from database.db_manager import DBManager
from ui.register_window import RegisterWindow


class LoginWindow(QWidget):
    login_success_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Campus Login")
        self.setFixedSize(500, 650)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.db = DBManager()
        self.reg_window = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(main_layout)

        # --- 卡片容器 ---
        self.card = QFrame()
        self.card.setObjectName("LoginCard")
        self.card.setFixedSize(440, 580)

        # 阴影特效
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        # 内部布局
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(45, 60, 45, 60)
        layout.setSpacing(25)

        # 1. 标题 LOGO
        title_lbl = QLabel("SMART CAMPUS")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("""
            background-color: transparent;
            color: #00b894; 
            font-size: 30px; 
            font-weight: 900; 
            font-family: 'Verdana'; 
            letter-spacing: 1px;
        """)

        sub_lbl = QLabel("智能园区 · 实时监控系统")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("""
            background-color: transparent;
            color: #b2bec3; 
            font-size: 14px; 
            letter-spacing: 3px; 
            margin-bottom: 20px;
        """)

        layout.addWidget(title_lbl)
        layout.addWidget(sub_lbl)

        # 2. 输入框
        input_style = """
            QLineEdit {
                background-color: #2d3436;
                border: none;
                border-bottom: 2px solid #636e72; 
                border-radius: 4px;
                padding: 12px 5px;
                color: white;
                font-size: 16px;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #00b894; 
                background-color: #353b48;
            }
            QLineEdit::placeholder { color: #636e72; font-size: 14px; }
        """

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username / 账号")
        self.user_input.setStyleSheet(input_style)

        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("Password / 密码")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setStyleSheet(input_style)
        self.pwd_input.returnPressed.connect(self.handle_login)

        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)

        layout.addSpacing(20)

        # 3. 登录按钮
        self.btn_login = QPushButton("LOGIN")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setFixedHeight(55)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #00b894; 
                color: white; 
                border-radius: 8px;
                font-weight: bold; 
                font-size: 18px;
                letter-spacing: 2px;
            }
            QPushButton:hover { background-color: #019E7E; }
            QPushButton:pressed { padding-top: 2px; padding-left: 2px; }
        """)
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

        # 4. 底部链接
        link_layout = QHBoxLayout()
        self.btn_close = QPushButton("退出")
        self.btn_close.clicked.connect(self.close)

        self.btn_register = QPushButton("注册新账号 →")
        self.btn_register.clicked.connect(self.open_register_window)

        for btn in [self.btn_close, self.btn_register]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #b2bec3; font-size: 13px; border: none;
                }
                QPushButton:hover { color: #00b894; text-decoration: underline; }
            """)

        link_layout.addWidget(self.btn_close)
        link_layout.addStretch()
        link_layout.addWidget(self.btn_register)

        layout.addLayout(link_layout)

        main_layout.addWidget(self.card)

        # 整体 CSS
        self.setStyleSheet("""
            QWidget { font-family: 'Microsoft YaHei'; }
            QFrame#LoginCard {
                background-color: #1e272e; 
                border-radius: 15px;
                border: 1px solid #333;
            }
        """)

    def handle_login(self):
        username = self.user_input.text().strip()
        password = self.pwd_input.text().strip()

        if not username or not password:
            self.show_message("提示", "请输入用户名和密码", "warning")
            return

        is_success, role = self.db.login(username, password)

        if is_success:
            print(f"✅ 登录成功: {username}")
            self.login_success_signal.emit({"username": username, "role": role})
        else:
            self.show_message("登录失败", "账号或密码错误", "error")

    def open_register_window(self):
        if self.reg_window is None:
            self.reg_window = RegisterWindow()
            self.reg_window.register_success_signal.connect(self.auto_fill_login)
        self.reg_window.move(self.geometry().center() - self.reg_window.rect().center())
        self.reg_window.show()

    def auto_fill_login(self, user, pwd):
        self.user_input.setText(user)
        self.pwd_input.setText(pwd)

    # 🟢 [核心修改] 升级版弹窗函数
    def show_message(self, title, text, type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)

        if type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "warning":
            msg.setIcon(QMessageBox.Warning)
        else:
            msg.setIcon(QMessageBox.Information)

        # 🟢 强力去背景样式表
        # * { background: transparent; } 会让所有子控件背景透明
        # 然后再单独给 QMessageBox 设置背景色
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e272e; /* 弹窗主背景 */
                border: 1px solid #444;
            }
            QMessageBox QLabel {
                color: #dfe6e9;
                background-color: transparent; /* 确保文字和图标背景透明 */
            }
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 15px;
                font-weight: bold;
                font-family: 'Microsoft YaHei';
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #019E7E;
            }
        """)
        msg.exec_()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()