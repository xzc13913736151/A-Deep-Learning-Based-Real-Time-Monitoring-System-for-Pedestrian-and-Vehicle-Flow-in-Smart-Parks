from dataclasses import dataclass
from datetime import datetime

@dataclass
class User:
    """用户数据模型"""
    id: int
    username: str
    role: str  # 'admin' or 'user'
    created_at: str

@dataclass
class Event:
    """报警事件数据模型"""
    id: int = None
    event_type: str = ""      # 例如 "Fall", "Intrusion"
    camera_id: str = ""       # 摄像头 IP 或 ID
    timestamp: str = ""       # 发生时间
    description: str = ""     # 详细描述
    snapshot_path: str = ""   # 截图路径
    video_path: str = ""      # 录像路径

    def to_dict(self):
        """转为字典格式，方便导出 Excel"""
        return {
            "ID": self.id,
            "类型": self.event_type,
            "摄像头": self.camera_id,
            "时间": self.timestamp,
            "描述": self.description,
            "截图": self.snapshot_path,
            "录像": self.video_path
        }
