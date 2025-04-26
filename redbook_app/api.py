from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import os
import sys
from typing import List, Dict, Any, Optional
from fastapi.staticfiles import StaticFiles
import pandas as pd
from datetime import datetime
import threading
import time
import requests

# 将当前目录添加到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import redbook

app = FastAPI(title="小红书达人数据爬取工具 API")

# 添加CORS中间件，允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建用于存储结果的目录
os.makedirs("results", exist_ok=True)

class ProcessStatus(BaseModel):
    status: str
    message: str
    file_path: Optional[str] = None

# 全局变量存储处理状态
processing_status = []
result_file_path = None

# 挂载静态文件
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

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

# 修改 process_urls_background 函数
async def process_urls_background(url_list):
    global processing_status, result_file_path
    
    # 更新状态为开始处理
    if not any(item.get("message") == "开始处理URL..." for item in processing_status):
        processing_status.append({"status": "info", "message": "开始处理URL..."})
    
    # 处理 URL
    data_list, results = redbook.process_urls(url_list)
    
    # 更新处理结果
    processing_status.extend(results)
    
    # 如果有数据，保存到 Excel
    if data_list:
        try:
            filename = redbook.save_to_excel(data_list)
            if filename:
                # 移动文件到 results 目录
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
    try:
        return {
            "status": processing_status,
            "file_path": result_file_path
        }
    except Exception as e:
        import traceback
        error_detail = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }
        print(f"获取状态时错误详情: {error_detail}")
        return {"status": [{"status": "error", "message": f"获取状态出错: {str(e)}"}], "error_detail": error_detail}

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
    
    # 验证文件类型
    if not file.filename.endswith('.txt'):
        return {"error": "请上传 TXT 文本文件"}
    
    # 保存上传的文件
    file_path = f"uploaded_{file.filename}"
    try:
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 读取文件内容
        url_list = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # 跳过空行
                    url_list.append(line)
        
        # 删除临时文件
        os.remove(file_path)
        
        if not url_list:
            return {"error": "文件中没有有效的 URL"}
        
        # 在后台任务中处理 URL
        processing_status.append({"status": "info", "message": f"从文件中读取了 {len(url_list)} 个 URL"})
        background_tasks.add_task(process_urls_background, url_list)
        
        return {"message": "文件已上传并开始处理，请查看状态"}
    
    except Exception as e:
        # 确保临时文件被删除
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": f"处理文件时出错: {str(e)}"}

@app.post("/api/upload-excel")
async def upload_excel_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), column: str = Form("A")):
    global processing_status, result_file_path
    
    # 重置状态
    processing_status = []
    result_file_path = None
    
    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return {"error": "请上传 Excel 文件 (.xlsx 或 .xls)"}
    
    # 保存上传的文件
    file_path = f"uploaded_{file.filename}"
    try:
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        # 读取 Excel 文件
        try:
            # 添加详细日志
            processing_status.append({"status": "info", "message": f"正在读取 Excel 文件: {file.filename}"})
            
            # 尝试读取 Excel 文件，不跳过任何行
            df = pd.read_excel(file_path)
            
            # 记录总行数
            total_rows = len(df)
            processing_status.append({"status": "info", "message": f"Excel 文件共有 {total_rows} 行数据"})
            
            # 检查列是否存在
            if column.upper() in df.columns:
                # 使用列名
                url_column = column.upper()
                processing_status.append({"status": "info", "message": f"使用列名: {url_column}"})
            elif column.isalpha():
                # 将列字母转换为索引 (A->0, B->1, etc.)
                col_idx = ord(column.upper()) - ord('A')
                if col_idx >= 0 and col_idx < len(df.columns):
                    url_column = df.columns[col_idx]
                    processing_status.append({"status": "info", "message": f"使用列 {column} (列名: {url_column})"})
                else:
                    return {"error": f"列 {column} 不存在，文件只有 {len(df.columns)} 列"}
            else:
                return {"error": "请提供有效的列名或列字母 (如 A, B, C...)"}
            
            # 提取 URL - 更宽松的验证
            url_list = []
            skipped_rows = 0
            empty_rows = 0
            
            # 遍历所有行，不使用 dropna()
            for i, row in df.iterrows():
                if url_column in row and pd.notna(row[url_column]):
                    url = str(row[url_column]).strip()
                    if url:
                        # 更宽松的 URL 验证，只要不是空字符串就接受
                        url_list.append(url)
                    else:
                        empty_rows += 1
                else:
                    skipped_rows += 1
            
            # 删除临时文件
            os.remove(file_path)
            
            # 添加详细日志
            processing_status.append({"status": "info", "message": f"找到 {len(url_list)} 个 URL，跳过 {skipped_rows} 行空值，{empty_rows} 行空字符串"})
            
            if not url_list:
                return {"error": "Excel 文件中没有找到有效的 URL"}
            
            # 显示前几个 URL 作为示例
            sample_size = min(3, len(url_list))
            samples = url_list[:sample_size]
            processing_status.append({"status": "info", "message": f"URL 示例: {', '.join(samples)}"})
            
            # 在后台任务中处理 URL
            background_tasks.add_task(process_urls_background, url_list)
            
            return {"message": f"Excel 文件已上传并开始处理 {len(url_list)} 个 URL，请查看状态"}
            
        except Exception as e:
            processing_status.append({"status": "error", "message": f"读取 Excel 文件时出错: {str(e)}"})
            return {"error": f"读取 Excel 文件时出错: {str(e)}"}
            
    except Exception as e:
        # 确保临时文件被删除
        if os.path.exists(file_path):
            os.remove(file_path)
        return {"error": f"处理文件时出错: {str(e)}"}

# 修改根路径处理程序，重定向到前端
@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>小红书爬虫工具</title>
        <meta charset="UTF-8">
        <meta http-equiv="refresh" content="0;url=/frontend/index.html">
    </head>
    <body>
        <p>正在重定向到小红书爬虫工具...</p>
    </body>
    </html>
    """

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# 自动 ping 服务，防止 Heroku 休眠
def ping_service():
    app_url = os.environ.get('APP_URL')
    if not app_url:
        print("WARNING: APP_URL 环境变量未设置，自动 ping 功能不会工作")
        return
    
    while True:
        try:
            response = requests.get(f"{app_url}/api/health")
            print(f"自动 ping 服务: {response.status_code}")
        except Exception as e:
            print(f"自动 ping 失败: {e}")
        
        # 每 25 分钟 ping 一次，低于 Heroku 的 30 分钟休眠阈值
        time.sleep(25 * 60)

# 在主函数中启动 ping 线程
if __name__ == "__main__":
    # 启动自动 ping 线程
    if os.environ.get('PREVENT_SLEEP') == 'true':
        ping_thread = threading.Thread(target=ping_service, daemon=True)
        ping_thread.start()
    
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.environ.get('PORT', 8008)), reload=True) 