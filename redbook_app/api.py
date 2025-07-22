from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
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
import io

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

# 添加全局变量存储最新的数据（内存方案）
latest_scraped_data = None
latest_scrape_timestamp = None

# 挂载静态文件
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

@app.post("/api/process")
async def process_data(background_tasks: BackgroundTasks, urls: str = Form(...)):
    global processing_status, result_file_path
    
    # 重置状态
    processing_status = []
    result_file_path = None
    
    # 分割URL并过滤空行
    url_list = [url.strip() for url in urls.strip().split('\n') if url.strip()]
    
    # 验证URL列表
    if not url_list:
        return {"error": "没有提供有效的URL"}
    
    # 添加初始状态信息
    processing_status.append({"status": "info", "message": f"准备处理 {len(url_list)} 个URL..."})
    
    # 在后台任务中处理URL
    background_tasks.add_task(process_urls_background, url_list)
    
    # 立即返回响应，不等待处理完成
    return {"message": f"处理已开始，共 {len(url_list)} 个URL，请通过状态API查询进度", "url_count": len(url_list)}

# 修改 process_urls_background 函数
async def process_urls_background(url_list):
    global processing_status, result_file_path
    
    try:
        # 更新状态为开始处理
        processing_status.append({"status": "info", "message": f"开始处理 {len(url_list)} 个URL..."})
        
        # 处理 URL
        data_list, results = redbook.process_urls(url_list)
        
        # 更新处理结果
        processing_status.extend(results)
        
        # 如果有数据，保存到 Excel
        if data_list:
            # 保存到全局变量（内存方案）
            global latest_scraped_data, latest_scrape_timestamp
            latest_scraped_data = data_list
            latest_scrape_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            print(f"💾 内存数据保存调试信息:")
            print(f"  数据条数: {len(data_list)}")
            print(f"  时间戳: {latest_scrape_timestamp}")
            print(f"  数据预览: {data_list[:2] if len(data_list) > 0 else '空'}")
            
            try:
                processing_status.append({"status": "info", "message": f"准备保存 {len(data_list)} 条数据到Excel..."})
                
                filename = redbook.save_to_excel(data_list)
                if filename:
                    # save_to_excel 现在已经处理了文件保存和路径，不需要再移动
                    # 查找实际保存的文件路径
                    possible_paths = [
                        os.path.join("results", filename),
                        filename,
                        os.path.join("/tmp", filename),
                        os.path.join(os.getcwd(), filename),
                        os.path.join("/app", filename),
                        os.path.join(os.path.expanduser("~"), filename)
                    ]
                    
                    actual_path = None
                    for path in possible_paths:
                        if os.path.exists(path):
                            actual_path = path
                            file_size = os.path.getsize(path)
                            print(f"找到文件: {path}, 大小: {file_size} 字节")
                            break
                    
                    if actual_path:
                        result_file_path = actual_path
                        processing_status.append({"status": "success", "message": f"✅ 数据已成功保存到 {filename}"})
                        processing_status.append({"status": "info", "message": f"📍 文件位置: {actual_path}"})
                        print(f"文件实际保存位置: {actual_path}")
                    else:
                        # 文件保存失败，但我们有内存备份
                        processing_status.append({"status": "warning", "message": f"⚠️ 文件保存失败，但数据已保存到内存"})
                        processing_status.append({"status": "info", "message": "📥 可以使用内存下载功能"})
                        result_file_path = None
                else:
                    # 文件保存完全失败，但我们有内存备份
                    processing_status.append({"status": "warning", "message": "⚠️ 文件保存失败，但数据已保存到内存"})
                    processing_status.append({"status": "info", "message": "📥 可以使用内存下载功能"})
                    result_file_path = None
            except Exception as e:
                processing_status.append({"status": "error", "message": f"保存Excel时出错: {str(e)}"})
        else:
            processing_status.append({"status": "warning", "message": "没有数据可保存"})
            
        # 添加处理完成状态
        processing_status.append({"status": "success", "message": "所有URL处理完成"})
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        processing_status.append({"status": "error", "message": f"处理URL时出错: {str(e)}"})
        print(f"处理URL时错误详情: {error_detail}")

@app.get("/api/status")
async def get_status():
    global processing_status, result_file_path
    
    try:
        # 确保processing_status是一个列表
        if not isinstance(processing_status, list):
            processing_status = []
        
        # 确保result_file_path是字符串或None
        file_path = result_file_path if isinstance(result_file_path, str) else None
        
        # 构建响应数据
        response_data = {
            "status": processing_status,
            "file_path": file_path,
            "timestamp": datetime.now().isoformat()
        }
        
        # 验证响应数据可以序列化为JSON
        import json
        json.dumps(response_data, ensure_ascii=False)
        
        return response_data
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"获取状态时错误详情: {error_detail}")
        
        # 即使出错，也返回一个有效的JSON响应
        emergency_response = {
            "status": [
                {"status": "error", "message": f"获取状态出错: {str(e)}"},
                {"status": "info", "message": "如果数据处理已完成，请尝试下载结果"}
            ],
            "file_path": result_file_path if isinstance(result_file_path, str) else None,
            "error_detail": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return emergency_response

@app.get("/api/download")
async def download_file():
    global result_file_path
    
    # 定义可能的文件查找路径
    search_paths = [
        "results",           # results目录
        ".",                # 当前目录
        "/tmp",             # 临时目录（云平台常用）
        os.getcwd(),        # 当前工作目录
        os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录
    ]
    
    found_files = []
    
    # 1. 首先检查全局变量中的文件路径
    if result_file_path:
        if os.path.exists(result_file_path):
            return FileResponse(
                path=result_file_path,
                filename=os.path.basename(result_file_path),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            print(f"全局路径文件不存在: {result_file_path}")
    
    # 2. 在所有可能的路径中查找Excel文件
    for search_path in search_paths:
        try:
            if os.path.exists(search_path) and os.path.isdir(search_path):
                excel_files = []
                for file in os.listdir(search_path):
                    if file.endswith('.xlsx') and '小红书达人数据' in file:
                        full_path = os.path.join(search_path, file)
                        if os.path.isfile(full_path):
                            excel_files.append(full_path)
                
                found_files.extend(excel_files)
                print(f"在 {search_path} 中找到 {len(excel_files)} 个Excel文件")
                
        except Exception as e:
            print(f"搜索路径 {search_path} 时出错: {e}")
            continue
    
    # 3. 如果找到文件，选择最新的
    if found_files:
        # 按修改时间排序，选择最新的
        try:
            latest_file = max(found_files, key=lambda x: os.path.getmtime(x))
            print(f"选择最新文件: {latest_file}")
            
            # 更新全局变量
            result_file_path = latest_file
            
            return FileResponse(
                path=latest_file,
                filename=os.path.basename(latest_file),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            print(f"处理找到的文件时出错: {e}")
    
    # 4. 如果还是没找到，尝试查找任何Excel文件
    try:
        for search_path in search_paths:
            if os.path.exists(search_path) and os.path.isdir(search_path):
                all_excel = [f for f in os.listdir(search_path) if f.endswith('.xlsx')]
                if all_excel:
                    latest_excel = max([os.path.join(search_path, f) for f in all_excel], 
                                     key=lambda x: os.path.getmtime(x))
                    print(f"找到备选Excel文件: {latest_excel}")
                    return FileResponse(
                        path=latest_excel,
                        filename=os.path.basename(latest_excel),
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    except Exception as e:
        print(f"查找备选文件时出错: {e}")
    
    # 5. 实在找不到，返回详细的调试信息
    debug_info = {
        "error": "文件不存在", 
        "message": "请确保数据处理已完成",
        "debug": {
            "result_file_path": result_file_path,
            "current_directory": os.getcwd(),
            "searched_paths": search_paths,
            "found_files_count": len(found_files),
            "found_files": found_files[:3] if found_files else [],  # 只显示前3个避免响应过大
        }
    }
    
    return debug_info

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
        
        processing_status.append({"status": "success", "message": f"Cookie已更新，包含 {len(cookies)} 个字段"})
        
        return {"message": "Cookie更新成功", "cookie_count": len(cookies)}
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        processing_status.append({"status": "error", "message": f"Cookie更新失败: {str(e)}"})
        return {"error": f"Cookie更新失败: {str(e)}", "traceback": error_detail}

@app.get("/api/get-cookie")
async def get_current_cookie():
    """获取当前cookie"""
    try:
        current_cookies = redbook.cookies
        # 将cookies转换为字符串格式
        cookie_string = "; ".join([f"{key}={value}" for key, value in current_cookies.items()])
        return {
            "cookies": current_cookies, 
            "cookie_string": cookie_string,
            "cookie_count": len(current_cookies)
        }
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {"error": f"获取Cookie失败: {str(e)}", "traceback": error_detail}

@app.get("/api/download-memory")
async def download_memory():
    """通过内存流直接下载Excel，完全绕过文件系统"""
    global latest_scraped_data, latest_scrape_timestamp
    
    print(f"🔍 内存下载调试信息:")
    print(f"  latest_scraped_data: {latest_scraped_data is not None}")
    print(f"  latest_scrape_timestamp: {latest_scrape_timestamp}")
    if latest_scraped_data:
        print(f"  数据条数: {len(latest_scraped_data)}")
        print(f"  数据预览: {latest_scraped_data[:2] if len(latest_scraped_data) > 0 else '空'}")
    
    if not latest_scraped_data:
        # 尝试从文件系统恢复数据
        print("🔄 内存中没有数据，尝试从文件系统恢复...")
        try:
            # 查找最新的Excel文件
            import glob
            excel_files = glob.glob("*.xlsx") + glob.glob("results/*.xlsx") + glob.glob("/tmp/*.xlsx")
            if excel_files:
                latest_file = max(excel_files, key=os.path.getctime)
                print(f"📁 找到文件: {latest_file}")
                # 读取Excel文件并转换为数据
                df = pd.read_excel(latest_file)
                latest_scraped_data = df.to_dict('records')
                print(f"✅ 从文件恢复数据成功，条数: {len(latest_scraped_data)}")
            else:
                return {"error": "没有可下载的数据", "message": "请先爬取数据"}
        except Exception as e:
            print(f"❌ 从文件恢复数据失败: {e}")
            return {"error": "没有可下载的数据", "message": "请先爬取数据"}
    
    try:
        # 创建DataFrame
        df = pd.DataFrame(latest_scraped_data)
        
        # 生成文件名
        timestamp = latest_scrape_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"小红书达人数据_{timestamp}.xlsx"
        
        # 创建内存流
        output = io.BytesIO()
        
        # 直接写入内存流
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='达人数据')
        
        # 重置流位置
        output.seek(0)
        
        # 返回文件流
        return StreamingResponse(
            io.BytesIO(output.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        return {"error": f"生成Excel失败: {str(e)}"}

@app.get("/api/download-base64")
async def download_base64():
    """返回Base64编码的Excel数据作为终极备用方案"""
    global latest_scraped_data, latest_scrape_timestamp
    
    if not latest_scraped_data:
        return {"error": "没有可下载的数据", "message": "请先爬取数据"}
    
    try:
        import base64
        
        # 创建DataFrame
        df = pd.DataFrame(latest_scraped_data)
        
        # 生成文件名
        timestamp = latest_scrape_timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"小红书达人数据_{timestamp}.xlsx"
        
        # 创建内存流
        output = io.BytesIO()
        
        # 写入Excel
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='达人数据')
        
        # 获取二进制数据
        excel_data = output.getvalue()
        
        # 编码为Base64
        base64_data = base64.b64encode(excel_data).decode('utf-8')
        
        return {
            "success": True,
            "filename": filename,
            "data": base64_data,
            "size": len(excel_data),
            "message": "Base64数据传输成功"
        }
        
    except Exception as e:
        return {"error": f"生成Base64数据失败: {str(e)}"}

@app.get("/api/validate-cookie")
async def validate_cookie():
    """验证cookie有效性和获取信息"""
    try:
        current_cookies = redbook.cookies
        
        # 分析cookie信息
        cookie_info = analyze_cookie_expiry(current_cookies)
        
        # 测试cookie是否有效
        validity_result = await test_cookie_validity(current_cookies)
        
        return {
            "is_valid": validity_result.get("is_valid"),
            "test_message": validity_result.get("message", ""),
            "test_results": validity_result.get("test_results", []),
            "cookie_info": cookie_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return {"error": f"验证Cookie失败: {str(e)}", "traceback": error_detail}

async def test_cookie_validity(cookies):
    """通过实际API调用测试cookie是否有效"""
    try:
        # 测试几个不同的API端点来验证cookie有效性
        test_endpoints = [
            {
                "url": "https://pgy.xiaohongshu.com/api/solar/cooperator/user/profile",
                "description": "用户配置信息"
            },
            {
                "url": "https://pgy.xiaohongshu.com/api/pgy/kol/search/bloggers",
                "description": "博主搜索API"
            }
        ]
        
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
            'referer': 'https://pgy.xiaohongshu.com/solar/pre-trade/home',
        }
        
        test_results = []
        
        for endpoint in test_endpoints:
            try:
                response = requests.get(endpoint["url"], headers=headers, cookies=cookies, timeout=10)
                
                result = {
                    "endpoint": endpoint["description"],
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "unauthorized": response.status_code in [401, 403]
                }
                
                test_results.append(result)
                
                # 如果任何一个端点返回401/403，说明cookie可能无效
                if response.status_code in [401, 403]:
                    return {
                        "is_valid": False,
                        "test_results": test_results,
                        "message": f"API测试失败：{endpoint['description']} 返回 {response.status_code}"
                    }
                    
            except Exception as e:
                test_results.append({
                    "endpoint": endpoint["description"],
                    "error": str(e),
                    "success": False
                })
        
        # 如果所有测试都通过，说明cookie可能有效
        successful_tests = sum(1 for r in test_results if r.get("success", False))
        
        return {
            "is_valid": successful_tests > 0,
            "test_results": test_results,
            "message": f"完成 {len(test_results)} 项测试，{successful_tests} 项成功"
        }
        
    except Exception as e:
        return {
            "is_valid": None,
            "error": str(e),
            "message": "网络测试失败，无法确定cookie状态"
        }

def analyze_cookie_expiry(cookies):
    """分析cookie信息（不猜测过期时间）"""
    import time
    from datetime import datetime, timedelta
    
    cookie_info = {
        "loadts": None,
        "loadts_readable": None,
        "session_tokens": [],
        "important_note": "⚠️ 我们无法从cookie中准确获取过期时间，只能通过实际API测试来验证有效性"
    }
    
    # 解析loadts时间戳（但明确这不是过期时间）
    if "loadts" in cookies:
        try:
            loadts = cookies["loadts"]
            
            # 尝试不同的时间戳格式
            if len(loadts) <= 10:
                # 秒级时间戳
                loadts_datetime = datetime.fromtimestamp(int(loadts))
            else:
                # 毫秒级时间戳，可能需要补0
                if len(loadts) == 11:
                    loadts_ms = int(loadts + '00')
                elif len(loadts) == 12:
                    loadts_ms = int(loadts + '0')
                else:
                    loadts_ms = int(loadts)
                loadts_datetime = datetime.fromtimestamp(loadts_ms / 1000)
            
            cookie_info["loadts"] = loadts
            cookie_info["loadts_readable"] = loadts_datetime.strftime("%Y-%m-%d %H:%M:%S")
            cookie_info["loadts_note"] = "这可能是会话创建时间，不是过期时间"
            
        except (ValueError, TypeError) as e:
            cookie_info["loadts_readable"] = f"无法解析时间戳: {e}"
    
    # 识别重要的会话令牌
    session_keys = ["web_session", "customer-sso-sid", "solar.beaker.session.id", 
                   "access-token-pgy.xiaohongshu.com", "access-token-pgy.beta.xiaohongshu.com"]
    
    for key in session_keys:
        if key in cookies:
            cookie_info["session_tokens"].append({
                "key": key,
                "length": len(cookies[key]),
                "prefix": cookies[key][:15] + "..." if len(cookies[key]) > 15 else cookies[key]
            })
    
    # 添加获取真实过期时间的说明
    cookie_info["how_to_get_real_expiry"] = [
        "🔍 真实过期时间只能通过以下方式获取：",
        "1. 浏览器开发者工具 → Application → Cookies → 查看 Expires 列",
        "2. Network 面板 → 查看 Set-Cookie 响应头",
        "3. 最可靠的方法：定期测试API调用是否还有效"
    ]
    
    return cookie_info

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
    port = int(os.environ.get('PORT', 8008))
    uvicorn.run("api:app", host="0.0.0.0", port=port, log_level="info") 