# 快速开始指南

## 5分钟快速上手

### 第一步：安装依赖

```bash
# 方式1: 使用一键安装脚本
bash install.sh

# 方式2: 手动安装
pip3 install -r requirements.txt
```

### 第二步：配置（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加NEWS_API_KEY（如果需要）
# 可以在 https://newsapi.org/ 免费申请API密钥
```

### 第三步：测试运行

```bash
# 运行测试，验证各功能
python3 test_fetcher.py

# 直接运行脚本
python3 ai_news_fetcher.py
```

### 第四步：查看结果

```bash
# 查看生成的文章
ls -la ai_articles/

# 阅读文章
cat ai_articles/ai_news_$(date +%Y%m%d).md
```

### 第五步：设置定时任务

```bash
# 编辑crontab
crontab -e

# 添加以下内容（每天早上9点运行）
0 9 * * * cd /Users/luojie/workspace/scrpit && /usr/bin/python3 ai_news_fetcher.py >> ai_news.log 2>&1

# 查看已设置的定时任务
crontab -l
```

## 自定义配置

### 修改RSS源

编辑 `ai_news_fetcher.py`：

```python
RSS_FEEDS = [
    'https://openai.com/blog/rss.xml',
    'https://your-rss-source.com/feed',  # 添加你的RSS源
]
```

### 添加爬取网站

1. 访问目标网站
2. 使用浏览器开发者工具（F12）查看HTML结构
3. 找到文章列表、标题、链接的CSS选择器
4. 添加到配置：

```python
WEBSITES_TO_SCRAPE = [
    {
        'name': '网站名称',
        'url': 'https://example.com',
        'list_selector': '.article-item',
        'title_selector': 'h2.title',
        'link_selector': 'a'
    }
]
```

### 调整获取范围

```python
MAX_ARTICLES_PER_SOURCE = 10  # 增加到每个源10篇文章
DAYS_TO_FETCH = 2             # 获取最近2天的新闻
OUTPUT_DIR = './my_articles'   # 修改输出目录
```

## 常见问题

### Q: 为什么RSS获取不到内容？
A: 检查网络连接，确认RSS URL是否可访问。某些RSS可能有访问限制。

### Q: 爬取网站失败怎么办？
A:
1. 网站可能更新了HTML结构，需要更新CSS选择器
2. 检查是否有反爬虫机制（如Cloudflare）
3. 尝试添加User-Agent（脚本已包含）

### Q: 如何只获取特定主题的新闻？
A: 修改 `fetch_from_news_api()` 中的搜索关键词：

```python
'q': 'GPT OR ChatGPT OR LLM',  # 修改为特定主题
```

### Q: 生成的文章太长/太短？
A: 调整 `MAX_ARTICLES_PER_SOURCE` 参数，减少或增加每个源的文章数量。

## 进阶功能

### 使用AI生成摘要

可以使用Claude/GPT API为每篇文章生成更详细的摘要：

```python
# 在 generate_markdown() 中添加AI摘要功能
def generate_ai_summary(self, article_text):
    # 调用Claude API生成摘要
    # 需要安装 anthropic 包
    pass
```

### 自动发布到博客

扩展脚本，将生成的Markdown自动发布到：
- GitHub Pages
- WordPress
- Ghost
- Notion

### 添加通知功能

```python
# 文章生成后发送通知
def send_notification(self, filename):
    # 发送邮件
    # 发送到微信/Telegram/Slack
    pass
```

## 项目结构

```
.
├── ai_news_fetcher.py      # 主脚本
├── test_fetcher.py          # 测试脚本
├── install.sh               # 安装脚本
├── requirements.txt         # 依赖列表
├── .env.example             # 环境变量模板
├── crontab.example          # Cron配置示例
├── README.md                # 详细说明
├── CLAUDE.md                # 项目架构说明
├── QUICKSTART.md            # 本文件
├── .gitignore               # Git忽略文件
└── ai_articles/             # 生成的文章目录
    └── ai_news_YYYYMMDD.md
```

## 获取帮助

- 运行测试: `python3 test_fetcher.py`
- 查看日志: `tail -f ai_news.log`
- 检查配置: 确认 `ai_news_fetcher.py` 中的配置项
