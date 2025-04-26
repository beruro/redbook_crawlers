import os
import sys
import time

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def start_api_server():
    print("启动API服务器...")
    # 切换到脚本目录
    os.chdir(SCRIPT_DIR)
    
    # 导入FastAPI应用并运行
    from api import app
    import uvicorn
    
    # 获取PORT环境变量（Railway会自动设置）
    port = int(os.environ.get("PORT", 8008))
    
    print(f"API服务器将在端口 {port} 上启动")
    
    # 启动FastAPI应用
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs(os.path.join(SCRIPT_DIR, "frontend"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "results"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "templates"), exist_ok=True)
    os.makedirs(os.path.join(SCRIPT_DIR, "static"), exist_ok=True)
    
    # 设置环境变量
    os.environ["DOCKER_ENV"] = "true"
    
    # 添加防止Heroku/Railway自动休眠的设置
    if os.environ.get("PREVENT_SLEEP") == "true":
        print("已启用防止自动休眠功能")
    
    # 在Railway上，我们只需要启动API服务器
    start_api_server() 