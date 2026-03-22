#!/usr/bin/env python3
"""测试发送到飞书的消息内容"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher
import os

# 模拟发送到飞书的内容
fetcher = AINewsFetcher()

# 读取生成的文章
filename = '/Users/luojie/workspace/scrpit/ai_articles/ai_news_20260322.md'
if os.path.exists(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        article_content = f.read()

    # 预览将要发送到飞书的消息
    print("=" * 60)
    print("📤 将要发送到飞书的消息预览")
    print("=" * 60)
    print()
    print(f"消息长度: {len(article_content)} 字符")
    print()
    print("消息内容（前500字）:")
    print("-" * 60)
    print(article_content[:500])
    print("-" * 60)
    print()
    print("...")
    print()
    print("消息内容（最后500字）:")
    print("-" * 60)
    print(article_content[-500:])
    print("-" * 60)
    print()
    print("✅ 完整文章内容将被发送到飞书")
else:
    print("❌ 文章文件不存在")
