#!/usr/bin/env python3
"""测试翻译功能"""

import sys
sys.path.insert(0, '/Users/luojie/workspace/scrpit')

from ai_news_fetcher import AINewsFetcher, TRANSLATION_ENABLED

print("=" * 60)
print("🧪 翻译功能测试")
print("=" * 60)

if not TRANSLATION_ENABLED:
    print("❌ 翻译功能未启用，请配置OPENAI_API_KEY")
    print("   在 .env 文件中添加: OPENAI_API_KEY=your-key-here")
    exit(1)

fetcher = AINewsFetcher()

# 测试英文检测
print("\n📝 测试英文检测:")
test_texts = [
    "Hello, this is a test",
    "这是一个测试",
    "GPT-4 is a large language model",
    "OpenAI发布GPT-4",
]

for text in test_texts:
    is_english = fetcher._is_english(text)
    status = "英文" if is_english else "中文"
    print(f"  '{text}' -> {status}")

# 测试翻译功能
print("\n🌐 测试翻译功能:")
test_translations = [
    "How we monitor internal coding agents for misalignment",
    "Introducing GPT-5.4 mini and nano",
    "OpenAI to acquire Astral",
]

for text in test_translations:
    print(f"  原文: {text}")
    translated = fetcher._translate_text(text)
    print(f"  译文: {translated}")
    print()

print("=" * 60)
print("✅ 翻译功能测试完成")
print("=" * 60)
