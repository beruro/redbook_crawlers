import os
import sys
import webbrowser
import threading
import time
import http.server
import socketserver

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def start_api_server():
    print("启动API服务器...")
    # 切换到脚本目录
    os.chdir(SCRIPT_DIR)
    os.system("python api.py")

def start_frontend_server():
    print("启动前端服务器...")
    # 切换到前端目录
    frontend_dir = os.path.join(SCRIPT_DIR, "frontend")
    os.chdir(frontend_dir)
    
    # 创建一个简单的HTTP服务器
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"前端服务器运行在 http://localhost:{PORT}")
        httpd.serve_forever()

def open_browser():
    # 在Docker环境中不打开浏览器
    if os.environ.get('DOCKER_ENV') != 'true':
        time.sleep(2)
        print("在浏览器中打开应用...")
        webbrowser.open("http://localhost:8080")

if __name__ == "__main__":
    # 创建前端目录（如果不存在）
    os.makedirs(os.path.join(SCRIPT_DIR, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "results"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "templates"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "static"), exist_ok=True)
    
    # 设置Docker环境变量
    os.environ['DOCKER_ENV'] = 'true'
    
    # 启动API服务器（在新线程中）
    api_thread = threading.Thread(target=start_api_server)
    api_thread.daemon = True
    api_thread.start()
    
    # 启动前端服务器（在新线程中）
    frontend_thread = threading.Thread(target=start_frontend_server)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    # 在浏览器中打开应用
    open_browser()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("应用已停止")
        sys.exit(0) 