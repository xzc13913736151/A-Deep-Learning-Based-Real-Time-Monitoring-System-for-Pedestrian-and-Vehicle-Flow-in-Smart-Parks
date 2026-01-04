# core/tensor_ops.py
import torch


class TensorSlicer:
    """
    基于 PyTorch Tensor 的图像切片器
    作用：利用 GPU 加速将大图切成小块 (用于 SAHI 推理)
    """

    def __init__(self, slice_size=640, overlap_ratio=0.2):
        self.slice_size = slice_size
        self.stride = int(slice_size * (1 - overlap_ratio))

    def slice_batch(self, images):
        """
        输入: Batch图片张量 (B, C, H, W)
        输出: 切好的一堆小图 (N, C, slice_size, slice_size)
        """
        # 假设 images 已经是 (B, C, H, W) 格式的 Tensor
        b, c, h, w = images.shape

        # 使用 unfold 进行滑动窗口切片 (这是 PyTorch 处理图像的高级用法)
        # 1. 垂直方向 unfold
        patches = images.unfold(2, self.slice_size, self.stride)
        # 2. 水平方向 unfold
        patches = patches.unfold(3, self.slice_size, self.stride)

        # 现在的形状是 (B, C, n_rows, n_cols, slice_h, slice_w)
        # 需要把它变成 (N, C, slice_h, slice_w) 以便喂给 YOLO
        patches = patches.contiguous().view(-1, c, self.slice_size, self.slice_size)

        return patches


def torch_iou(box1, box2):
    """
    手写 PyTorch 版的 IoU (Intersection over Union) 计算
    用于后续的 NMS (非极大值抑制) 处理
    box格式: [x1, y1, x2, y2]
    """
    # 计算交集坐标
    inter_x1 = torch.max(box1[:, 0], box2[:, 0])
    inter_y1 = torch.max(box1[:, 1], box2[:, 1])
    inter_x2 = torch.min(box1[:, 2], box2[:, 2])
    inter_y2 = torch.min(box1[:, 3], box2[:, 3])

    # 计算交集面积
    inter_area = (inter_x2 - inter_x1).clamp(min=0) * (inter_y2 - inter_y1).clamp(min=0)

    # 计算并集面积
    area1 = (box1[:, 2] - box1[:, 0]) * (box1[:, 3] - box1[:, 1])
    area2 = (box2[:, 2] - box2[:, 0]) * (box2[:, 3] - box2[:, 1])
    union_area = area1 + area2 - inter_area

    return inter_area / (union_area + 1e-6)