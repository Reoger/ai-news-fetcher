#!/usr/bin/env python3
"""
AI News Fetcher - 定时获取最新AI动态并生成文章
支持多种数据源：RSS订阅、新闻API、网页爬取
支持自动翻译英文内容为中文（使用免费Google翻译）
"""

import feedparser
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import os
from typing import List, Dict
import re
import subprocess
from dotenv import load_dotenv

# Google翻译器（免费，无需API密钥）
try:
    from googletrans import Translator
    google_translator = Translator()
    GOOGLE_TRANSLATE_AVAILABLE = True
    print("✅ Google翻译器初始化成功")
except Exception as e:
    google_translator = None
    GOOGLE_TRANSLATE_AVAILABLE = False
    print(f"⚠️  Google翻译器初始化失败: {e}")

# OpenAI客户端（备用翻译服务）
try:
    from openai import OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    if OPENAI_API_KEY and OPENAI_API_KEY != 'your-openai-api-key-here':
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        OPENAI_TRANSLATE_AVAILABLE = True
        print("✅ OpenAI翻译器初始化成功")
    else:
        openai_client = None
        OPENAI_TRANSLATE_AVAILABLE = False
except Exception as e:
    openai_client = None
    OPENAI_TRANSLATE_AVAILABLE = False
    print(f"⚠️  OpenAI翻译器初始化失败: {e}")

# 翻译功能启用状态
TRANSLATION_ENABLED = GOOGLE_TRANSLATE_AVAILABLE or OPENAI_TRANSLATE_AVAILABLE
if TRANSLATION_ENABLED:
    print(f"✅ 翻译功能已启用 (Google: {GOOGLE_TRANSLATE_AVAILABLE}, OpenAI: {OPENAI_TRANSLATE_AVAILABLE})")
else:
    print("⚠️  翻译功能未启用，文章将保持原文")

# ==================== 配置部分 ====================

# RSS订阅源列表
RSS_FEEDS = [
    'https://openai.com/blog/rss.xml',  # OpenAI Blog
    'https://blog.google/technology/ai/rss/',  # Google AI
    'https://www.anthropic.com/rss',  # Anthropic
    'https://feeds.feedburner.com/oreilly/radar',  # O'Reilly AI
    'https://www.qbitai.com/feed',  # 量子位
]

# 新闻API配置 (需要申请免费的API密钥)
# NewsAPI: https://newsapi.org/
# GNews: https://gnews.io/
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')  # 从环境变量获取
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# 爬取的网站列表
WEBSITES_TO_SCRAPE = [
    {
        'name': '机器之心',
        'url': 'https://www.jiqizhixin.com',
        'list_selector': '.article-item',
        'title_selector': '.article-title',
        'link_selector': 'a'
    }
]

# 输出配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, 'ai_articles')
MAX_ARTICLES_PER_SOURCE = 5  # 每个源最多获取多少篇文章
DAYS_TO_FETCH = 7  # 获取最近几天的新闻（改为7天以获取更多内容）

# ==================== 核心功能 ====================

class AINewsFetcher:
    def __init__(self):
        self.articles = []
        self.output_dir = OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.translation_cache = {}  # 翻译缓存，避免重复翻译

    def _is_english(self, text: str) -> bool:
        """检测文本是否主要为英文"""
        if not text:
            return False

        # 移除URL、特殊字符等
        clean_text = re.sub(r'https?://\S+|www\.\S+', '', text)
        clean_text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', clean_text)

        if len(clean_text) == 0:
            return False

        # 计算英文字符比例
        english_chars = sum(1 for c in clean_text if c.isascii() and c.isalpha())
        total_chars = sum(1 for c in clean_text if c.isalpha())

        if total_chars == 0:
            return False

        english_ratio = english_chars / total_chars

        # 如果英文字符超过40%，认为是英文内容
        return english_ratio > 0.4

    def _translate_text(self, text: str, max_retries: int = 2) -> str:
        """翻译文本为中文（优先使用免费Google翻译）"""
        if not text or not TRANSLATION_ENABLED:
            return text

        # 检查是否需要翻译
        if not self._is_english(text):
            return text

        # 检查缓存
        cache_key = hash(text)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        translated_text = text  # 默认返回原文

        # 优先使用Google翻译（免费）
        if GOOGLE_TRANSLATE_AVAILABLE:
            try:
                result = google_translator.translate(text, src='en', dest='zh-cn')
                if result and result.text:
                    translated_text = result.text
                    self.translation_cache[cache_key] = translated_text
                    print(f"  🌐 [Google] 已翻译: {text[:50]}...")
                    return translated_text
            except Exception as e:
                print(f"  ⚠️  Google翻译失败: {str(e)}")

        # 如果Google翻译失败，尝试OpenAI（需要付费）
        if OPENAI_TRANSLATE_AVAILABLE and translated_text == text:
            try:
                for attempt in range(max_retries):
                    try:
                        response = openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "你是一个专业的翻译助手。请将以下英文文本翻译成中文。要求：1.保持专业术语的准确性 2.保持原意不变 3.语言流畅自然 4.只返回翻译结果，不要添加任何解释。"},
                                {"role": "user", "content": text}
                            ],
                            temperature=0.3,
                            max_tokens=1000
                        )

                        translated_text = response.choices[0].message.content.strip()
                        self.translation_cache[cache_key] = translated_text
                        print(f"  🌐 [OpenAI] 已翻译: {text[:50]}...")
                        return translated_text

                    except Exception as e:
                        if attempt < max_retries - 1:
                            print(f"  ⚠️  OpenAI翻译失败，重试中... ({attempt + 1}/{max_retries})")
                            continue
                        else:
                            print(f"  ⚠️  OpenAI翻译失败: {str(e)}")
                            break

            except Exception as e:
                print(f"  ⚠️  OpenAI翻译出错: {str(e)}")

        # 如果所有翻译都失败，返回原文
        print(f"  ⚠️  翻译失败，保留原文: {text[:50]}...")
        return text

    def _translate_article(self, article: Dict) -> Dict:
        """翻译文章的标题和简介"""
        if not TRANSLATION_ENABLED:
            return article

        translated_article = article.copy()

        # 翻译标题
        if self._is_english(article.get('title', '')):
            translated_title = self._translate_text(article['title'])
            translated_article['title'] = translated_title

        # 翻译简介
        if self._is_english(article.get('summary', '')):
            translated_summary = self._translate_text(article['summary'])
            translated_article['summary'] = translated_summary

        return translated_article

    def fetch_from_rss(self) -> List[Dict]:
        """从RSS订阅获取新闻"""
        print("📡 正在从RSS源获取新闻...")
        articles = []

        for feed_url in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_url)
                source_name = feed.feed.get('title', feed_url)

                for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
                    # 过滤最近几天的新闻
                    published = entry.get('published_parsed')
                    if published:
                        pub_date = datetime(*published[:6])
                        if pub_date < datetime.now() - timedelta(days=DAYS_TO_FETCH):
                            continue

                    # 获取简介，优先使用description，如果没有则尝试获取文章内容
                    description = entry.get('description', entry.get('summary', ''))

                    # 先清理description
                    summary = self._clean_html(description)

                    # 如果简介太短，尝试获取文章内容
                    if len(summary) < 50:
                        article_url = entry.get('link', '')
                        if article_url:
                            full_content = self._fetch_article_content(article_url, max_length=200)
                            if full_content and len(full_content) > len(summary):
                                # 清理获取到的完整内容
                                summary = self._clean_html(full_content)

                    # 确保不为空
                    if not summary or len(summary.strip()) == 0:
                        summary = '暂无简介'

                    article = {
                        'title': entry.get('title', '无标题'),
                        'link': entry.get('link', ''),
                        'summary': summary,
                        'published': entry.get('published', '未知时间'),
                        'source': f"RSS - {source_name}"
                    }

                    # 翻译英文内容
                    article = self._translate_article(article)

                    articles.append(article)
                    print(f"  ✓ {article['title'][:50]}...")

            except Exception as e:
                print(f"  ✗ 获取RSS失败 {feed_url}: {str(e)}")

        return articles

    def fetch_from_news_api(self) -> List[Dict]:
        """从新闻API获取AI相关新闻"""
        if not NEWS_API_KEY:
            print("⚠️  未配置NEWS_API_KEY，跳过API获取")
            return []

        print("🔍 正在从新闻API获取AI动态...")
        articles = []

        try:
            # 计算时间范围
            from_date = (datetime.now() - timedelta(days=DAYS_TO_FETCH)).strftime('%Y-%m-%d')

            params = {
                'q': 'AI OR artificial intelligence OR machine learning OR deep learning OR LLM OR GPT',
                'language': 'zh,en',
                'sortBy': 'publishedAt',
                'from': from_date,
                'apiKey': NEWS_API_KEY,
                'pageSize': MAX_ARTICLES_PER_SOURCE
            }

            response = requests.get(NEWS_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            for item in data.get('articles', [])[:MAX_ARTICLES_PER_SOURCE]:
                article = {
                    'title': item.get('title', '无标题'),
                    'link': item.get('url', ''),
                    'summary': item.get('description', ''),
                    'published': item.get('publishedAt', '未知时间'),
                    'source': f"API - {item.get('source', {}).get('name', '未知来源')}"
                }

                # 翻译英文内容
                article = self._translate_article(article)

                articles.append(article)
                print(f"  ✓ {article['title'][:50]}...")

        except Exception as e:
            print(f"  ✗ 获取API新闻失败: {str(e)}")

        return articles

    def scrape_websites(self) -> List[Dict]:
        """爬取指定网站的AI新闻"""
        print("🕷️  正在爬取网站新闻...")
        articles = []

        for site in WEBSITES_TO_SCRAPE:
            try:
                response = requests.get(site['url'], timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')
                items = soup.select(site['list_selector'])

                for item in items[:MAX_ARTICLES_PER_SOURCE]:
                    title_elem = item.select_one(site['title_selector'])
                    link_elem = item.select_one(site['link_selector'])

                    if title_elem and link_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href', '')

                        # 处理相对链接
                        if link and not link.startswith('http'):
                            link = site['url'] + link

                        # 获取文章摘要，优先从页面元素获取
                        summary_elem = item.select_one('.summary, .description, .excerpt, .content-preview')
                        summary = summary_elem.get_text(strip=True) if summary_elem else ''

                        # 如果没有找到摘要，或者摘要太短，尝试获取文章内容
                        if not summary or len(summary) < 50:
                            summary = self._fetch_article_content(link, max_length=200)

                        # 如果还是没有，使用标题
                        if not summary:
                            summary = title

                        # 确保不超过200字
                        if len(summary) > 200:
                            summary = summary[:197] + '...'

                        article = {
                            'title': title,
                            'link': link,
                            'summary': summary,
                            'published': datetime.now().strftime('%Y-%m-%d'),
                            'source': f"爬取 - {site['name']}"
                        }

                        # 翻译英文内容
                        article = self._translate_article(article)

                        articles.append(article)
                        print(f"  ✓ {article['title'][:50]}...")

            except Exception as e:
                print(f"  ✗ 爬取网站失败 {site['name']}: {str(e)}")

        return articles

    def _clean_html(self, html_content: str) -> str:
        """清理HTML标签，保留纯文本，限制在200字以内"""
        if not html_content:
            return ''

        # 先移除不规范的HTML标签（如"< img"）
        text = re.sub(r'<\s*img[^>]*>', '', html_content, flags=re.IGNORECASE)

        # 清理HTML标签
        soup = BeautifulSoup(text, 'html.parser')

        # 移除所有图片标签（双重保险）
        for img in soup.find_all('img'):
            img.decompose()

        text = soup.get_text(strip=True)

        # 清理常见的无关信息（按顺序处理）
        # 1. 移除日期时间
        text = re.sub(r'\d{4}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{1,2}:\d{1,2}', '', text)
        # 2. 移除来源标记（只移除"来源：量子位"这几个字）
        text = re.sub(r'来源[:：]\s*量子位', '', text)
        # 3. 移除作者信息（包括作者名和"发自"等）
        text = re.sub(r'(允中|听雨|克雷西|West|侧写|明明)\s+发自\s+凹非寺', '', text)
        text = re.sub(r'(允中|听雨|克雷西|West|侧写|明明)\s+', '', text)
        text = re.sub(r'发自\s+凹非寺', '', text)
        # 4. 移除公众号信息
        text = re.sub(r'量子位\.?公众号|QbitAI', '', text)
        text = re.sub(r'量子位\s+的朋友们', '', text)

        # 移除多余的空白字符和分隔符
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[·|\-]\s*', ' ', text)
        text = text.strip()

        # 限制在200字以内
        if len(text) > 200:
            text = text[:197] + '...'

        return text

    def _fetch_article_content(self, url: str, max_length: int = 500) -> str:
        """尝试获取文章正文内容"""
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 先移除所有图片标签
            for tag in soup.find_all('img'):
                tag.decompose()

            # 移除不需要的标签
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()

            # 尝试找到主要内容区域
            content_selectors = [
                'article',
                '[role="article"]',
                '.post-content',
                '.article-content',
                '.entry-content',
                '.content',
                'main',
                '.post-body',
                '#content'
            ]

            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break

            if not content:
                # 如果没找到主要内容区域，使用body
                content = soup.get_text(strip=True)

            # 清理和截断
            content = re.sub(r'\s+', ' ', content)
            if len(content) > max_length:
                content = content[:max_length-3] + '...'

            return content

        except Exception as e:
            return ''

    def send_to_feishu(self, article_count: int, filename: str):
        """发送文章到飞书"""
        try:
            # 读取文章内容
            with open(filename, 'r', encoding='utf-8') as f:
                article_content = f.read()

            date_str = datetime.now().strftime('%Y年%m月%d日')
            time_str = datetime.now().strftime('%H:%M')

            message = f"""📰 AI动态日报

📅 日期: {date_str} {time_str}
📊 文章数: {article_count}篇

{article_content}"""

            # 使用openclaw发送到飞书
            # 注意：需要先通过 openclaw channels login --channel feishu 登录飞书
            # 如果gateway未运行，会尝试使用本地模式
            result = subprocess.run(
                [
                    'openclaw', 'agent',
                    '--agent', 'main',
                    '--message', message,
                    '--local',  # 使用本地模式，不需要gateway
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("✅ 已通过本地模式发送AI动态日报")
            else:
                # 如果失败，尝试使用gateway模式（需要gateway运行）
                result2 = subprocess.run(
                    [
                        'openclaw', 'agent',
                        '--agent', 'main',
                        '--message', message,
                        '--channel', 'feishu',
                        '--deliver'
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result2.returncode == 0:
                    print("✅ 已发送AI动态日报到飞书")
                else:
                    print(f"⚠️  飞书通知发送失败（可能需要启动gateway或检查配置）")
                    # 只打印简要错误，不显示完整的错误堆栈
                    if "gateway" in result2.stderr.lower():
                        print(f"   提示: 如需发送到飞书，请先启动openclaw gateway")

        except FileNotFoundError:
            print("⚠️  找不到文章文件，跳过飞书推送")
        except subprocess.TimeoutExpired:
            print("⚠️  飞书通知发送超时")
        except Exception as e:
            print(f"⚠️  飞书通知发送出错: {str(e)}")

    def generate_markdown(self, articles: List[Dict]) -> str:
        """生成Markdown格式的文章"""
        # 按来源和时间排序
        articles.sort(key=lambda x: (x['source'], x['published']), reverse=True)

        # 生成文件名
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"{self.output_dir}/ai_news_{date_str}.md"

        # 生成文章内容
        md_content = f"""# AI动态日报

**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}
**文章数量**: {len(articles)}篇

---

## 📊 今日概览

本日报收集了来自多个来源的最新AI动态，包括OpenAI、Google、Anthropic等官方动态，以及机器之心、量子位等AI媒体的最新报道。

---

## 🔥 热门资讯

"""

        # 按来源分组
        source_groups = {}
        for article in articles:
            source = article['source']
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(article)

        # 生成各个来源的内容
        for source, source_articles in source_groups.items():
            md_content += f"\n### {source}\n\n"

            for i, article in enumerate(source_articles, 1):
                md_content += f"#### {i}. {article['title']}\n\n"
                md_content += f"**时间**: {article['published']}\n\n"
                md_content += f"**简介**: {article['summary']}\n\n"
                md_content += f"**链接**: [{article['link']}]({article['link']})\n\n"
                md_content += "---\n\n"

        # 添加页脚
        md_content += f"""
---

## 📝 说明

本文由AI News Fetcher自动生成，数据来源包括：
- RSS订阅源
- 新闻API
- 网站爬取

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return md_content

    def run(self):
        """执行完整的抓取流程"""
        print("=" * 60)
        print("🤖 AI News Fetcher 开始运行")
        print("=" * 60)

        # 从各个来源获取新闻
        all_articles = []

        # 1. RSS订阅
        all_articles.extend(self.fetch_from_rss())

        # 2. 新闻API
        all_articles.extend(self.fetch_from_news_api())

        # 3. 网站爬取
        all_articles.extend(self.scrape_websites())

        # 去重（基于标题相似度）
        all_articles = self._deduplicate_articles(all_articles)

        print(f"\n📊 总共获取 {len(all_articles)} 篇文章")

        if all_articles:
            # 生成Markdown文章
            md_content = self.generate_markdown(all_articles)

            # 保存文件
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"{self.output_dir}/ai_news_{date_str}.md"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"\n✅ 文章已生成: {filename}")
            print(f"📂 保存位置: {os.path.abspath(filename)}")

            # 发送到飞书
            print("\n📤 正在发送通知到飞书...")
            self.send_to_feishu(len(all_articles), os.path.abspath(filename))
        else:
            print("\n⚠️  未获取到任何文章")

        print("=" * 60)

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """简单的去重逻辑"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            # 简单的标题标准化
            title = article['title'].lower().strip()
            title_hash = hash(title)

            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_articles.append(article)

        if len(unique_articles) < len(articles):
            print(f"  🔍 去重后保留 {len(unique_articles)} 篇文章（原 {len(articles)} 篇）")

        return unique_articles

# ==================== 主程序 ====================

if __name__ == '__main__':
    fetcher = AINewsFetcher()
    fetcher.run()
