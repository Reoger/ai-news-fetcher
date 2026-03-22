#!/usr/bin/env python3
"""测试所有数据源"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher

fetcher = AINewsFetcher()

print("=" * 60)
print("测试所有数据源")
print("=" * 60)

# 测试RSS源
print("\n📡 RSS源测试:")
rss_articles = fetcher.fetch_from_rss()
print(f"  获取到 {len(rss_articles)} 篇文章")

# 按来源分组
from collections import Counter
sources = [article['source'] for article in rss_articles]
source_counts = Counter(sources)

print("\n  各源文章数:")
for source, count in source_counts.items():
    print(f"    {source}: {count}篇")

# 测试新闻API
print("\n🔍 新闻API测试:")
api_articles = fetcher.fetch_from_news_api()
print(f"  获取到 {len(api_articles)} 篇文章")

# 测试网站爬取
print("\n🕷️  网站爬取测试:")
web_articles = fetcher.scrape_websites()
print(f"  获取到 {len(web_articles)} 篇文章")

print("\n" + "=" * 60)
print(f"总计: {len(rss_articles) + len(api_articles) + len(web_articles)} 篇文章")
print("=" * 60)
