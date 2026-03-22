#!/usr/bin/env python3
"""调试文章数据"""

import sys
import json
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher

fetcher = AINewsFetcher()

# 获取文章
articles = fetcher.fetch_from_rss()

print(f"获取到 {len(articles)} 篇文章")
print()

if articles:
    article = articles[0]
    print("第一篇文章数据:")
    print(f"标题: {article['title']}")
    print(f"来源: {article['source']}")
    print(f"简介长度: {len(article['summary'])}")
    print(f"简介内容: {article['summary'][:300]}")
    print()
    print("完整数据(JSON):")
    print(json.dumps(article, ensure_ascii=False, indent=2))
