from app import app

if __name__ == '__main__':
    from waitress import serve
    serve(
        app, 
        host='0.0.0.0', 
        port=8080,
        threads=100,  # 线程数
        connection_limit=1000  # 连接限制
    )