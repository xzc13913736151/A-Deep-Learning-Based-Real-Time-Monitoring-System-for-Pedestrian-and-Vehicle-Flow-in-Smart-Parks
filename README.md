# 🎓 Smart Campus Pro - 基于深度学习的智能园区监控系统

## 📖 项目介绍
本项目是一个基于 **YOLOv8-CBAM** 改进模型与 **PyQt5** 的智能园区人流车流实时监控系统。
系统集成了 **ByteTrack** 追踪算法、**SAHI** 小目标切片推理技术，以及自定义的车辆测速模块。

## ✨ 核心功能 (Core Features)
* **🎯 高精度检测**: 引入 CBAM 注意力机制改进 YOLOv8，显著提升 VisDrone 数据集上的小目标检测率。
* **🔪 SAHI 切片推理**: 支持超高分辨率（4K）下的微小目标检测（可配置开关）。
* **🏎️ 车辆测速**: 基于透视变换（Perspective Transformation）的单目视觉测速。
* **📊 实时数据大屏**: 包含进出流量统计、拥挤度分析、全类别图例显示。
* **📼 历史回放**: 支持异常事件录像与回放。

## 🛠️ 环境安装
1. pip install -r requirements.txt安装环境
2. 下载数据集:https://universe.roboflow.com/uogolanrewaju/visdrone2019-det/dataset/4/download/yolov8
3. 进入miniconda3/envs/monitor/lib/python3.9/site-packages/ultralytics/nn/modules/conv.py(如果使用conda环境)
4.把这段加到 conv.py 的最后面


    class ChannelAttention(nn.Module):
    def __init__(self, in_planes, ratio=16):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.fc = nn.Sequential(
            nn.Conv2d(in_planes, in_planes // ratio, 1, bias=False),
            nn.ReLU(),
            nn.Conv2d(in_planes // ratio, in_planes, 1, bias=False)
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = self.fc(self.avg_pool(x))
        max_out = self.fc(self.max_pool(x))
        out = avg_out + max_out
        return self.sigmoid(out)


    class SpatialAttention(nn.Module):
        def __init__(self, kernel_size=7):
            super(SpatialAttention, self).__init__()
            assert kernel_size in (3, 7), 'kernel size must be 3 or 7'
            padding = 3 if kernel_size == 7 else 1
            self.conv1 = nn.Conv2d(2, 1, kernel_size, padding=padding, bias=False)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            avg_out = torch.mean(x, dim=1, keepdim=True)
            max_out, _ = torch.max(x, dim=1, keepdim=True)
            x_cat = torch.cat([avg_out, max_out], dim=1)
            out = self.conv1(x_cat)
            return self.sigmoid(out)

    class CBAM(nn.Module):
        def __init__(self, c1, kernel_size=7):
            super(CBAM, self).__init__()
            self.channel_attention = ChannelAttention(c1)
            self.spatial_attention = SpatialAttention(kernel_size)

    def forward(self, x):
        out = self.channel_attention(x) * x
        out = self.spatial_attention(out) * out
        return out
5. 进入miniconda3/envs/monitor/lib/python3.9/site-packages/ultralytics/nn/tasks.py
6. 在最顶部加上from ultralytics.nn.modules.conv import Conv, LightConv, RepConv, DWConv, CBAM  # <--- 加在这里
7. python train.py运行主程序
8. 运行训练脚本python train.py（可选）
## 🛠️ 项目结构
SmartCampus_Pro/
│
├── configs/               # [配置层] 存放系统参数
│   ├── __init__.py        # ⚠️必须有 (空文件即可)
│   └── system_config.py   # 系统运行时的配置文件 (存RTSP地址、报警阈值等)
│
├── core/                  # [算法层] 核心逻辑
│   ├── __init__.py        # ⚠️必须有
│   ├── detector.py        # 负责调用YOLO、绘图、计数逻辑
│   ├── speed_estimator.py # 负责速度计算 (透视变换)
│   ├── attention.py       # 修改YOLO架构，添加手写注意力层
│   ├── tensor_ops.py      # 手写张量运算
│   └── sahi_inference.py  # 负责 SAHI 切片推理
│
├── ui/                    # [界面层] PyQt5 窗口代码
│   ├── __init__.py        # ⚠️必须有
│   ├── login_window.py    # 登录窗口
│   ├── main_window.py     # 主框架 (侧边栏+堆叠布局)
│   ├── monitor_grid.py    # 核心监控页面 (视频+图例+统计)
│   ├── history_window.py  # 历史回放页面
│   └── settings_window.py # 设置页面
│
├── data/                  # [数据层] 资源文件
│   ├── visdrone/          # 数据集目录 (Roboflow下载的或解压的)
│   │   ├── train/
│   │   ├── valid/
│   │   ├── test/
│   │   └── data.yaml      # ⚠️训练用的数据集配置文件
│   │
│   └── test_video1.mp4    # 测试用的视频 (GitHub上传时会被忽略)
│
├── weights/               # [模型层] 存放训练好的权重
│   └── yolov8m_cbam.pt    # 最佳模型 (从 runs/ 复制出来的)
│
├── runs/                  # [日志层] 训练产生的日志 (会被 .gitignore 忽略)
│
├── main.py                # 🚀 程序启动入口
├── train.py               # 🏋️ 训练脚本
├── requirements.txt       # 依赖列表
├── .gitignore             # Git 忽略规则
└── README.md              # 项目说明书