def check_dependencies():
    """检查所需的依赖是否已安装"""
    missing_deps = []
    
    try:
        import fastapi
        print(f"FastAPI 版本: {fastapi.__version__}")
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import jinja2
        print(f"Jinja2 版本: {jinja2.__version__}")
    except ImportError:
        missing_deps.append("jinja2")
    
    try:
        import uvicorn
        print(f"Uvicorn 版本: {uvicorn.__version__}")
    except ImportError:
        missing_deps.append("uvicorn")
    
    try:
        from fastapi.templating import Jinja2Templates
        print("FastAPI templating 模块可用")
    except ImportError:
        missing_deps.append("fastapi.templating")
    
    if missing_deps:
        print(f"缺少以下依赖: {', '.join(missing_deps)}")
        print("请运行: pip install -r requirements.txt")
    else:
        print("所有依赖已正确安装")

if __name__ == "__main__":
    check_dependencies() 