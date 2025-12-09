"""
应用配置文件
"""
import os

# 服务器配置
HOST = os.environ.get('APP_HOST', '0.0.0.0')
PORT = int(os.environ.get('APP_PORT', 8000))

# 数据库配置
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///test_system.db')

# 密钥配置（生产环境请使用环境变量设置）
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')

# 调试模式
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 图片上传配置
ALLOWED_IMG_EXT = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
MAX_IMG_SIZE = 2 * 1024 * 1024  # 2MB

# 时区配置
TIMEZONE_OFFSET = 8  # 北京时间 UTC+8
