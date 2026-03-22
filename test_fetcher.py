#!/usr/bin/env python3
"""
测试脚本 - 验证各个数据源是否正常工作
"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher
import os

def test_rss():
    """测试RSS获取"""
    print("\n🧪 测试 RSS 获取...")
    fetcher = AINewsFetcher()
    articles = fetcher.fetch_from_rss()
    print(f"✅ 获取到 {len(articles)} 篇RSS文章")
    return len(articles) > 0

def test_api():
    """测试API获取"""
    print("\n🧪 测试 NewsAPI 获取...")
    if not os.getenv('NEWS_API_KEY'):
        print("⚠️  未设置NEWS_API_KEY，跳过测试")
        return True

    fetcher = AINewsFetcher()
    articles = fetcher.fetch_from_news_api()
    print(f"✅ 获取到 {len(articles)} 篇API文章")
    return len(articles) > 0

def test_scraping():
    """测试网站爬取"""
    print("\n🧪 测试网站爬取...")
    fetcher = AINewsFetcher()
    articles = fetcher.scrape_websites()
    print(f"✅ 获取到 {len(articles)} 篇爬取文章")
    return len(articles) > 0

def test_markdown_generation():
    """测试Markdown生成"""
    print("\n🧪 测试Markdown生成...")
    fetcher = AINewsFetcher()

    # 使用示例数据
    test_articles = [
        {
            'title': '测试文章标题',
            'link': 'https://example.com/test',
            'summary': '这是一个测试文章的摘要内容。',
            'published': '2025-03-22',
            'source': '测试源'
        }
    ]

    md_content = fetcher.generate_markdown(test_articles)

    if md_content and 'AI动态日报' in md_content:
        print("✅ Markdown生成成功")
        print(f"\n生成的Markdown预览:\n{'='*60}")
        print(md_content[:300] + '...')
        return True
    else:
        print("❌ Markdown生成失败")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 AI News Fetcher 测试套件")
    print("=" * 60)

    results = {
        'RSS测试': test_rss(),
        'API测试': test_api(),
        '爬取测试': test_scraping(),
        'Markdown生成测试': test_markdown_generation()
    }

    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(results.values())

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查配置")
