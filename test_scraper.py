import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from redbook_app.redbook import extract_user_id_from_url, scrape_xiaohongshu_blogger

# Test URL
test_url = "https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/5e44b2e2000000000100128a?track_id=kolSimilar_1592ac1605644b5abce01c912fc377b5&source=Advertiser_Similar_Kol"

# Extract user ID from URL
user_id = extract_user_id_from_url(test_url)
print(f"Extracted user ID: {user_id}")

if user_id:
    # Scrape blogger data
    print("Scraping blogger data...")
    data = scrape_xiaohongshu_blogger(user_id)
    
    if data:
        print("\nScraped Data:")
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print("Failed to fetch data. This could be due to invalid cookies or network issues.")
else:
    print("Failed to extract user ID from URL.") 