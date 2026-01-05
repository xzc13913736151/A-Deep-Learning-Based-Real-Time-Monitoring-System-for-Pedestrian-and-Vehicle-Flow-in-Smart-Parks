# core/detector.py
import cv2
import torch
import numpy as np
import supervision as sv
from ultralytics import YOLO
import os

try:
    from core.speed_estimator import SpeedEstimator
except ImportError:
    import sys

    sys.path.append(os.getcwd())
    from core.speed_estimator import SpeedEstimator

# 导入 GPU 版 SAHI
try:
    from core.sahi_inference import SahiWrapper

    SAHI_AVAILABLE = True
except ImportError:
    print("⚠️ 未找到 core/sahi_inference.py，SAHI 功能将不可用")
    SAHI_AVAILABLE = False


class SmartDetector:
    def __init__(self, model_path=None, rtsp_url=None, use_sahi=False):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(current_dir)
            model_path = os.path.join(root_dir, 'weights', 'yolov8m_cbam.pt')

        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"💻 运行设备: {self.device}")

        print(f"🔄 正在加载基座模型: {model_path} ...")
        try:
            self.model = YOLO(model_path)
        except:
            print("⚠️ 模型加载失败，使用默认 yolov8n.pt")
            self.model = YOLO('yolov8n.pt')

        self.sahi_agent = None
        self.use_sahi_init = use_sahi

        # 初始化 SAHI
        if use_sahi and SAHI_AVAILABLE:
            self._init_sahi()

        self.tracker = sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, frame_rate=30)
        self.estimator = SpeedEstimator()

        self.line_zone = None
        self.line_annotator = sv.LineZoneAnnotator(
            thickness=4, text_thickness=2, text_scale=1.0, color=sv.Color.from_hex("#FF0000")
        )

        # 🟢 [核心修复] 恢复手动调色板，确保每一类都有颜色！
        # 如果不加这个，Supervision 可能不知道该用什么颜色画框，导致“隐形”
        colors = [
            sv.Color.from_hex("#00FFFF"),  # 0: awning-tricycle
            sv.Color.from_hex("#FF9F43"),  # 1: bicycle
            sv.Color.from_hex("#9B59B6"),  # 2: bus
            sv.Color.from_hex("#FFD700"),  # 3: car
            sv.Color.from_hex("#341f97"),  # 4: motor
            sv.Color.from_hex("#FF6B6B"),  # 5: pedestrian
            sv.Color.from_hex("#fd79a8"),  # 6: people
            sv.Color.from_hex("#55E6C1"),  # 7: tricycle
            sv.Color.from_hex("#3498DB"),  # 8: truck
            sv.Color.from_hex("#2ECC71"),  # 9: van
        ]
        self.fixed_palette = sv.ColorPalette(colors)

        # 🟢 [核心修复] 强制绑定调色板
        self.box_annotator = sv.BoxAnnotator(thickness=2, color=self.fixed_palette)
        self.label_annotator = sv.LabelAnnotator(
            text_scale=0.8, text_padding=5,
            text_color=sv.Color.WHITE, color=self.fixed_palette
        )
        self.trace_annotator = sv.TraceAnnotator(
            trace_length=30, thickness=2, color=self.fixed_palette
        )

        self.cap = None
        if rtsp_url is not None:
            self.cap = cv2.VideoCapture(rtsp_url)

    def _init_sahi(self):
        try:
            print("🚀 初始化 GPU 加速 SAHI 引擎...")
            self.sahi_agent = SahiWrapper(self.model)
            print("✅ GPU SAHI 就绪")
        except Exception as e:
            print(f"❌ SAHI 初始化失败: {e}")

    def process_frame(self, img=None, use_sahi_override=False, speed_limit=60):
        if img is None:
            if self.cap is None: return None, {}
            ret, frame = self.cap.read()
            if not ret: return None, {}
        else:
            frame = img

        if self.line_zone is None:
            h, w = frame.shape[:2]
            line_y = int(h * 0.35)
            self.line_zone = sv.LineZone(start=sv.Point(50, line_y), end=sv.Point(w - 50, line_y))

        # 1. 动态加载
        if use_sahi_override and SAHI_AVAILABLE and self.sahi_agent is None:
            self._init_sahi()

        detections = None

        # 2. 推理逻辑
        if use_sahi_override and self.sahi_agent:
            try:
                # GPU SAHI 推理
                detections = self.sahi_agent.infer(frame, conf_thres=0.35, slice_height=960, slice_width=960)
            except Exception as e:
                print(f"❌ GPU SAHI 出错: {e}")
                results = self.model(frame, verbose=False, conf=0.25)[0]
                detections = sv.Detections.from_ultralytics(results)
        else:
            # 普通 YOLO 推理
            results = self.model(frame, verbose=False, conf=0.25)[0]
            detections = sv.Detections.from_ultralytics(results)
            # 🟢 [调试] 打印检测到的数量，确认 YOLO 是否工作
            # if len(detections) > 0: print(f"YOLO Detected: {len(detections)}")

        # 3. 追踪
        detections = self.tracker.update_with_detections(detections)

        # 4. 过滤机动车 (用于计数线)
        vehicle_ids = [0, 2, 3, 4, 7, 8, 9]
        mask = np.isin(detections.class_id, vehicle_ids)
        self.line_zone.trigger(detections=detections[mask])

        # 5. 数据统计
        info_data = {
            'in_count': self.line_zone.in_count,
            'out_count': self.line_zone.out_count,
            'current_people': len(detections),
            'alerts': []
        }

        labels = []
        names = self.model.names

        for xyxy, mask, confidence, class_id, tracker_id, data in detections:
            # 兼容性获取类别名
            if isinstance(names, dict):
                class_name = names.get(class_id, f"ID-{class_id}")
            else:
                class_name = names[int(class_id)] if int(class_id) < len(names) else "Unknown"

            speed = 0
            if class_id in [2, 3, 4, 8, 9] and tracker_id is not None:
                center_x = (xyxy[0] + xyxy[2]) / 2
                center_y = (xyxy[1] + xyxy[3]) / 2
                speed = self.estimator.estimate_speed(tracker_id, (center_x, center_y))

            label_text = f"#{tracker_id} {class_name}"
            if speed > 0:
                label_text += f" {int(speed)}km/h"
                if speed > speed_limit:
                    info_data['alerts'].append(f"#{tracker_id} 超速: {int(speed)}km/h")
                    label_text += " [⚡]"
            labels.append(label_text)

        # 6. 绘图
        # 如果 labels 长度匹配，Annotator 就会工作
        if len(detections) > 0:
            frame = self.trace_annotator.annotate(scene=frame, detections=detections)
            frame = self.box_annotator.annotate(scene=frame, detections=detections)
            frame = self.label_annotator.annotate(scene=frame, detections=detections, labels=labels)

        self.line_annotator.annotate(frame=frame, line_counter=self.line_zone)

        return frame, info_data