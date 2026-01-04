# main.py
# 程序入口：负责连接 界面(GUI) 与 大脑(Detector)
import sys
import cv2
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

# 导入我们写的另外两个模块
from ui.main_window import MainWindowUI
from core.detector import SmartDetector


class MainApp(MainWindowUI):
    def __init__(self):
        super().__init__()  # 1. 初始化漂亮的界面

        # 2. 初始化 AI 大脑
        # 注意：现在还是用 yolov8n.pt，等你服务器训练好 best.pt 后
        # 记得把下面这行改成: model_path='weights/best.pt'
        try:
            self.detector = SmartDetector(model_path='runs/train/visdrone_test/weights/best.pt')
        except Exception as e:
            QMessageBox.critical(self, "错误", f"模型加载失败！\n请检查 weights 目录下是否有 pt 文件。\n错误信息: {e}")
            sys.exit(1)

        # 3. 信号绑定 (按钮点击 -> 触发函数)
        self.btn_open.clicked.connect(self.open_file)
        self.btn_start.clicked.connect(self.toggle_video)

        # 4. 视频定时器 (控制帧率)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)

        # 状态变量
        self.cap = None
        self.is_running = False

    def open_file(self):
        """打开视频文件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择视频", "./data", "Videos (*.mp4 *.avi *.mkv)")
        if path:
            # 如果之前有视频在跑，先释放
            if self.cap:
                self.cap.release()

            self.cap = cv2.VideoCapture(path)
            self.video_label.setText("✅ 视频已就绪，请点击 '开始监控'")

            # 这里的逻辑是：换新视频时，应该重置 UI 上的数字
            # (虽然 detector 内部的计数器还在累加，为了演示效果，我们在 UI 上清零视觉效果)
            self.lbl_in.setText("⬆️ 进入人数: 0")
            self.lbl_out.setText("⬇️ 离开人数: 0")
            self.lbl_curr.setText("👥 画面拥挤度: 0")

    def toggle_video(self):
        """开始/暂停开关"""
        if not self.cap:
            QMessageBox.warning(self, "提示", "请先点击 '加载视频' 按钮！")
            return

        if self.is_running:
            # 暂停
            self.timer.stop()
            self.is_running = False
            self.btn_start.setText("▶️ 继续监控")
            self.btn_start.setStyleSheet("background-color: #00b894; color: white;")  # 恢复绿色
        else:
            # 开始
            self.timer.start(30)  # 30ms 刷新一次 ≈ 33 FPS
            self.is_running = True
            self.btn_start.setText("⏸️ 暂停监控")
            self.btn_start.setStyleSheet("background-color: #e17055; color: white;")  # 变成橙色

    def update_frame(self):
        """每一帧执行的核心循环"""
        if not self.cap or not self.cap.isOpened():
            self.timer.stop()
            self.is_running = False
            self.btn_start.setText("▶️ 重新开始")
            return

        ret, frame = self.cap.read()
        if not ret:
            # 视频播放结束，自动循环播放 (可选)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            return

        # --- 核心：调用 AI 进行检测 ---
        try:
            processed_frame, stats = self.detector.process_frame(frame)
        except Exception as e:
            print(f"检测出错: {e}")
            return

        # --- 更新 UI 数据 ---
        self.lbl_in.setText(f"⬆️ 进入人数: {stats['in_count']}")
        self.lbl_out.setText(f"⬇️ 离开人数: {stats['out_count']}")

        # --- 拥挤报警逻辑 (适配暗黑风格) ---
        count = stats['current_people']
        limit = 20  # 报警阈值 (可以根据演示视频调整)

        if count > limit:
            # 报警状态：霓虹红色，加粗
            self.lbl_curr.setText(f"⚠️ 严重拥挤: {count} (超标!)")
            self.lbl_curr.setStyleSheet("color: #ff4757; font-size: 22px; font-weight: bold;")
        else:
            # 正常状态：恢复银白色
            self.lbl_curr.setText(f"👥 画面拥挤度: {count}")
            self.lbl_curr.setStyleSheet("color: #dfe6e9; font-size: 20px;")

        # --- 显示画面 ---
        self.display_image(processed_frame)

    def display_image(self, img):
        """将 OpenCV 图像转换为 PyQt 图像并显示"""
        # OpenCV 是 BGR，Qt 是 RGB，需要转换
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        bytes_per_line = ch * w

        qt_img = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # 保持比例缩放，平滑缩放 (SmoothTransformation)
        pixmap = QPixmap.fromImage(qt_img).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    def closeEvent(self, event):
        """关闭窗口时的清理工作"""
        if self.cap:
            self.cap.release()
        event.accept()


if __name__ == "__main__":
    # 高分屏自适应 (防止在高分辨率屏幕上字体太小)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())
