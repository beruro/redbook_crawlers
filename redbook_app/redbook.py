import requests
import json
import re
import pandas as pd
import os
from datetime import datetime
import time

# 从环境变量获取 Cookie
def get_cookies():
    cookies_str = os.environ.get('XIAOHONGSHU_COOKIES')
    if cookies_str:
        try:
            return json.loads(cookies_str)
        except:
            # 如果 JSON 解析失败，尝试解析为字典
            cookies = {}
            for item in cookies_str.split(';'):
                if '=' in item:
                    key, value = item.strip().split('=', 1)
                    cookies[key] = value
            return cookies
    
    # 如果环境变量不存在，使用默认 Cookie
    return {
        "a1": "19363212f4acl9fm3846czee2men7mekzmbtw3zgg30000352410",
        "webId": "03a0d588d937b6c7f6f8a607e08e2415",
        "gid": "yjqKqJy42fuiyjqKqJyJi6qu40S1ji6qY4KSDkkuddJ6d9q8IW6dTE888q2J4y88fYq0dWKq",
        "x-user-id-pgy.xiaohongshu.com": "666fcc2de200000000000001",
        "customerClientId": "195177604463666",
        "abRequestId": "03a0d588d937b6c7f6f8a607e08e2415",
        "x-user-id-creator.xiaohongshu.com": "5aae83144eacab32f473510e",
        "web_session": "030037a07a83c92536a83f2eae204a75bf449d",
        "loadts": "1744441044226",
        "xsecappid": "ratlin",
        "acw_tc": "0a0d068317452200818276972e7a25f4771165c751b843f8217c8f9418bf35",
        "websectiga": "8886be45f388a1ee7bf611a69f3e174cae48f1ea02c0f8ec3256031b8be9c7ee",
        "sec_poison_id": "2d0ec507-46c6-44a4-a3df-7878e57d11e4",
        "customer-sso-sid": "68c517495664263468210246irrt863syga98fw1",
        "solar.beaker.session.id": "AT-68c5174956642634658924436lrc2wxcewffhq7a",
        "access-token-pgy.xiaohongshu.com": "customer.pgy.AT-68c5174956642634658924436lrc2wxcewffhq7a",
        "access-token-pgy.beta.xiaohongshu.com": "customer.pgy.AT-68c5174956642634658924436lrc2wxcewffhq7a"
    }

cookies = get_cookies()

def scrape_xiaohongshu_blogger(user_id):
    # 基础URL
    user_info_url = f"https://pgy.xiaohongshu.com/api/solar/cooperator/user/blogger/{user_id}"
    data_summary_url = f"https://pgy.xiaohongshu.com/api/solar/kol/data_v3/data_summary?userId={user_id}&business=1"
    
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
        result["互动中位数"] = summary_data.get("data", {}).get("interactionMedian", "N/A")
        result["阅读中位数"] = summary_data.get("data", {}).get("readMedian", "N/A")
        
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
    
    for url in urls:
        url = url.strip()
        if not url:
            continue
            
        # 从URL中提取用户ID
        user_id = extract_user_id_from_url(url)
        
        if user_id:
            log_message = f"正在处理URL: {url}, 用户ID: {user_id}"
            results.append({"status": "processing", "message": log_message})
            
            # 爬取博主数据
            result = scrape_xiaohongshu_blogger(user_id)
            
            if result:
                all_data.append(result)
                results.append({"status": "success", "message": f"成功获取 {result['达人名称']} 的数据"})
            else:
                results.append({"status": "error", "message": f"获取用户 {user_id} 数据失败"})
            
            # 添加延时以避免请求过于频繁
            time.sleep(2)
        else:
            results.append({"status": "error", "message": f"无法从URL中提取用户ID: {url}"})
    
    return all_data, results

def save_to_excel(data_list):
    """保存数据到Excel并返回文件路径"""
    if not data_list:
        return None
        
    # 添加时间戳到文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"小红书达人数据_{timestamp}.xlsx"
    
    # 创建DataFrame
    df = pd.DataFrame(data_list)
    
    # 保存到Excel
    df.to_excel(filename, index=False)
    return filename