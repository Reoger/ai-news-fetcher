#!/usr/bin/env python3
"""测试从文章页面获取内容"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher

fetcher = AINewsFetcher()

url = 'https://www.qbitai.com/2026/03/391014.html'
content = fetcher._fetch_article_content(url, max_length=200)

print("获取的内容:")
print(content)
print()
print(f"长度: {len(content)}")
