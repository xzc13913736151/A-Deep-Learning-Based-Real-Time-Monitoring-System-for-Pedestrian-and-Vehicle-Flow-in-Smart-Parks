import json
import os

# 定义配置文件的保存名称
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

# 默认配置 (如果用户第一次运行，或者把配置文件删了，就用这个)
DEFAULT_CONFIG = {
    # 模型路径 (自动指向你改名后的文件)
    "model_path": "weights/yolov8m_cbam.pt",

    # 视频源: "0" 代表本地摄像头，或者填 "data/test_video1.mp4"
    "rtsp_url": "data/test_video1.mp4",

    # 算法参数
    "use_sahi": False,  # 是否开启 SAHI 切片推理
    "conf_threshold": 0.25,  # 置信度阈值
    "alarm_threshold": 20,  # 拥挤报警阈值 (超过20人报警)

    # 系统设置
    "enable_audio": True,  # 是否开启声音报警
    "auto_record": False  # 是否开启自动录像
}


class SystemConfig:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()  # 初始化时尝试读取本地文件

    def load(self):
        """从 JSON 文件加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    # 更新默认配置 (防止版本更新后缺少新字段)
                    self.config.update(saved_config)
                    print(f"✅ 系统配置已加载: {CONFIG_FILE}")
            except Exception as e:
                print(f"⚠️ 配置文件读取失败，使用默认值: {e}")
        else:
            print("ℹ️ 未找到配置文件，将使用默认设置")

    def save(self):
        """保存当前配置到 JSON 文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            print("💾 配置已保存")
        except Exception as e:
            print(f"❌ 保存配置失败: {e}")

    # --- 便捷的 Get/Set 方法 ---
    def get(self, key):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key, value):
        self.config[key] = value
        # 每次设置完自动保存，防止程序崩溃丢失
        self.save()


# 创建一个全局单例，方便其他文件直接 import config 使用
sys_config = SystemConfig()

# 测试代码
if __name__ == "__main__":
    print("当前 RTSP 地址:", sys_config.get("rtsp_url"))
    sys_config.set("alarm_threshold", 50)
    print("修改后的阈值:", sys_config.get("alarm_threshold"))