# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News Fetcher - 一个自动获取最新AI动态并生成Markdown文章的Python脚本。支持多种数据源：RSS订阅、新闻API、网页爬取。可通过cron定时任务自动执行。

## Development Commands

- **安装依赖**: `pip install -r requirements.txt`
- **运行脚本**: `python3 ai_news_fetcher.py`
- **测试功能**: `python3 test_fetcher.py`
- **一键安装**: `bash install.sh`
- **查看生成的文章**: `ls -la ai_articles/`

## Architecture

### 核心文件

- `ai_news_fetcher.py` - 主脚本，包含 AINewsFetcher 类
  - `fetch_from_rss()` - 从RSS订阅获取新闻
  - `fetch_from_news_api()` - 从NewsAPI获取AI新闻
  - `scrape_websites()` - 爬取指定网站的新闻
  - `generate_markdown()` - 生成Markdown格式文章
  - `run()` - 执行完整的抓取流程

- `test_fetcher.py` - 测试脚本，验证各数据源功能
- `install.sh` - 一键安装脚本
- `crontab.example` - Cron定时任务配置示例

### 配置部分

在 `ai_news_fetcher.py` 顶部配置：
- `RSS_FEEDS` - RSS订阅源列表
- `WEBSITES_TO_SCRAPE` - 要爬取的网站列表（包含CSS选择器）
- `OUTPUT_DIR` - 文章保存目录（默认: `./ai_articles`）
- `MAX_ARTICLES_PER_SOURCE` - 每个源最多获取文章数（默认: 5）
- `DAYS_TO_FETCH` - 获取最近几天的新闻（默认: 1）

### 输出结构

```
ai_articles/
├── ai_news_20250322.md
├── ai_news_20250321.md
└── ...
```

## Important Notes

### 环境变量

- `NEWS_API_KEY` - NewsAPI的密钥（可选，从 https://newsapi.org/ 获取）
  - 可在 `.env` 文件中设置
  - 也可直接设置系统环境变量

### 依赖包

- `feedparser` - 解析RSS订阅
- `requests` - HTTP请求
- `beautifulsoup4` - HTML解析
- `lxml` - XML/HTML解析器

### 网站爬取配置

添加新网站时需要提供CSS选择器：
```python
{
    'name': '网站名称',
    'url': 'https://example.com',
    'list_selector': '.article-item',  # 文章列表容器
    'title_selector': '.title',         # 标题元素
    'link_selector': 'a'                # 链接元素
}
```

### 常见问题

1. **RSS获取失败**: 检查网络连接和RSS URL是否正确
2. **API请求失败**: 检查API密钥和额度限制
3. **网站爬取失败**: 网站可能更新了HTML结构，需要更新CSS选择器
4. **Cron不执行**: 检查python3路径和脚本路径是否正确

### 扩展建议

- 添加更多RSS源和爬取网站
- 实现文章去重和相似度检测
- 添加文章内容摘要生成（可使用AI API）
- 支持多语言翻译
- 添加邮件/微信通知功能
