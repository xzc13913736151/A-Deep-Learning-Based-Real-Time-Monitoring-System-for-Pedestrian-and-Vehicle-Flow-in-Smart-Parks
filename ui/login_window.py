# ui/login_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QFrame)
from PyQt5.QtCore import pyqtSignal, Qt

class LoginWindow(QWidget):
    # 定义一个信号，登录成功后发射，携带用户信息字典
    login_success_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("智慧园区系统 - 用户登录")
        self.resize(400, 350)
        
        # 简单的暗黑风样式
        self.setStyleSheet("""
            QWidget { background-color: #2d3436; color: white; }
            QLineEdit { 
                padding: 10px; border-radius: 5px; border: 1px solid #636e72; 
                background-color: #353b48; color: white; font-size: 14px;
            }
            QPushButton {
                background-color: #0984e3; color: white; padding: 10px; 
                border-radius: 5px; font-weight: bold; font-size: 16px;
            }
            QPushButton:hover { background-color: #74b9ff; }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)

        # 标题
        self.title_label = QLabel("Smart Campus Pro")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #00b894;")
        
        # 输入框
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("用户名 (admin)")
        
        self.pwd_input = QLineEdit()
        self.pwd_input.setPlaceholderText("密码 (123456)")
        self.pwd_input.setEchoMode(QLineEdit.Password)
        
        # 登录按钮
        self.btn_login = QPushButton("登 录")
        self.btn_login.clicked.connect(self.handle_login)

        layout.addWidget(self.title_label)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pwd_input)
        layout.addWidget(self.btn_login)
        layout.addStretch()
        
        self.setLayout(layout)

    def handle_login(self):
        username = self.user_input.text()
        password = self.pwd_input.text()

        # 模拟登录校验 (这里写死，方便你测试)
        if username == "admin" and password == "123456":
            # 登录成功，发射信号！
            user_data = {"username": "admin", "role": "superuser"}
            self.login_success_signal.emit(user_data)
        else:
            QMessageBox.warning(self, "登录失败", "用户名或密码错误\n(默认账号: admin / 123456)")