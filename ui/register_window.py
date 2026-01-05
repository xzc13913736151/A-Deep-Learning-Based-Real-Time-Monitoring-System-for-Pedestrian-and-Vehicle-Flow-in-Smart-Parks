# ui/register_window.py
import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QMessageBox, QHBoxLayout, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from database.db_manager import DBManager


class RegisterWindow(QWidget):
    register_success_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("新用户注册")
        self.setFixedSize(500, 650)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.db = DBManager()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        self.setLayout(main_layout)

        # --- 卡片容器 ---
        self.card = QFrame()
        self.card.setObjectName("Card")
        self.card.setFixedSize(440, 580)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(40, 50, 40, 50)
        card_layout.setSpacing(20)

        # 标题区
        title = QLabel("🚀 JOIN US")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            background-color: transparent;
            font-family: 'Arial Black'; font-size: 32px; color: #00b894; letter-spacing: 2px;
        """)

        subtitle = QLabel("创建您的智能园区账号")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            background-color: transparent;
            color: #b2bec3; font-size: 14px; margin-bottom: 20px;
        """)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)

        # 输入框样式
        input_style = """
            QLineEdit {
                background-color: #2d3436;
                border: 2px solid #2d3436;
                border-radius: 10px;
                padding: 12px 15px;
                color: white;
                font-size: 15px;
                selection-background-color: #00b894;
            }
            QLineEdit:focus {
                border: 2px solid #00b894;
                background-color: #353b48;
            }
            QLineEdit::placeholder { color: #636e72; }
        """

        self.input_user = QLineEdit()
        self.input_user.setPlaceholderText("👤  设置用户名")
        self.input_user.setStyleSheet(input_style)

        self.input_pwd = QLineEdit()
        self.input_pwd.setPlaceholderText("🔒  设置密码")
        self.input_pwd.setEchoMode(QLineEdit.Password)
        self.input_pwd.setStyleSheet(input_style)

        self.input_pwd2 = QLineEdit()
        self.input_pwd2.setPlaceholderText("🛡️  确认密码")
        self.input_pwd2.setEchoMode(QLineEdit.Password)
        self.input_pwd2.setStyleSheet(input_style)

        card_layout.addWidget(self.input_user)
        card_layout.addWidget(self.input_pwd)
        card_layout.addWidget(self.input_pwd2)

        card_layout.addSpacing(20)

        # 按钮区
        self.btn_submit = QPushButton("立即注册 / REGISTER")
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.setFixedHeight(50)
        self.btn_submit.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00b894, stop:1 #00cec9);
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #55efc4, stop:1 #81ecec);
            }
            QPushButton:pressed {
                padding-top: 3px; padding-left: 3px;
            }
        """)
        self.btn_submit.clicked.connect(self.handle_register)

        self.btn_cancel = QPushButton("返回登录")
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: transparent; color: #636e72; font-size: 14px;
            }
            QPushButton:hover { color: #b2bec3; text-decoration: underline; }
        """)
        self.btn_cancel.clicked.connect(self.close)

        card_layout.addWidget(self.btn_submit)
        card_layout.addWidget(self.btn_cancel)

        main_layout.addWidget(self.card)

        # 样式
        self.setStyleSheet("""
            QWidget { background-color: transparent; font-family: 'Microsoft YaHei'; }
            QFrame#Card {
                background-color: #1e272e;
                border-radius: 20px;
                border: 1px solid #444;
            }
        """)

    def handle_register(self):
        user = self.input_user.text().strip()
        pwd = self.input_pwd.text().strip()
        pwd2 = self.input_pwd2.text().strip()

        if not user or not pwd:
            self.show_message("提示", "用户名和密码不能为空", "warning")
            return

        if pwd != pwd2:
            self.show_message("错误", "两次输入的密码不一致！", "warning")
            return

        success = self.db.add_user(user, pwd, role="user")

        if success:
            self.show_message("成功", f"欢迎加入！\n用户 {user} 注册成功。", "success")
            self.register_success_signal.emit(user, pwd)
            self.close()
        else:
            self.show_message("失败", "该用户名已被占用，请换一个。", "error")

    # 🟢 [核心修改] 升级版弹窗函数
    def show_message(self, title, text, type="info"):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)

        if type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif type == "success":
            msg.setIcon(QMessageBox.Information)
        else:
            msg.setIcon(QMessageBox.Warning)

        # 🟢 强力去背景样式表
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #1e272e; 
                border: 1px solid #444;
            }
            QMessageBox QLabel {
                color: #dfe6e9;
                background-color: transparent; /* 修复图标和文字背景 */
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