#!/usr/bin/env python3
"""
测试量子位RSS源
"""

import feedparser
from datetime import datetime, timedelta

print("🧪 测试量子位RSS源...")
print("=" * 60)

try:
    feed = feedparser.parse('https://www.qbitai.com/feed')
    source_name = feed.feed.get('title', '量子位')

    print(f"✅ RSS源连接成功！")
    print(f"📰 来源: {source_name}")
    print(f"🔗 链接: {feed.feed.get('link', 'N/A')}")
    print(f"📝 描述: {feed.feed.get('description', 'N/A')[:100]}...")
    print(f"📊 总文章数: {len(feed.entries)}")
    print()

    # 显示最近5篇文章
    print("📰 最新文章预览 (前5篇):")
    print("-" * 60)

    for i, entry in enumerate(feed.entries[:5], 1):
        print(f"\n{i}. {entry.get('title', '无标题')}")
        print(f"   链接: {entry.get('link', 'N/A')[:80]}...")
        print(f"   时间: {entry.get('published', '未知时间')}")

        # 获取摘要
        summary = entry.get('description', entry.get('summary', ''))
        if summary:
            # 移除HTML标签
            from bs4 import BeautifulSoup
            clean_summary = BeautifulSoup(summary, 'html.parser').get_text(strip=True)
            print(f"   摘要: {clean_summary[:100]}...")

    print("\n" + "=" * 60)
    print("✅ 量子位RSS源测试成功！")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
