#!/usr/bin/env python3
"""调试清理函数"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher
import feedparser

fetcher = AINewsFetcher()

# 测试RSS清理
feed = feedparser.parse('https://www.qbitai.com/feed')
if feed.entries:
    entry = feed.entries[0]
    description = entry.get('description', entry.get('summary', ''))

    print("原始描述:")
    print(description[:200])
    print()

    print("清理后:")
    cleaned = fetcher._clean_html(description)
    print(cleaned)
    print()
    print(f"长度: {len(cleaned)}")
