import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "model_path": "weights/yolov8m_cbam.pt",
    "rtsp_url": "data/test_video1.mp4",
    "use_sahi": False,          # 切片检测开关
    "conf_threshold": 0.25,
    "alarm_threshold": 20,      # 拥堵阈值 (辆)
    "speed_limit": 60,          # 🔴 [新增] 超速阈值 (km/h)
    "enable_audio": True,
    "auto_record": False
}

class SystemConfig:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except: pass

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except: pass

    def get(self, key, default=None):
        return self.config.get(key, DEFAULT_CONFIG.get(key, default))

    def set(self, key, value):
        self.config[key] = value
        self.save()

sys_config = SystemConfig()