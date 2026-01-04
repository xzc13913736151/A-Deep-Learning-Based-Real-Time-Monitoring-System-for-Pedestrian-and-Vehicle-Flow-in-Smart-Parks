import torch
import numpy as np
from core.tensor_ops import TensorSlicer


class SahiWrapper:
    """
    SAHI (Slicing Aided Hyper Inference) 真正实现版
    """

    def __init__(self, model, slice_size=640, overlap_ratio=0.25):
        self.model = model
        self.slice_size = slice_size
        # 初始化之前的 tensor_ops 切片工具
        self.slicer = TensorSlicer(slice_size, overlap_ratio)

    def infer(self, frame, conf_thres=0.25):
        """
        输入: 原始大图 (numpy array)
        输出: 类似 YOLO 的 results 对象 (包含坐标映射后的框)
        """
        # 1. 预处理：转为 Tensor (B, C, H, W) 并归一化
        # 假设输入是 BGR (Opencv默认)，YOLOv8 内部会自动处理颜色，我们只需要转结构
        img_tensor = torch.from_numpy(frame).permute(2, 0, 1).float()
        if torch.cuda.is_available():
            img_tensor = img_tensor.cuda()
        img_tensor = img_tensor.unsqueeze(0)  # 加 batch 维度

        # 2. 切片：利用 tensor_ops 得到一堆小图
        # patches shape: (N, 3, 640, 640)
        patches = self.slicer.slice_batch(img_tensor)

        # 3. 批量推理：一次性喂给 YOLO
        # 注意：YOLOv8 可以直接吃 Tensor
        results_list = self.model(patches, verbose=False, conf=conf_thres)

        # 4. 坐标还原 (Coordinate Mapping)
        # 我们需要把每个小图里的框，加上小图在原图上的偏移量(offset)
        final_boxes = []
        final_confs = []
        final_cls = []

        # 计算切片的网格分布 (行数, 列数)
        # 这里为了简化，我们需要反推 tensor_ops 是怎么切的
        # stride 是步长
        stride = self.slicer.stride
        _, _, h, w = img_tensor.shape
        n_rows = (h - self.slice_size) // stride + 1
        n_cols = (w - self.slice_size) // stride + 1

        for i, res in enumerate(results_list):
            # 计算当前小图在原图的左上角坐标 (offset_x, offset_y)
            row_idx = i // n_cols
            col_idx = i % n_cols
            offset_y = row_idx * stride
            offset_x = col_idx * stride

            # 获取当前小图检测到的框
            boxes = res.boxes
            if len(boxes) == 0:
                continue

            # 还原坐标：x_new = x_old + offset_x
            # xyxy 格式: x1, y1, x2, y2
            cloned_boxes = boxes.xyxy.clone()
            cloned_boxes[:, 0] += offset_x
            cloned_boxes[:, 1] += offset_y
            cloned_boxes[:, 2] += offset_x
            cloned_boxes[:, 3] += offset_y

            final_boxes.append(cloned_boxes)
            final_confs.append(boxes.conf)
            final_cls.append(boxes.cls)

        # 5. 如果没有检测到任何东西
        if not final_boxes:
            # 返回一个空的 result 结构 (借用第一张小图的结构清空内容)
            empty_res = results_list[0]
            empty_res.boxes = empty_res.boxes[0:0]  # 清空
            return [empty_res]

        # 6. 合并所有结果
        all_boxes = torch.cat(final_boxes)
        all_confs = torch.cat(final_confs)
        all_cls = torch.cat(final_cls)

        # 7. NMS (非极大值抑制) - 去除切片边缘重复的框
        # 使用 torchvision 的 nms 或者 ultralytics 自带的
        from torchvision.ops import nms
        keep_indices = nms(all_boxes, all_confs, iou_threshold=0.5)

        # 8. 重新封装成 YOLO 的 Results 对象 (为了兼容 detector.py 后面的代码)
        # 这是一个脏活，但必须做，为了让 detector 以为这是普通推理出来的
        merged_res = results_list[0]  # 借壳
        # 手动构造 Boxes 对象 (需要 hack 一下内部结构，或者直接替换 data)
        # 为了简单，我们只返回最关键的数据供 detector 使用
        # detector 后面是用 sv.Detections.from_ultralytics(results)
        # 所以我们这里其实可以稍微偷懒，构造一个伪对象，只要 detector 能读就行

        # 修正：直接修改 merged_res 的 boxes 属性最稳妥
        # 这是一个 hacky 的方法，但在工程上有效
        from ultralytics.engine.results import Boxes

        # 构造 (N, 6) 的张量: [x1, y1, x2, y2, conf, cls]
        merged_data = torch.cat([
            all_boxes[keep_indices],
            all_confs[keep_indices].unsqueeze(1),
            all_cls[keep_indices].unsqueeze(1)
        ], dim=1)

        merged_res.boxes = Boxes(merged_data, merged_res.orig_shape)

        return [merged_res]