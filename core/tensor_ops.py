# core/tensor_ops.py
import torch
import torchvision


class TensorSlicer:
    """
    GPU 加速切片器：利用 PyTorch 的 unfold 操作瞬间完成切图
    """

    def __init__(self, slice_height=640, slice_width=640, overlap_ratio=0.2):
        self.h = slice_height
        self.w = slice_width
        self.overlap = overlap_ratio
        self.stride_h = int(self.h * (1 - self.overlap))
        self.stride_w = int(self.w * (1 - self.overlap))

    def slice_batch(self, image_tensor):
        """
        输入: (C, H, W) 归一化后的 Tensor，在 GPU 上
        输出: (Batch_Size, C, h, w) 切片后的 Batch，以及每个切片的偏移量坐标
        """
        # 补全 padding，确保能整除
        _, img_h, img_w = image_tensor.shape

        # 计算需要的 padding
        pad_h = (self.h - (img_h % self.stride_h)) % self.stride_h
        pad_w = (self.w - (img_w % self.stride_w)) % self.stride_w

        # 如果图片不够大，强制 pad 到切片大小
        if img_h < self.h: pad_h = self.h - img_h
        if img_w < self.w: pad_w = self.w - img_w

        # 应用 padding (左, 右, 上, 下)
        # 注意: pad 接收的是 W 方向和 H 方向
        padded_img = torch.nn.functional.pad(image_tensor, (0, pad_w, 0, pad_h), value=0)

        # Unfold 操作 (核心加速点)
        # 维度变化: (C, H, W) -> (C, grid_h, grid_w, slice_h, slice_w)
        patches = padded_img.unfold(1, self.h, self.stride_h).unfold(2, self.w, self.stride_w)

        c, grid_h, grid_w, sh, sw = patches.shape

        # 变形成 Batch: (grid_h * grid_w, C, sh, sw)
        batch_patches = patches.contiguous().view(c, -1, sh, sw).permute(1, 0, 2, 3)

        # 计算每个 patch 的左上角坐标偏移量 (用于后续还原坐标)
        offsets = []
        for i in range(grid_h):
            for j in range(grid_w):
                offsets.append([j * self.stride_w, i * self.stride_h])

        return batch_patches, torch.tensor(offsets, device=image_tensor.device)


def run_nms(boxes, scores, class_ids, iou_thres=0.4):
    """
    使用 torchvision 的 CUDA NMS 进行结果去重
    """
    if boxes.numel() == 0:
        return boxes, scores, class_ids

    # 执行 NMS
    keep_indices = torchvision.ops.nms(boxes, scores, iou_thres)

    return boxes[keep_indices], scores[keep_indices], class_ids[keep_indices]
