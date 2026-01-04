# main.py
import sys
from PyQt5.QtWidgets import QApplication
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

# --- 全局样式表 (高端暗黑风) ---
GLOBAL_STYLES = """
/* 全局背景和字体 */
QWidget {
    background-color: #121212; /* 极深黑背景 */
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 14px;
}

/* 滚动条美化 */
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 8px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 提示框美化 */
QMessageBox {
    background-color: #2d3436;
    border: 1px solid #444;
}
"""

def main():
    # 适配高分屏
    QApplication.setAttribute(sys.modules['PyQt5.QtCore'].Qt.AA_EnableHighDpiScaling)
    
    app = QApplication(sys.argv)
    app.setStyleSheet(GLOBAL_STYLES) # <--- 注入灵魂
    
    login_ui = LoginWindow()
    
    def show_main_window(user_info):
        global main_ui 
        main_ui = MainWindow(user_info)
        main_ui.show()
        login_ui.close()

    login_ui.login_success_signal.connect(show_main_window)
    login_ui.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()