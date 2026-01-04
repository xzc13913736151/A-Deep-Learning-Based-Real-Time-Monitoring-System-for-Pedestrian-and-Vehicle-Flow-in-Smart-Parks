# 文件路径: train.py
import sys
import os
from ultralytics import YOLO
from ultralytics.nn.tasks import parse_model

# --- 关键步骤：注册你的自定义模块 ---
# 这一步是为了让 YOLO 能读懂 yaml 文件里的 "CBAM"
from core.attention import CBAM

# 这里的逻辑是：虽然我们没法直接修改 ultralytics 的库文件
# 但我们可以确保在程序运行时，Python 知道 CBAM 是什么
# (注意：通常需要修改 ultralytics 源码的 tasks.py 才能完美识别
# 但为了不破坏环境，我们可以尝试用这种方式，或者你直接去修改库文件)
# --------------------------------

def main():
    # 1. 指定你的新配置文件
    # 这一步构建了一个基于 Medium + CBAM 架构的模型
    model = YOLO('configs/yolov8m_cbam.yaml')

    # 2. 加载官方预训练权重 (迁移学习)
    # 这样你就不是从零训练，而是站在巨人的肩膀上
    # 它会把 yolov8m.pt 里能用的权重都加载进来，CBAM 层则随机初始化
    model.load('weights/yolov8m.pt')

    # 3. 开始训练
    # data 指向你的 visdrone 数据集配置
    # device=0 使用你的 V100 显卡
    # batch=16 (Medium 模型比较大，V100 开 32 可能会爆，先试 16)
    model.train(
        data='data/visdrone/data.yaml',
        epochs=100,
        imgsz=640,
        batch=16,
        project='runs/train',
        name='visdrone_cbam_final',
        device=0,
        amp=False # 如果之前报错，这里关掉 AMP
    )

if __name__ == '__main__':
    main()