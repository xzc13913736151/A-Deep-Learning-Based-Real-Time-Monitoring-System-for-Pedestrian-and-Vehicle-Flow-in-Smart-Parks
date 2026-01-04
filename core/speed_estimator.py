import cv2
import numpy as np


class SpeedEstimator:
    def __init__(self, src_points=None, real_width=3.5, real_length=10):
        """
        初始化测速模块 (基于透视变换 Homography)
        :param src_points: list, 视频中选取的4个点 [(x,y), ...], 围成一个矩形区域(如一条车道)
        :param real_width: float, 这块区域在现实世界中的宽度 (米), 默认车道宽 3.5米
        :param real_length: float, 这块区域在现实世界中的长度 (米), 默认看清距离 10米
        """
        # 如果没有传入点，提供一组默认的梯形点 (针对一般路口监控视角)
        if src_points is None:
            # 注意：这里的点需要根据你的实际视频画面去微调！
            # 顺序：[左下, 右下, 右上, 左上]
            self.src_points = np.array([
                [200, 700],  # 左下
                [1000, 700],  # 右下
                [850, 400],  # 右上
                [350, 400]  # 左上
            ], dtype=np.float32)
        else:
            self.src_points = np.array(src_points, dtype=np.float32)

        # 目标点：把倾斜的视角映射成一个俯视的矩形 (Top-down view)
        # 这里的像素比例尺不重要，重要的是长宽比要符合现实
        self.dst_points = np.float32([
            [0, 0],
            [100, 0],
            [100, 300],  # 假设长宽比是 1:3
            [0, 300]
        ])

        # 计算单应性矩阵 (Homography Matrix) - 核心数学公式
        # H 矩阵负责把 图像坐标 -> 物理坐标
        self.matrix = cv2.getPerspectiveTransform(self.src_points, self.dst_points)

        # 存储上一帧的位置 {track_id: (real_x, real_y, timestamp)}
        self.previous_positions = {}

        # 比例尺: 像素距离 -> 现实距离 (米)
        # 简单估算：映射后的 300 像素 = real_length (10米)
        self.pixels_per_meter = 300 / real_length

    def transform_point(self, point):
        """
        把屏幕像素坐标 (x,y) 转换成 变换后的鸟瞰图坐标
        """
        # OpenCV 的透视变换需要三维向量
        p = np.array([[[point[0], point[1]]]], dtype=np.float32)
        transformed = cv2.perspectiveTransform(p, self.matrix)
        return transformed[0][0]

    def estimate_speed(self, object_id, center_point, fps=30):
        """
        计算速度的核心函数
        :param object_id: 追踪ID
        :param center_point: 检测框中心点 (x, y)
        :param fps: 视频帧率
        :return: 速度 (km/h)
        """
        # 1. 获取当前时刻的鸟瞰图坐标
        current_map_pos = self.transform_point(center_point)
        current_x, current_y = current_map_pos

        speed = 0

        if object_id in self.previous_positions:
            prev_map_pos = self.previous_positions[object_id]
            prev_x, prev_y = prev_map_pos

            # 2. 计算欧氏距离 (像素单位)
            distance_pixels = np.linalg.norm(current_map_pos - prev_map_pos)

            # 3. 换算成 现实距离 (米)
            distance_meters = distance_pixels / self.pixels_per_meter

            # 4. 速度公式: v = s / t
            # 时间间隔 = 1 / fps
            # 速度 (m/s) = distance * fps
            speed_mps = distance_meters * fps

            # 5. 转换成 km/h
            speed = speed_mps * 3.6

            # 6. 低通滤波 & 异常值剔除
            # 如果速度瞬间超过 200km/h (通常是ID跳变导致的)，归零
            if speed > 200:
                speed = 0

            # 可以加一个平滑逻辑，这里简化处理

        # 更新记录
        self.previous_positions[object_id] = current_map_pos

        return int(speed)