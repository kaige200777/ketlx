from app import init_db, app
from waitress import serve
import os

if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 启动Waitress服务器
    # 绑定到0.0.0.0:8000
    print("Starting server on http://0.0.0.0:8000")
    serve(app, host='0.0.0.0', port=8000) 