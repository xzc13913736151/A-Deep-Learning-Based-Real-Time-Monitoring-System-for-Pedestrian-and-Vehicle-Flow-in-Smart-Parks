import cv2
import torch
import numpy as np
import supervision as sv
from ultralytics import YOLO
import os

try:
    from core.speed_estimator import SpeedEstimator
except ImportError:
    from core.speed_estimator import SpeedEstimator
from core.sahi_inference import SahiWrapper


class SmartDetector:
    def __init__(self, model_path=None, rtsp_url=None, use_sahi=False):
        # 1. 路径处理
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root_dir = os.path.dirname(current_dir)
            model_path = os.path.join(root_dir, 'weights', 'yolov8m_cbam.pt')

        self.use_sahi = use_sahi
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        try:
            self.model = YOLO(model_path)
        except:
            self.model = YOLO('yolov8n.pt')

        if self.use_sahi:
            self.sahi_agent = SahiWrapper(self.model)

        self.tracker = sv.ByteTrack(track_activation_threshold=0.25, lost_track_buffer=30, frame_rate=30)
        self.estimator = SpeedEstimator()

        # 计数线 (红线)
        self.line_zone = None
        self.line_annotator = sv.LineZoneAnnotator(
            thickness=4,
            text_thickness=2,
            text_scale=1.0,
            color=sv.Color.from_hex("#FF0000")
        )

        # --- [重点修改] 10种类别全家桶调色板 ---
        # 按照你给的 names 顺序:
        # 0: awning-tricycle (带棚三轮) -> 青色
        # 1: bicycle (自行车) -> 橙色
        # 2: bus (公交车) -> 紫色
        # 3: car (轿车) -> 金黄色
        # 4: motor (摩托车) -> 深蓝
        # 5: pedestrian (行人) -> 红色
        # 6: people (人) -> 粉色
        # 7: tricycle (三轮车) -> 浅绿
        # 8: truck (卡车) -> 蓝色
        # 9: van (货车) -> 翡翠绿

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

        # 绑定调色板
        self.box_annotator = sv.BoxAnnotator(
            thickness=2,
            color=self.fixed_palette
        )

        self.label_annotator = sv.LabelAnnotator(
            text_thickness=2,
            text_scale=0.8,
            text_color=sv.Color.WHITE,
            text_padding=5,
            color=self.fixed_palette
        )

        self.trace_annotator = sv.TraceAnnotator(
            trace_length=30,
            thickness=2,
            color=self.fixed_palette
        )

        self.cap = None
        if rtsp_url is not None:
            self.cap = cv2.VideoCapture(rtsp_url)

    def process_frame(self, img=None):
        if img is None:
            if self.cap is None: return None, {}
            ret, frame = self.cap.read()
            if not ret: return None, {}
        else:
            frame = img

        # 动态初始化线
        if self.line_zone is None:
            h, w = frame.shape[:2]
            line_y = int(h * 0.6)
            start_point = sv.Point(50, line_y)
            end_point = sv.Point(w - 50, line_y)
            self.line_zone = sv.LineZone(start=start_point, end=end_point)

        # 推理
        if self.use_sahi:
            results = self.sahi_agent.infer(frame, conf_thres=0.35)[0]
        else:
            results = self.model(frame, verbose=False, conf=0.25)[0]

        detections = sv.Detections.from_ultralytics(results)
        detections = self.tracker.update_with_detections(detections)

        # 跨线检测 (依然只统计机动车，避免行人乱走导致数据很乱)
        # 如果你想统计所有东西，把这里改成 vehicle_ids = [0,1,2,3,4,5,6,7,8,9]
        # 这里我保留只统计机动车 (Car, Bus, Truck, Van, Motor)
        vehicle_ids = [0, 2, 3, 4, 7, 8, 9]
        mask = np.isin(detections.class_id, vehicle_ids)
        vehicle_detections = detections[mask]
        self.line_zone.trigger(detections=vehicle_detections)

        info_data = {
            'in_count': self.line_zone.in_count,
            'out_count': self.line_zone.out_count,
            'current_people': 0,
            'car': 0,
            'alerts': []
        }

        labels = []
        for xyxy, mask, confidence, class_id, tracker_id, data in detections:
            class_name = results.names[class_id]

            # 统计屏幕上的总目标数 (只要是检测到的都算)
            info_data['current_people'] += 1
            if class_name == 'car':
                info_data['car'] += 1

            center_x = (xyxy[0] + xyxy[2]) / 2
            center_y = (xyxy[1] + xyxy[3]) / 2
            speed = 0

            # 只有机动车测速
            if class_id in [2, 3, 4, 8, 9] and tracker_id is not None:
                speed = self.estimator.estimate_speed(tracker_id, (center_x, center_y))

            label_text = f"#{tracker_id} {class_name}"
            if speed > 0:
                label_text += f" {int(speed)}km/h"
                if speed > 60:
                    info_data['alerts'].append(f"#{tracker_id} 超速: {speed}")

            labels.append(label_text)

        # 绘图
        frame = self.trace_annotator.annotate(scene=frame, detections=detections)
        frame = self.box_annotator.annotate(scene=frame, detections=detections)
        frame = self.label_annotator.annotate(scene=frame, detections=detections, labels=labels)
        self.line_annotator.annotate(frame=frame, line_counter=self.line_zone)

        return frame, info_data