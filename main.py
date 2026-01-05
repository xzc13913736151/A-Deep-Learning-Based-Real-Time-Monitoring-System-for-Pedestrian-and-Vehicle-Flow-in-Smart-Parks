# main.py
import sys
import traceback  # 用于打印报错信息
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt  # 修复高分屏缩放属性的引用

# --- 引入界面 ---
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

# --- 引入后端 (新增) ---
# 这行如果报错，说明你的文件夹结构不对，或者缺少 __init__.py
try:
    from database.db_manager import DBManager
except ImportError as e:
    print("❌ 严重错误: 无法导入数据库模块！请检查 database 文件夹和 __init__.py")
    print(f"详细错误: {e}")
    input("按回车键退出...")  # 暂停让你看清报错
    sys.exit(1)

# --- 全局样式表 ---
GLOBAL_STYLES = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
    font-size: 14px;
}
QScrollBar:vertical {
    border: none;
    background: #1e1e1e;
    width: 8px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #444;
    min-height: 20px;
    border-radius: 4px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QMessageBox {
    background-color: #2d3436;
    border: 1px solid #444;
}
"""


def main():
    # 1. 启动前的“全身检查” (捕获所有启动报错)
    try:
        # 适配高分屏 (标准写法)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        app = QApplication(sys.argv)
        app.setStyleSheet(GLOBAL_STYLES)

        # 2. 初始化数据库 (这一步会自动创建 smart_campus.db 文件)
        print("正在初始化数据库...")
        db = DBManager()
        print("✅ 数据库连接正常")

        # 3. 启动登录窗口
        login_ui = LoginWindow()

        def show_main_window(user_info):
            global main_ui
            # 传递用户信息给主窗口
            main_ui = MainWindow(user_info)
            main_ui.show()
            login_ui.close()

        login_ui.login_success_signal.connect(show_main_window)
        login_ui.show()

        print("🚀 系统启动成功！")
        sys.exit(app.exec_())

    except Exception as e:
        # ⚠️ 如果闪退，这里会捕获并打印错误
        print("\n" + "=" * 50)
        print("💥 程序启动时发生崩溃！")
        print("=" * 50)
        traceback.print_exc()  # 打印详细报错红字
        print("=" * 50)
        input("🔴 程序已暂停，请查看上方报错信息，按回车键退出...")


if __name__ == "__main__":
    main()