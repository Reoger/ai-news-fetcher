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
import shutil
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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

# GitHub配置
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # GitHub Personal Access Token（可选，提高API限制）
GITHUB_SEARCH_QUERIES = [
    'LLM OR "large language model"',
    'machine learning',
    'AI OR artificial intelligence',
    'multimodal OR "computer vision"',
    'langchain OR "vector database"',
]
GITHUB_TRENDING_URL = 'https://github.com/trending'
GITHUB_REPOS_TO_WATCH = [
    'openai/whisper',  # OpenAI语音识别
    'langchain-ai/langchain',  # LangChain框架
    'microsoft/semantic-kernel',  # 微软语义内核
    'TransformerOptimus/SuperAGI',  # AI Agent框架
    ' Vaughnzan/Knowledge-GPT',  # 知识库问答
]

# 飞书配置
FEISHU_CHAT_ID = os.getenv('FEISHU_CHAT_ID', 'oc_76cb06231ced648365fe0bf033e6db15')  # 飞书群聊ID

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

    def fetch_from_github_trending(self) -> List[Dict]:
        """从GitHub Trending获取热门AI项目"""
        print("🔥 正在从GitHub Trending获取热门AI项目...")
        articles = []

        try:
            # 爬取GitHub Trending页面
            response = requests.get(GITHUB_TRENDING_URL, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # 查找所有项目条目
            repo_items = soup.select('article.Box-row')

            for item in repo_items[:MAX_ARTICLES_PER_SOURCE]:
                try:
                    # 获取项目名称和链接
                    title_elem = item.select_one('h2 a')
                    if not title_elem:
                        continue

                    repo_link = title_elem.get('href', '')
                    repo_name = repo_link.strip('/')
                    repo_url = f"https://github.com{repo_link}"

                    # 获取项目描述
                    desc_elem = item.select_one('p')
                    description = desc_elem.get_text(strip=True) if desc_elem else '暂无描述'

                    # 获取编程语言和star数
                    language_elem = item.select_one('span[itemprop="programmingLanguage"]')
                    language = language_elem.get_text(strip=True) if language_elem else 'Unknown'

                    star_elem = item.select_one('a[href$="/stargazers"]')
                    stars = star_elem.get_text(strip=True) if star_elem else '0'

                    # 检查是否为AI相关项目（通过关键词）
                    ai_keywords = ['ai', 'machine learning', 'llm', 'gpt', 'langchain',
                                   'transformer', 'diffusion', 'vision', 'multimodal',
                                   'embedding', 'vector', 'agent', 'chatbot', 'openai',
                                   'hugging', 'anthropic', 'semantic', 'rag', 'inference']

                    text_to_check = f"{repo_name} {description}".lower()
                    if not any(keyword in text_to_check for keyword in ai_keywords):
                        continue

                    article = {
                        'title': f"⭐ {repo_name} ({language}, {stars} stars)",
                        'link': repo_url,
                        'summary': description[:200] + '...' if len(description) > 200 else description,
                        'published': datetime.now().strftime('%Y-%m-%d'),
                        'source': "GitHub - Trending"
                    }

                    # 翻译英文内容
                    article = self._translate_article(article)

                    articles.append(article)
                    print(f"  ✓ {article['title'][:50]}...")

                except Exception as e:
                    continue

        except Exception as e:
            print(f"  ✗ 获取GitHub Trending失败: {str(e)}")

        return articles

    def fetch_from_github_search(self) -> List[Dict]:
        """从GitHub Search API搜索热门AI仓库"""
        print("🔍 正在从GitHub搜索热门AI仓库...")
        articles = []

        # 如果没有token，跳过（API限制太严格）
        if not GITHUB_TOKEN:
            print("  ⚠️  未配置GITHUB_TOKEN，跳过GitHub搜索（可选）")
            return articles

        headers = {'Authorization': f'token {GITHUB_TOKEN}'}

        for query in GITHUB_SEARCH_QUERIES[:2]:  # 只搜索前2个查询，避免超限
            try:
                # 简化查询，只使用python语言，按star数排序
                params = {
                    'q': f'{query} language:python stars:>500',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 3  # 每个查询获取3个结果
                }

                response = requests.get(
                    'https://api.github.com/search/repositories',
                    headers=headers,
                    params=params,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                total = data.get('total_count', 0)
                if total > 0:
                    print(f"  找到 {total} 个相关仓库")

                for item in data.get('items', [])[:3]:
                    # 获取并增强描述
                    original_desc = item.get('description', '')
                    enhanced_summary = self._enhance_github_description(
                        item['name'],
                        item['owner']['login'],
                        original_desc
                    )

                    article = {
                        'title': f"📦 {item['name']} (⭐ {item['stargazers_count']:,})",
                        'link': item['html_url'],
                        'summary': enhanced_summary,
                        'published': item['updated_at'][:10],
                        'source': "GitHub - 热门项目"
                    }

                    # 翻译英文内容
                    article = self._translate_article(article)

                    articles.append(article)
                    print(f"  ✓ {article['title'][:50]}...")

                # 避免API限流
                import time
                time.sleep(1)

            except Exception as e:
                print(f"  ✗ GitHub搜索失败 ({query}): {str(e)}")
                continue

        return articles

    def _enhance_github_description(self, repo_name: str, owner_login: str, original_desc: str) -> str:
        """增强GitHub项目描述，如果描述太短则尝试获取README或添加补充说明"""
        # 如果原描述已经足够长（>80字符），直接使用
        if original_desc and len(original_desc) > 80:
            return original_desc[:200] + ('...' if len(original_desc) > 200 else '')

        # 如果描述太短，尝试获取README的第一段
        if not GITHUB_TOKEN:
            return self._add_fallback_description(repo_name, original_desc)

        try:
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            readme_url = f'https://api.github.com/repos/{owner_login}/{repo_name}/readme'
            response = requests.get(readme_url, headers=headers, timeout=10)

            if response.status_code == 200:
                import base64
                readme_data = response.json()
                # GitHub API返回的是base64编码的内容
                content = base64.b64decode(readme_data['content']).decode('utf-8', errors='ignore')

                # 清理HTML和XML标签
                content = re.sub(r'<[^>]+>', '', content)
                # 移除所有方括号和圆括号（简单但有效）
                content = re.sub(r'\[\[?', '', content)
                content = re.sub(r'\]\]?', ' ', content)
                content = re.sub(r'\([^\)]*\)', ' ', content)
                # 清理markdown标题
                content = re.sub(r'^#+\s+', '', content, flags=re.MULTILINE)
                # 清理特殊符号和HTML实体
                content = re.sub(r'&\w+;', ' ', content)
                content = re.sub(r'\|', '', content)
                content = re.sub(r'\*\*', '', content)
                content = re.sub(r'\*+', '', content)
                content = re.sub(r'_{2,}', '', content)
                content = re.sub(r'`+', '', content)
                # 合并多余空格
                content = re.sub(r'\s+', ' ', content)

                # 提取纯文本段落
                lines = content.split('\n')
                enhanced_desc = ''

                for line in lines[:30]:  # 看前30行
                    line = line.strip()
                    # 跳过标题行（以#开头）、空行、特殊标记
                    if not line or line.startswith('#') or line.startswith('![') or line.startswith('```'):
                        continue

                    enhanced_desc += line + ' '
                    if len(enhanced_desc) > 100:  # 获取足够的内容
                        break

                # 清理多余空格
                enhanced_desc = ' '.join(enhanced_desc.split())

                if len(enhanced_desc) > 50:
                    return enhanced_desc[:200] + ('...' if len(enhanced_desc) > 200 else '')

        except Exception:
            pass

        # 如果所有尝试都失败，使用fallback
        return self._add_fallback_description(repo_name, original_desc)

    def _add_fallback_description(self, repo_name: str, original_desc: str) -> str:
        """为描述太短的项目添加fallback说明"""
        if not original_desc:
            original_desc = '暂无描述'

        # 常见AI项目的补充说明
        fallbacks = {
            'langchain': ' - 用于构建LLM应用的框架，支持链式调用、Agent、工具集成等功能',
            'transformers': ' - Hugging Face的深度学习框架，支持PyTorch、TensorFlow和JAX',
            'autogpt': ' - 自主AI代理，可以自动完成复杂任务的AI助手',
            'whisper': ' - OpenAI的语音识别系统，支持多语言转录和翻译',
            'stable-diffusion': ' - 文本生成图像的AI模型，可生成高质量图片',
            'semantic-kernel': ' - 微软的AI编排框架，集成LLM到应用中',
        }

        # 检查是否匹配已知项目
        for key, fallback in fallbacks.items():
            if key.lower() in repo_name.lower():
                enhanced = original_desc + fallback
                return enhanced[:200] + ('...' if len(enhanced) > 200 else '')

        # 通用补充
        if len(original_desc) < 50:
            enhanced = original_desc + ' - AI/Machine Learning相关项目'
            return enhanced[:200]

        return original_desc[:200] + ('...' if len(original_desc) > 200 else '')

    def fetch_from_github_repos(self) -> List[Dict]:
        """监控重点AI仓库的更新"""
        print("👀 正在检查重点AI仓库的更新...")
        articles = []

        if not GITHUB_TOKEN:
            print("  ⚠️  未配置GITHUB_TOKEN，使用基础检查...")

        for repo_path in GITHUB_REPOS_TO_WATCH[:3]:  # 只检查前3个
            try:
                headers = {}
                if GITHUB_TOKEN:
                    headers['Authorization'] = f'token {GITHUB_TOKEN}'

                # 获取仓库信息
                response = requests.get(
                    f'https://api.github.com/repos/{repo_path}',
                    headers=headers,
                    timeout=10
                )

                if response.status_code == 404:
                    continue
                response.raise_for_status()

                repo_data = response.json()

                # 检查最近7天是否有更新
                from datetime import timedelta
                updated_at = datetime.strptime(repo_data['updated_at'], '%Y-%m-%dT%H:%M:%SZ')
                if updated_at < datetime.now() - timedelta(days=DAYS_TO_FETCH):
                    continue

                # 获取最新release
                release_response = requests.get(
                    f'https://api.github.com/repos/{repo_path}/releases/latest',
                    headers=headers,
                    timeout=10
                )

                release_info = ''
                if release_response.status_code == 200:
                    release_data = release_response.json()
                    if release_data.get('tag_name'):
                        release_info = f" 最新版本: {release_data['tag_name']}"

                article = {
                    'title': f"🚀 {repo_path} 更新{release_info}",
                    'link': repo_data['html_url'],
                    'summary': repo_data.get('description', '暂无描述')[:200],
                    'published': repo_data['updated_at'][:10],
                    'source': "GitHub - 重点关注"
                }

                # 翻译英文内容
                article = self._translate_article(article)

                articles.append(article)
                print(f"  ✓ {article['title'][:50]}...")

            except Exception as e:
                print(f"  ✗ 检查仓库失败 ({repo_path}): {str(e)}")
                continue

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

            # 获取openclaw的绝对路径，避免cron环境下PATH变量问题
            # 优先使用shutil.which，如果找不到则尝试已知的nvm路径
            openclaw_path = shutil.which('openclaw')

            # 如果shutil.which找不到，尝试nvm路径
            if not openclaw_path:
                possible_paths = [
                    os.path.expanduser('~/.nvm/versions/node/v24.14.0/bin/openclaw'),
                    '/Users/luojie/.nvm/versions/node/v24.14.0/bin/openclaw',
                    os.path.expanduser('~/npm-global/bin/openclaw'),
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        openclaw_path = path
                        break

            if not openclaw_path:
                print("⚠️  找不到openclaw命令，跳过飞书推送")
                print(f"   提示: 请确保openclaw已安装或在PATH中")
                print(f"   调试: shutil.which结果: {shutil.which('openclaw')}")
                print(f"   调试: nvm路径存在: {os.path.exists('/Users/luojie/.nvm/versions/node/v24.14.0/bin/openclaw')}")
                return

            # 使用openclaw发送到飞书
            # 使用--channel feishu --deliver实际发送消息
            # 使用--to参数指定目标群聊
            result = subprocess.run(
                [
                    openclaw_path, 'agent',
                    '--agent', 'main',
                    '--to', FEISHU_CHAT_ID,
                    '--message', message,
                    '--channel', 'feishu',
                    '--deliver'
                ],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("✅ 已发送AI动态日报到飞书")
            else:
                print(f"⚠️  飞书通知发送失败")
                # 只打印简要错误
                if result.stderr:
                    error_msg = result.stderr.split('\n')[0] if '\n' in result.stderr else result.stderr
                    print(f"   错误: {error_msg[:100]}")

        except IOError as e:
            # 文件相关的错误（包括文件不存在、无权限等）
            print(f"⚠️  无法读取文章文件: {filename}")
            print(f"   错误: {str(e)}")
        except subprocess.TimeoutExpired:
            print("⚠️  飞书通知发送超时")
        except Exception as e:
            print(f"⚠️  飞书通知发送出错: {type(e).__name__}: {str(e)}")

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

        # 4. GitHub Trending热门AI项目
        all_articles.extend(self.fetch_from_github_trending())

        # 5. GitHub搜索最新AI仓库
        all_articles.extend(self.fetch_from_github_search())

        # 6. GitHub重点仓库监控
        all_articles.extend(self.fetch_from_github_repos())

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
