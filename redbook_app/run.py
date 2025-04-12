import os
import sys
import webbrowser
import threading
import time
import http.server
import socketserver

def start_api_server():
    print("启动API服务器...")
    os.system("python3 api.py")

def start_frontend_server():
    print("启动前端服务器...")
    os.chdir("frontend")
    
    # 创建一个简单的HTTP服务器
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"前端服务器运行在 http://localhost:{PORT}")
        httpd.serve_forever()

def open_browser():
    # 等待服务器启动
    time.sleep(2)
    print("在浏览器中打开应用...")
    webbrowser.open("http://localhost:8080")

if __name__ == "__main__":
    # 创建前端目录（如果不存在）
    os.makedirs("frontend", exist_ok=True)
    
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