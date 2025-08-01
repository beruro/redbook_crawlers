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
    "web_session": "040069b06170eb56e33d3d33bc3a4b976c002b",
    "unread": "{%22ub%22:%226889bc8f0000000025020287%22%2C%22ue%22:%226888b4f7000000000403e017%22%2C%22uc%22:25}",
    "webBuild": "4.75.0",
    "xsecappid": "ratlin",
    "customer-sso-sid": "68c517533119020201092856bbpbirxkwiaal1rh",
    "x-user-id-pgy.xiaohongshu.com": "67b6cf6804ee000000000001",
    "solar.beaker.session.id": "AT-68c517533119024497680616pivku1fb8fbggqox",
    "access-token-pgy.xiaohongshu.com": "customer.pgy.AT-68c517533119024497680616pivku1fb8fbggqox",
    "access-token-pgy.beta.xiaohongshu.com": "customer.pgy.AT-68c517533119024497680616pivku1fb8fbggqox",
    "acw_tc": "0a422b2617540157344662525e944ed9e4cee10a5dd91bd39d099502a703e5",
    "loadts": "1754015735894",
    "websectiga": "cffd9dcea65962b05ab048ac76962acee933d26157113bb213105a116241fa6c",
    "sec_poison_id": "9c7b8686-a616-49e1-b6e4-e28efae4545"
}

# 初始化全局cookies变量，允许动态更新
cookies = get_cookies()

def scrape_xiaohongshu_blogger(user_id):
    # 基础URL
    user_info_url = f"https://pgy.xiaohongshu.com/api/solar/cooperator/user/blogger/{user_id}"
    data_summary_url = f"https://pgy.xiaohongshu.com/api/pgy/kol/data/data_summary?userId={user_id}&business=1"
    
    # 生成时间戳
    import time
    current_timestamp = str(int(time.time() * 1000))
    
    # 两个请求共用的请求头
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': f'https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/{user_id}',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-b3-traceid': f'{random.randint(100000000000000, 999999999999999):x}',
        'x-s': 'O6slsjMlsBsK1BFWZgvlOlsWOjFL1lAbOBTp0jMGZgs3',
        'x-s-common': '2UQAPsHCPUIjqArjwjHjNsQhPsHCH0rjNsQhPaHCH0c1PahFHjIj2eHjwjQ+GnPW/MPjNsQhPUHCHdQY4BlkJjMAyBpVJsHVHdWFH0ijPshIN0D7PaHVHdWMH0ijP/DA+0PUP/Qf+Bb0JeSfJ/Ph+e802fpSPfMSJ04T8nTCJnQF4A+C89qAPeZIPePMP0clPsHVHdW9H0ijHjIj2eqjwjHjNsQhwsHCHDDAwoQH8B4AyfRI8FS98g+Dpd4daLP3JFSb/BMsn0pSPM87nrldzSzQ2bPAGdb7zgQB8nph8emSy9E0cgk+zSS1qgzianYt8Lzf/LzN4gzaa/+NqMS6qS4HLozoqfQnPbZEp98QyaRSp9P98pSl4oSzcgmca/P78nTTL08z/sVManD9q9z18np/8db8aob7JeQl4epsPrzsagW3tF4ryaRApdz3agYDq7YM47HFqgzkanYMGLSbP9LA/bGIa/+nprSe+9LI4gzVPDbrJg+P4fprLFTALMm7+LSb4d+kpdzt/7b7wrQM498cqBzSpr8g/FSh+bzQygL9nSm7qSmM4epQ4flY/BQdqA+l4oYQ2BpAPp87arS34nMQyFSE8nkdqMD6pMzd8/4SL7bF8aRr+7+rG7mkqBpD8pSUzozQcA8Szb87PDSb/d+/qgzVJfl/4LExpdzQ4fRSy7bFP9+y+7+nJAzdaLp/2LSiz/QH+FlpagYTLrRCJnRQyn+G8pm7zDS9ypHUcfRAzoi7q7Yn4BzQ408S8eq78pSx4gzQznzS+S4j80QM49kQyrkAP9RSqA8r4fpLLozwGML98LzM4ApQ4SSIG9pS8n8n47pIwn4AL7b7JFDALDlQ2BMVq7bFq9bc47SAqFYjaFc7q9zs8o+34gzSanS68nc6cnLAG9l+aLpO8nzj4d+nJFpaanTS8pzn4rMQyFzD4op7qrRl4F+QPFkSpopFzDS3P7+kqgzfanDA8p4c4F8tqg4PwopFaDSeyApQcAz1LB8CpDkCP9Ll4g4ianYizFS3PBpD4g46nSk34rQp+g+gcpbranTo/rkl4rTYqg4Mag8D8/8n4oYzqrTSPFSm8/bP2dQQzLkAyFQO8nkn4ApcLoz9anSdqAbM4eQQcAmApFz8pFS3J7+h2fzAPMm7/rSi8nLIpdzYcf+g+LShJrSQy/pSn/mtqAmy/7+kG94Sygb7JDSbpobQcFcM/ob7arSh/opQPAmSpAZFLB4B/9pk4gq9agYczL4M4F4jJApS2rb9q7Yn4bLhpdcEanTlarSeqBlwqgzf8gb7yrShJ7+n8n4SpMm72ezc4BlQcFFItM8FJDSkaBlF2Skba/PMqM8jP7+3qf4Sngp7L9Ql4BlQ2rY9anT6q98l4BMQ40pS2BchGFSbnnSHJ/WhaL+8qDSe4fp3Loql2SmFPSml4eSQ2rzyanW7qMzS/9pn4gqEqrzcJDSi/bYCpdz8/MmF8DSkLeQQynThagY/qDS9N9prw/pAL9EV8LQn4F+Qyr8CzM87cpbM4AQQcURSp04rnrSkLrG6JFbS8S8Fpbmc4ob6GFlsJn4npFSkJbSILo4wanT9qA80wBEQy/YiJ7b7pFS32DlH4gzgJMmFtFSi4p+Q4DMfanYCLoQn49zQygQPaLLMqA+M4MY6G9MmanYi8LSe+g+8cDTAyM878DSenLQQzLlbGnlQnLS9/pP6JBY+agGAqAmU+9pgpd4FaLL6qMSc4BbQzgQ1aL+mq9zM4FkQ4fMYcdb7nrSe+gPAG9WFaS8FcLRl4oQQ4fzSpMmFLrSiPo+//giManYdq98s8o+xpdzVqMStqA8l4AYUq0mApSmFqDDAJ7+/qURSzb8FzLS9/BMQ2b+xLop7zpbCLdmQ2e+SPpm7Gd+YPBphJBlGqM8FGFDAG0zQyFEALMSa4rS38g+DqgzNHjIj2eDjwjFl+/Pl+ec7+eWhNsQhP/Zjw0ZVHdWlPaHCHflk4BLjKc==',
        'x-t': current_timestamp,
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
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 406:
            print(f"❌ 406错误 - 请求不被接受: {e}")
            print("💡 解决建议:")
            print("   1. Cookie可能已过期，请更新Cookie")
            print("   2. 请求头可能不完整或格式错误")
            print("   3. 用户代理可能被服务器拒绝")
            print("   4. 请访问应用页面使用Cookie验证功能")
            return None
        elif e.response.status_code == 401:
            print(f"❌ 401错误 - 未授权访问: {e}")
            print("💡 Cookie已过期或无效，请重新获取Cookie")
            return None
        elif e.response.status_code == 403:
            print(f"❌ 403错误 - 访问被禁止: {e}")
            print("💡 可能触发了反爬虫机制，建议稍后再试或更新Cookie")
            return None
        else:
            print(f"❌ HTTP错误 {e.response.status_code}: {e}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络请求出错: {e}")
        return None
    except json.JSONDecodeError:
        print("❌ 解析JSON响应出错 - 服务器返回的不是有效JSON格式")
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