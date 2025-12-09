from app import init_db, app
from waitress import serve
import os

# 从环境变量或配置文件读取端口
try:
    from config import HOST, PORT
except ImportError:
    HOST = os.environ.get('APP_HOST', '0.0.0.0')
    PORT = int(os.environ.get('APP_PORT', 8000))

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 启动Waitress服务器
    print(f"Starting server on http://{HOST}:{PORT}")
    print(f"访问地址: http://localhost:{PORT}")
    print("按 Ctrl+C 停止服务器")
    serve(app, host=HOST, port=PORT) 