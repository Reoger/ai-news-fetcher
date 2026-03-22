#!/usr/bin/env python3
"""
快速测试NewsAPI是否正常工作
"""

import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

# 加载环境变量
load_dotenv()

API_KEY = os.getenv('NEWS_API_KEY')
print(f"🔑 API密钥: {API_KEY[:10]}...{API_KEY[-4:] if API_KEY else 'None'}")

if not API_KEY or API_KEY == 'your-api-key-here':
    print("❌ 未找到有效的API密钥")
    exit(1)

# 测试API请求
print("🔍 测试NewsAPI连接...")
from_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

params = {
    'q': 'AI OR artificial intelligence',
    'language': 'en',
    'sortBy': 'publishedAt',
    'from': from_date,
    'apiKey': API_KEY,
    'pageSize': 3
}

try:
    response = requests.get('https://newsapi.org/v2/everything', params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    print(f"✅ API连接成功！")
    print(f"📊 获取到 {len(data.get('articles', []))} 篇文章")

    if data.get('articles'):
        print("\n📰 最新文章预览:")
        for i, article in enumerate(data['articles'][:3], 1):
            print(f"{i}. {article['title'][:60]}...")
            print(f"   来源: {article['source']['name']}")
            print(f"   时间: {article['publishedAt']}")
            print()

except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP错误: {e}")
    print(f"   响应: {response.text}")
except Exception as e:
    print(f"❌ 错误: {e}")
