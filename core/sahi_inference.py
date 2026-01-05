# core/sahi_inference.py
import torch
import numpy as np
import supervision as sv
from core.tensor_ops import TensorSlicer, run_nms
import cv2


class SahiWrapper:
    def __init__(self, yolo_model):
        self.model = yolo_model
        self.device = yolo_model.device
        # 初始化切片器
        self.slicer = TensorSlicer(slice_height=960, slice_width=960, overlap_ratio=0.15)

    def infer(self, frame_img, conf_thres=0.25, slice_height=960, slice_width=960):
        """
        全 GPU 流程：
        1. BGR -> RGB
        2. 图片转 Tensor 上 GPU
        3. GPU 切片
        4. YOLO Batch 推理
        5. 坐标还原 & NMS 合并
        """
        # 1. BGR -> RGB
        frame_rgb = cv2.cvtColor(frame_img, cv2.COLOR_BGR2RGB)

        # 2. 预处理：numpy (H,W,C) -> tensor (C,H,W) -> 归一化
        img_tensor = torch.from_numpy(frame_rgb).to(self.device).float()
        img_tensor = img_tensor.permute(2, 0, 1) / 255.0  # (C,H,W) 0-1

        # 3. 动态更新切片器参数
        if self.slicer.h != slice_height or self.slicer.w != slice_width:
            self.slicer = TensorSlicer(slice_height, slice_width, overlap_ratio=0.15)

        # 4. GPU 切片
        batch_patches, offsets = self.slicer.slice_batch(img_tensor)

        # 5. YOLO 批量推理
        results = self.model(batch_patches, verbose=False, conf=conf_thres)

        # 6. 结果处理与合并
        all_boxes = []
        all_scores = []
        all_classes = []

        for i, res in enumerate(results):
            # 🟢 [关键修复] 必须加上 .clone()！
            # 否则 PyTorch 会报错：Inplace update to inference tensor...
            dets = res.boxes.data.clone()

            if dets.shape[0] > 0:
                # 获取当前切片的偏移量
                off_x, off_y = offsets[i]

                # 还原坐标 (现在是在 clone 的数据上修改，安全了)
                dets[:, 0] += off_x
                dets[:, 2] += off_x
                dets[:, 1] += off_y
                dets[:, 3] += off_y

                all_boxes.append(dets[:, :4])
                all_scores.append(dets[:, 4])
                all_classes.append(dets[:, 5])

        # 如果所有切片都没结果
        if len(all_boxes) == 0:
            return sv.Detections.empty()

        # 7. 拼接
        merged_boxes = torch.cat(all_boxes, dim=0)
        merged_scores = torch.cat(all_scores, dim=0)
        merged_classes = torch.cat(all_classes, dim=0)

        # 8. 全局 NMS
        final_boxes, final_scores, final_classes = run_nms(
            merged_boxes, merged_scores, merged_classes, iou_thres=0.45
        )

        return sv.Detections(
            xyxy=final_boxes.cpu().numpy(),
            confidence=final_scores.cpu().numpy(),
            class_id=final_classes.cpu().int().numpy()
        )