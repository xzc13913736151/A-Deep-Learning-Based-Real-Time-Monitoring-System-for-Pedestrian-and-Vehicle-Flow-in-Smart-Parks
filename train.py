from ultralytics import YOLO

def main():
    # 1. 加载模型
    model = YOLO('weights/yolov8n.pt')

    # 2. 开始训练
    # 注意：第一次跑建议把 epochs 设为 1 或者 3，先看看能不能跑通，不要直接设 50
    print("🚀 开始训练...")
    model.train(
        data='data/visdrone/data.yaml',
        epochs=100,
        imgsz=640,
        batch=32,           # 如果显存爆了(OOM)，把这个数字改小，比如 2
        project='runs/train',
        name='visdrone_test',
        device=0           # 如果没显卡或者是笔记本，改填 'cpu'
    )

if __name__ == '__main__':
    main()