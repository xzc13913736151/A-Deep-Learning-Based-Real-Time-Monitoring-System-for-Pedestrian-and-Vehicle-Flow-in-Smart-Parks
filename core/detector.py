# detector.py
# 负责核心视觉算法：检测、追踪、热力图、计数

import cv2
from ultralytics import YOLO
import supervision as sv
import numpy as np


class SmartDetector:
    def __init__(self, model_path='weights/yolov8n.pt'):
        # 1. 加载模型
        print(f"正在加载模型: {model_path} ...")
        self.model = YOLO(model_path)

        # 2. 初始化各种 "画笔" (Annotators)
        # 基础框画笔
        self.box_annotator = sv.BoxAnnotator(
            thickness=2
        )
        # 标签画笔 (显示 ID 和 类别)
        self.label_annotator = sv.LabelAnnotator(
            text_scale=0.5,
            text_thickness=1,
            text_position=sv.Position.TOP_CENTER
        )
        # 轨迹画笔 (显示目标走过的路径) -> 看起来非常高级
        self.trace_annotator = sv.TraceAnnotator(
            thickness=2,
            trace_length=50  # 轨迹保留长度
        )
        # 热力图画笔 (显示拥挤区域) -> 满分特效
        self.heatmap_annotator = sv.HeatMapAnnotator(
            position=sv.Position.BOTTOM_CENTER,
            opacity=0.5,
            radius=25,
            kernel_size=25
        )

        # 计数器相关 (先设为 None，等读到第一帧视频再初始化)
        self.line_zone = None
        self.line_zone_annotator = sv.LineZoneAnnotator(
            thickness=2,
            text_thickness=2,
            text_scale=0.8
        )

        # 状态标记
        self.is_initialized = False

    def process_frame(self, frame):
        """
        输入原始图片，输出：处理后的图片，当前的统计数据
        """
        # --- 1. 动态初始化 (只在第一帧执行一次) ---
        # 这样你的程序就能适应任何分辨率的视频，不用手动改坐标了
        if not self.is_initialized:
            h, w = frame.shape[:2]
            # 设定线的位置：在画面中间 (0, h/2) -> (w, h/2)
            start_point = sv.Point(0, int(h * 0.5))
            end_point = sv.Point(w, int(h * 0.5))

            self.line_zone = sv.LineZone(start=start_point, end=end_point)
            self.is_initialized = True
            print(f"✅ 计数线已自动校准: {w}x{h}")

        # --- 2. YOLO 检测 + 追踪 ---
        # conf=0.25: 只有置信度大于 0.25 的才算
        # classes=[0, 2]: 只检测 人(0) 和 车(2) (根据 VisDrone 或 COCO ID 调整)
        # 注意：如果你用了微调后的模型，VisDrone 的类别 ID 可能会变，
        # 如果训练时没改 yaml，通常 0 是 pedestrian, 1 是 people, 3 是 car 等。
        # 这里暂时用通用的 [0, 1, 2, 3] 比较保险
        results = self.model.track(frame, persist=True, verbose=False, conf=0.25)

        # --- 3. 数据转换 ---
        detections = sv.Detections.from_ultralytics(results[0])

        # 只有当有 ID 时 (追踪成功) 才进行后续逻辑
        if results[0].boxes.id is not None:
            detections.tracker_id = results[0].boxes.id.cpu().numpy().astype(int)

            # --- 4. 逻辑判断 ---
            # 触发越线计数
            self.line_zone.trigger(detections=detections)

        # --- 5. 画面绘制 (像 PS 图层一样一层层叠加) ---

        # Layer 1: 热力图 (最底层)
        frame = self.heatmap_annotator.annotate(scene=frame, detections=detections)

        # Layer 2: 轨迹线 (显示运动路径)
        frame = self.trace_annotator.annotate(scene=frame, detections=detections)

        # Layer 3: 目标框
        frame = self.box_annotator.annotate(scene=frame, detections=detections)

        # Layer 4: 标签 (ID + Class)
        # 动态生成标签文字，例如: "#42 Person"
        labels = [
            f"#{tracker_id} {results[0].names[class_id]}"
            for tracker_id, class_id
            in zip(detections.tracker_id, detections.class_id)
        ] if detections.tracker_id is not None else []

        frame = self.label_annotator.annotate(
            scene=frame,
            detections=detections,
            labels=labels
        )

        # Layer 5: 计数线 (最上层)
        frame = self.line_zone_annotator.annotate(frame, line_counter=self.line_zone)

        # --- 6. 整理统计数据返回给界面 ---
        stats = {
            "in_count": self.line_zone.in_count,
            "out_count": self.line_zone.out_count,
            "current_people": len(detections)
        }

        return frame, stats
