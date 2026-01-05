import logging
import os
from logging.handlers import RotatingFileHandler

class SystemLogger:
    """
    系统日志封装类
    功能：同时输出到控制台和日志文件，支持文件大小自动切割
    """
    def __init__(self, log_file="system.log"):
        self.logger = logging.getLogger("SmartCampus")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # 1. 格式设置
            formatter = logging.Formatter(
                fmt='[%(asctime)s] [%(levelname)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # 2. 文件处理器 (最大 5MB，保留 3 个备份)
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # 3. 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)

    def warning(self, msg):
        self.logger.warning(msg)

# 创建一个全局单例供其他模块直接引用
logger = SystemLogger()
