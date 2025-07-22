import requests
import json
import re
import pandas as pd
import os
from datetime import datetime
import time
import random

# 从环境变量获取 Cookie
def get_cookies():
    # cookies_str = os.environ.get('XIAOHONGSHU_COOKIES')
    # if cookies_str:
    #     try:
    #         return json.loads(cookies_str)
    #     except:
    #         # 如果 JSON 解析失败，尝试解析为字典
    #         cookies = {}
    #         for item in cookies_str.split(';'):
    #             if '=' in item:
    #                 key, value = item.strip().split('=', 1)
    #                 cookies[key] = value
    #         return cookies
    
    # 如果环境变量不存在，使用默认 Cookie
    return {
    "a1": "19363212f4acl9fm3846czee2men7mekzmbtw3zgg30000352410",
    "webId": "03a0d588d937b6c7f6f8a607e08e2415",
    "gid": "yjqKqJy42fuiyjqKqJyJi6qu40S1ji6qY4KSDkkuddJ6d9q8IW6dTE888q2J4y88fYq0dWKq",
    "customerClientId": "195177604463666",
    "abRequestId": "03a0d588d937b6c7f6f8a607e08e2415",
    "x-user-id-creator.xiaohongshu.com": "5aae83144eacab32f473510e",
    "web_session": "030037a07a83c92536a83f2eae204a75bf449d",
    "x-user-id-pgy.xiaohongshu.com": "666fcc2de200000000000001",
    "xsecappid": "ratlin",
    "acw_tc": "0a0d0e0317528178280124508e484abf9feaa6595bfcf6f61bffd5e7cbf1de",
    "websectiga": "f47eda31ec99545da40c2f731f0630efd2b0959e1dd10d5fedac3dce0bd1e04d",
    "sec_poison_id": "00f05050-2c2e-48da-a3ef-5eb9a67449be",
    "customer-sso-sid": "68c517528295397851909491ozwwokr3m1tmeecj",
    "solar.beaker.session.id": "AT-68c517528295397756569461xsm0irgry5lopioj",
    "access-token-pgy.xiaohongshu.com": "customer.pgy.AT-68c517528295397756569461xsm0irgry5lopioj",
    "access-token-pgy.beta.xiaohongshu.com": "customer.pgy.AT-68c517528295397756569461xsm0irgry5lopioj",
    "loadts": "1752817900223"
}

# 初始化全局cookies变量，允许动态更新
cookies = get_cookies()

def scrape_xiaohongshu_blogger(user_id):
    # 基础URL
    user_info_url = f"https://pgy.xiaohongshu.com/api/solar/cooperator/user/blogger/{user_id}"
    data_summary_url = f"https://pgy.xiaohongshu.com/api/pgy/kol/data/data_summary?userId={user_id}&business=1"
    
    # 两个请求共用的请求头
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'referer': f'https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/{user_id}',
        'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    }
    
    # 发送第一个请求获取用户信息
    try:
        response1 = requests.get(user_info_url, headers=headers, cookies=cookies)
        response1.raise_for_status()
        user_data = response1.json()
        
        # 发送第二个请求获取数据摘要
        response2 = requests.get(data_summary_url, headers=headers, cookies=cookies)
        response2.raise_for_status()
        summary_data = response2.json()
        
        # 提取所需信息
        result = {
            "达人名称": user_data.get("data", {}).get("name", "未知"),
            "id": user_data.get("data", {}).get("redId", "未知"),
            "主页链接": f"https://www.xiaohongshu.com/user/profile/{user_id}",
            "粉丝数(W)": round(user_data.get("data", {}).get("fansCount", 0) / 10000, 1),
        }
        
        # 处理赞藏数，可能是整数或字符串
        like_collect = user_data.get("data", {}).get("likeCollectCountInfo", 0)
        if isinstance(like_collect, str):
            # 如果是字符串(例如"80.0w"或"80.0万")，则去掉单位并转换为浮点数
            like_collect = float(like_collect.replace("w", "").replace("万", ""))
        elif isinstance(like_collect, (int, float)):
            # 如果已经是数字，则转换为万为单位
            like_collect = like_collect / 10000
        
        result["赞藏数(W)"] = round(like_collect, 1)
        result["互动中位数"] = summary_data.get("data", {}).get("mEngagementNum", "N/A")
        result["阅读中位数"] = summary_data.get("data", {}).get("readMedian", "N/A")
        result["曝光中位数"] = summary_data.get("data", {}).get("mAccumImpNum", "N/A")
        result["外溢进店中位数"] = summary_data.get("data", {}).get("mCpuvNum", "N/A")
        

        return result
        
    except requests.exceptions.RequestException as e:
        print(f"请求出错: {e}")
        return None
    except json.JSONDecodeError:
        print("解析JSON响应出错")
        return None
    except Exception as e:
        print(f"发生错误: {e}")
        return None

def extract_user_id_from_url(url):
    """从 URL 中提取用户 ID"""
    # 支持多种 URL 格式
    patterns = [
        r'blogger-detail/([a-zA-Z0-9]+)',  # 原始格式
        r'user/profile/([a-zA-Z0-9]+)',    # 用户主页格式
        r'xiaohongshu\.com/user/profile/([a-zA-Z0-9]+)',  # 完整用户主页 URL
        r'xiaohongshu\.com/discovery/item/([a-zA-Z0-9]+)'  # 笔记 URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def process_urls(urls):
    """处理多个URL并返回结果列表"""
    all_data = []
    results = []
    
    print(f"🔍 process_urls 调试信息:")
    print(f"  输入URL数量: {len(urls)}")
    print(f"  前3个URL: {urls[:3]}")
    
    # 将多个URL分批处理
    batch_size = 5  # 每批处理5个URL
    
    for i, url in enumerate(urls):
        url = url.strip()
        if not url:
            continue
            
        # 从URL中提取用户ID
        user_id = extract_user_id_from_url(url)
        
        if user_id:
            log_message = f"正在处理URL {i+1}/{len(urls)}: {url}, 用户ID: {user_id}"
            results.append({"status": "processing", "message": log_message})
            
            try:
                # 使用更合理的随机延时
                delay = random.uniform(2, 5)  # 2-5秒的随机延时
                results.append({"status": "info", "message": f"等待 {delay:.1f} 秒..."})
                time.sleep(delay)
                
                # 爬取博主数据
                result = scrape_xiaohongshu_blogger(user_id)
                
                if result:
                    all_data.append(result)
                    print(f"✅ 成功爬取用户 {user_id}: {result.get('达人名称', '未知')}")
                    results.append({"status": "success", "message": f"成功获取 {result['达人名称']} 的数据"})
                else:
                    print(f"❌ 爬取用户 {user_id} 失败")
                    results.append({"status": "error", "message": f"获取用户 {user_id} 数据失败"})
            except Exception as e:
                results.append({"status": "error", "message": f"处理用户 {user_id} 时出错: {str(e)}"})
            
            # 每处理一批URL，额外休息较短时间
            if (i + 1) % batch_size == 0 and i < len(urls) - 1:
                pause_time = random.uniform(5, 10)  # 5-10秒的休息时间
                results.append({"status": "info", "message": f"批量处理暂停，休息 {pause_time:.1f} 秒..."})
                time.sleep(pause_time)
        else:
            results.append({"status": "error", "message": f"无法从URL中提取用户ID: {url}"})
    
    print(f"📊 process_urls 完成统计:")
    print(f"  成功爬取数据条数: {len(all_data)}")
    print(f"  返回结果条数: {len(results)}")
    if all_data:
        print(f"  数据预览: {all_data[:2]}")
    
    return all_data, results

def save_to_excel(data_list):
    """保存数据到Excel并返回文件路径"""
    if not data_list:
        print("❌ 没有数据可保存")
        return None
        
    print(f"📊 准备保存 {len(data_list)} 条数据到Excel")
    
    # 添加时间戳到文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"小红书达人数据_{timestamp}.xlsx"
    
    # 尝试多个保存路径（适配云平台）
    save_paths = [
        os.path.join("results", filename),      # results目录
        filename,                               # 当前目录
        os.path.join("/tmp", filename),         # 临时目录（云平台）
        os.path.join(os.getcwd(), filename),    # 明确的当前工作目录
        os.path.join("/app", filename),         # 应用根目录
        os.path.join(os.path.expanduser("~"), filename)  # 用户目录
    ]
    
    # 创建DataFrame
    try:
        df = pd.DataFrame(data_list)
        print(f"✅ DataFrame创建成功，形状: {df.shape}")
        
        # 打印数据预览
        print("📋 数据预览:")
        for i, item in enumerate(data_list[:2]):  # 只显示前2条
            print(f"  {i+1}. {item.get('达人名称', '未知')}: {item.get('粉丝数(W)', 'N/A')}W粉丝")
            
    except Exception as e:
        print(f"❌ 创建DataFrame失败: {e}")
        return None
    
    saved_path = None
    save_errors = []
    
    # 尝试保存到不同路径
    for i, save_path in enumerate(save_paths):
        try:
            print(f"🔄 尝试保存路径 {i+1}/{len(save_paths)}: {save_path}")
            
            # 确保目录存在
            directory = os.path.dirname(save_path)
            if directory and not os.path.exists(directory):
                print(f"📁 创建目录: {directory}")
                os.makedirs(directory, exist_ok=True)
            
            # 保存到Excel
            df.to_excel(save_path, index=False, engine='openpyxl')
            print(f"💾 Excel保存操作完成")
            
            # 验证文件是否成功创建
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                print(f"✅ 文件验证成功: {save_path}")
                print(f"📏 文件大小: {file_size} 字节")
                
                if file_size > 1024:  # 至少1KB
                    saved_path = save_path
                    print(f"🎉 文件成功保存到: {save_path}")
                    break
                else:
                    print(f"⚠️ 文件太小 ({file_size} 字节)，可能保存失败")
                    save_errors.append(f"{save_path}: 文件太小")
            else:
                print(f"❌ 文件不存在: {save_path}")
                save_errors.append(f"{save_path}: 文件不存在")
                
        except Exception as e:
            error_msg = f"保存到 {save_path} 失败: {e}"
            print(f"❌ {error_msg}")
            save_errors.append(error_msg)
            continue
    
    if saved_path:
        print(f"🏆 最终成功保存: {saved_path}")
        return os.path.basename(saved_path)  # 返回文件名
    else:
        print("💥 所有保存路径都失败了!")
        print("📋 错误详情:")
        for error in save_errors:
            print(f"  - {error}")
        
        # 尝试获取更多调试信息
        print("🔍 系统信息:")
        print(f"  当前工作目录: {os.getcwd()}")
        print(f"  可写性测试...")
        
        for path in ["/tmp", ".", "/app"]:
            try:
                test_file = os.path.join(path, "test_write.tmp")
                with open(test_file, 'w') as f:
                    f.write("test")
                if os.path.exists(test_file):
                    os.remove(test_file)
                    print(f"  ✅ {path} 可写")
                else:
                    print(f"  ❌ {path} 写入失败")
            except Exception as e:
                print(f"  ❌ {path} 不可写: {e}")
        
        return None