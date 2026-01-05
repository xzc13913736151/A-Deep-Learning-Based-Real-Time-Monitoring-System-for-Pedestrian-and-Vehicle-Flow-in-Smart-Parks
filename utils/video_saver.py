# utils/video_saver.py
import cv2
import threading
import time
import os
from collections import deque


class VideoSaver:
    def __init__(self, save_dir="records", max_cache_frames=150):
        self.save_dir = save_dir
        self.max_cache_frames = max_cache_frames
        self.frame_buffer = deque(maxlen=max_cache_frames)
        self.is_recording = False
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def update_frame(self, frame):
        if frame is None: return
        self.frame_buffer.append(frame)

    # 🟢 [关键修改] 增加 on_finish 参数
    def start_recording(self, duration=10, filename=None, on_finish=None):
        if self.is_recording:
            print("⚠️ 正在录制中，跳过本次请求")
            return None

        if filename is None:
            filename = f"alert_{int(time.time())}.mp4"

        # 转为绝对路径，防止 OpenCV 找不到
        filepath = os.path.join(os.path.abspath(self.save_dir), filename)

        # 启动线程，把 on_finish 传进去
        t = threading.Thread(
            target=self._record_process,
            args=(filepath, duration, on_finish)
        )
        t.start()
        return filepath

    # 🟢 [关键修改] 接收 on_finish
    def _record_process(self, filepath, duration, on_finish):
        try:
            self.is_recording = True
            print(f"🎥 [后台] 开始录制: {filepath}")

            current_buffer = list(self.frame_buffer)
            if not current_buffer:
                print("❌ 缓存为空，无法录制")
                self.is_recording = False
                return

            h, w, _ = current_buffer[0].shape
            # 使用 mp4v 编码，兼容性较好
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filepath, fourcc, 30.0, (w, h))

            if not out.isOpened():
                print("❌ 无法创建视频文件，请检查路径或权限")
                self.is_recording = False
                return

            # 1. 写入过去的缓存
            for frame in current_buffer:
                out.write(frame)

            # 2. 写入未来的画面
            start_time = time.time()
            while time.time() - start_time < duration:
                if self.frame_buffer:
                    out.write(self.frame_buffer[-1])
                time.sleep(0.03)  # 模拟 30FPS

            out.release()
            self.is_recording = False
            print(f"✅ [后台] 录制完成，文件已释放: {filepath}")

            # 🟢 [关键] 只有文件彻底关闭后，才执行回调！
            if on_finish:
                on_finish(filepath)

        except Exception as e:
            print(f"❌ 录像线程出错: {e}")
            self.is_recording = False
