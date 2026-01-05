import sqlite3
import threading
import hashlib
import os
from datetime import datetime
from typing import List, Tuple, Optional
# 引入刚才定义的模型
from database.models import User, Event

class DBManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = "smart_campus.db"):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance.db_path = db_path
                    cls._instance._init_db()
        return cls._instance

    def _get_conn(self):
        """获取数据库连接 (check_same_thread=False 允许跨线程使用)"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """初始化数据库表结构"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                camera_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                snapshot_path TEXT,
                video_path TEXT,
                description TEXT
            )
        ''')
        
        # 初始化默认管理员
        cursor.execute("SELECT count(*) FROM users")
        if cursor.fetchone()[0] == 0:
            self._create_admin(cursor)
            
        conn.commit()
        conn.close()

    def _create_admin(self, cursor):
        """创建默认管理员账号"""
        pwd_hash = self._hash_password("admin123")
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", pwd_hash, "admin")
        )
        print("[DB] Default admin created.")

    def _hash_password(self, password: str) -> str:
        """密码加盐哈希"""
        salt = "nankai_project_salt"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    # --- 用户相关功能 ---

    def login(self, username, password) -> Tuple[bool, str]:
        """验证登录，返回 (是否成功, 角色)"""
        conn = self._get_conn()
        cursor = conn.cursor()
        pwd_hash = self._hash_password(password)
        
        cursor.execute(
            "SELECT role FROM users WHERE username=? AND password_hash=?", 
            (username, pwd_hash)
        )
        res = cursor.fetchone()
        conn.close()
        
        if res:
            return True, res[0]
        return False, ""

    def add_user(self, username, password, role="user") -> bool:
        """注册新用户"""
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            pwd_hash = self._hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, pwd_hash, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    # --- 事件相关功能 ---

    def insert_event(self, event: Event) -> int:
        """插入一条报警记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if not event.timestamp:
            event.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO events (event_type, camera_id, timestamp, description, snapshot_path, video_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (event.event_type, event.camera_id, event.timestamp, event.description, event.snapshot_path, event.video_path))
        
        new_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return new_id

    def get_all_events(self) -> List[Event]:
        """获取所有历史记录"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        events = []
        for row in rows:
            events.append(Event(
                id=row['id'],
                event_type=row['event_type'],
                camera_id=row['camera_id'],
                timestamp=row['timestamp'],
                description=row['description'],
                snapshot_path=row['snapshot_path'],
                video_path=row['video_path']
            ))
        conn.close()
        return events

    def delete_event(self, video_path):
        """根据视频路径删除数据库中的记录"""
        # 🟢 [关键] 使用你类里定义好的 _get_conn() 方法获取连接
        conn = self._get_conn()

        try:
            cursor = conn.cursor()
            # 根据唯一的文件路径来定位并删除
            cursor.execute("DELETE FROM events WHERE video_path = ?", (video_path,))
            conn.commit()

            # cursor.rowcount 表示受影响的行数
            if cursor.rowcount > 0:
                print(f"🗑️ 数据库记录已删除: {video_path}")
                return True
            else:
                print(f"⚠️ 数据库中未找到该路径，无法删除: {video_path}")
                return True  # 虽然没找到，但结果也是“没了”，算成功处理

        except Exception as e:
            print(f"❌ 删除数据库记录失败: {e}")
            return False
        finally:
            # 🟢 [关键] 必须关闭连接，释放资源
            conn.close()
