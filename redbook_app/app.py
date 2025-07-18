from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn
import os
from typing import List
import asyncio
from pydantic import BaseModel
import sys
import json
# 将当前目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import redbook

app = FastAPI(title="小红书达人数据爬取工具")

# 创建templates目录
os.makedirs("templates", exist_ok=True)

# 设置模板
templates = Jinja2Templates(directory="templates")

# 创建用于存储结果的目录
os.makedirs("results", exist_ok=True)

# 创建静态文件目录
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

class ProcessStatus(BaseModel):
    status: str
    message: str
    file_path: str = None

# 全局变量存储处理状态
processing_status = []
result_file_path = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/process")
async def process_data(background_tasks: BackgroundTasks, urls: str = Form(...)):
    global processing_status, result_file_path
    
    # 重置状态
    processing_status = []
    result_file_path = None
    
    # 分割URL
    url_list = urls.strip().split('\n')
    
    # 在后台任务中处理URL
    background_tasks.add_task(process_urls_background, url_list)
    
    return {"message": "处理已开始，请查看状态"}

async def process_urls_background(url_list):
    global processing_status, result_file_path
    
    # 更新状态为开始处理
    processing_status = [{"status": "info", "message": "开始处理URL..."}]
    
    # 处理URL
    data_list, results = redbook.process_urls(url_list)
    
    # 更新处理结果
    processing_status.extend(results)
    
    # 如果有数据，保存到Excel
    if data_list:
        try:
            filename = redbook.save_to_excel(data_list)
            if filename:
                # 移动文件到results目录
                new_path = os.path.join("results", filename)
                os.rename(filename, new_path)
                result_file_path = new_path
                processing_status.append({"status": "success", "message": f"数据已保存到 {filename}"})
            else:
                processing_status.append({"status": "error", "message": "保存Excel文件失败"})
        except Exception as e:
            processing_status.append({"status": "error", "message": f"保存Excel时出错: {str(e)}"})
    else:
        processing_status.append({"status": "warning", "message": "没有数据可保存"})

@app.get("/api/status")
async def get_status():
    return {
        "status": processing_status,
        "file_path": result_file_path
    }

@app.get("/api/download")
async def download_file():
    if result_file_path and os.path.exists(result_file_path):
        return FileResponse(
            path=result_file_path,
            filename=os.path.basename(result_file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    return {"error": "文件不存在"}

@app.post("/api/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    global processing_status, result_file_path
    
    # 重置状态
    processing_status = []
    result_file_path = None
    
    # 保存上传的文件
    file_path = f"uploaded_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # 读取文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        url_list = [line.strip() for line in f.readlines()]
    
    # 删除临时文件
    os.remove(file_path)
    
    # 在后台任务中处理URL
    background_tasks.add_task(process_urls_background, url_list)
    
    return {"message": "文件已上传并开始处理，请查看状态"}

@app.post("/api/update-cookie")
async def update_cookie(cookie_string: str = Form(...)):
    """更新cookie"""
    try:
        # 解析cookie字符串
        cookies = {}
        for item in cookie_string.split(';'):
            if '=' in item:
                key, value = item.strip().split('=', 1)
                cookies[key] = value
        
        # 更新redbook模块中的cookies
        redbook.cookies = cookies
        
        return {"message": "Cookie更新成功", "cookies": cookies}
    except Exception as e:
        return {"error": f"Cookie更新失败: {str(e)}"}

@app.get("/api/get-cookie")
async def get_current_cookie():
    """获取当前cookie"""
    try:
        current_cookies = redbook.cookies
        # 将cookies转换为字符串格式
        cookie_string = "; ".join([f"{key}={value}" for key, value in current_cookies.items()])
        return {"cookies": current_cookies, "cookie_string": cookie_string}
    except Exception as e:
        return {"error": f"获取Cookie失败: {str(e)}"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8008, reload=True) 