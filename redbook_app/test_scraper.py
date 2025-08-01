#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import redbook

def test_scraper():
    print("🚀 开始测试小红书爬虫...")
    
    # 测试URL
    test_urls = [
        "https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/598580556a6a693546052568?track_id=kolMatch_c9b9f2f0323a4dcaa7d02a6a83ae4642&source=Advertiser_Kol",
        "https://pgy.xiaohongshu.com/solar/pre-trade/blogger-detail/5e0b4f940000000001009091?track_id=kolSimilar_0f79c23e56bd445faaf850b18dcff3b4&source=Advertiser_Similar_Kol"
    ]
    
    print(f"📝 准备测试 {len(test_urls)} 个URL...")
    
    # 测试单个用户
    success_count = 0
    
    for i, url in enumerate(test_urls):
        print(f"\n🔍 测试 {i+1}/{len(test_urls)}: {url}")
        
        # 提取用户ID
        user_id = redbook.extract_user_id_from_url(url)
        if user_id:
            print(f"✅ 提取到用户ID: {user_id}")
            
            # 测试爬取
            try:
                result = redbook.scrape_xiaohongshu_blogger(user_id)
                if result:
                    print("🎉 爬取成功！")
                    print(f"   达人名称: {result.get('达人名称', 'N/A')}")
                    print(f"   粉丝数(W): {result.get('粉丝数(W)', 'N/A')}")
                    print(f"   赞藏数(W): {result.get('赞藏数(W)', 'N/A')}")
                    print(f"   互动中位数: {result.get('互动中位数', 'N/A')}")
                    print(f"   阅读中位数: {result.get('阅读中位数', 'N/A')}")
                    print(f"   曝光中位数: {result.get('曝光中位数', 'N/A')}")
                    success_count += 1
                else:
                    print("❌ 爬取失败")
            except Exception as e:
                print(f"💥 爬取出错: {e}")
        else:
            print("❌ 无法提取用户ID")
    
    if success_count > 0:
        print(f"\n🎉 测试完成！成功爬取 {success_count}/{len(test_urls)} 个用户数据")
        return True
    else:
        print("\n💥 所有测试都失败了")
        return False

if __name__ == "__main__":
    success = test_scraper()
    if success:
        print("\n✅ 爬虫配置正常工作")
    else:
        print("\n😞 测试失败，可能需要进一步调整配置") 