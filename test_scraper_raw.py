import os
import sys
import requests
import json

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from redbook_app.redbook import extract_user_id_from_url, get_cookies

# Test URL
test_url = "https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/5e44b2e2000000000100128a?track_id=kolSimilar_1592ac1605644b5abce01c912fc377b5&source=Advertiser_Similar_Kol"

# Extract user ID from URL
user_id = extract_user_id_from_url(test_url)
print(f"Extracted user ID: {user_id}")

if user_id:
    # Get cookies
    cookies = get_cookies()
    
    # Base URLs
    user_info_url = f"https://pgy.xiaohongshu.com/api/solar/cooperator/user/blogger/{user_id}"
    data_summary_url = f"https://pgy.xiaohongshu.com/api/pgy/kol/data/data_summary?userId={user_id}&business=1"
    
    # Request headers
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
    
    # Make the requests
    try:
        # User info request
        print("Making request for user info...")
        user_response = requests.get(user_info_url, headers=headers, cookies=cookies)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Data summary request
        print("Making request for data summary...")
        summary_response = requests.get(data_summary_url, headers=headers, cookies=cookies)
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        # Print the raw responses
        print("\nUser Info Response:")
        print(json.dumps(user_data, indent=2, ensure_ascii=False))
        
        print("\nData Summary Response:")
        print(json.dumps(summary_data, indent=2, ensure_ascii=False))
        
        # Specifically look for fields in data summary:
        print("\nAll fields in data summary:")
        data_part = summary_data.get("data", {})
        for key, value in data_part.items():
            print(f"{key}: {value}")
        
        # Check for specific engagement-related fields
        print("\nChecking for specific engagement fields:")
        engagement_keys = [key for key in data_part.keys() if "engage" in key.lower() or "imp" in key.lower() or "cpuv" in key.lower()]
        for key in engagement_keys:
            print(f"{key}: {data_part.get(key)}")
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Failed to extract user ID from URL.") 