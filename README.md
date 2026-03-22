# AI News Fetcher

自动获取最新AI动态并生成Markdown文章的Python脚本。

## 功能特性

- 📡 **RSS订阅**: 从OpenAI、Google、Anthropic等官方博客获取最新动态
- 🔍 **新闻API**: 通过NewsAPI获取AI相关新闻报道
- 🕷️ **网页爬取**: 爬取机器之心、量子位等AI媒体网站
- 📝 **自动生成**: 生成格式化的Markdown日报
- 🔄 **定时运行**: 支持cron定时任务自动执行

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置说明

### 1. 配置新闻API（可选）

如果需要使用NewsAPI，需要申请免费的API密钥：

1. 访问 https://newsapi.org/ 注册账号
2. 获取API密钥
3. 设置环境变量：

```bash
# 临时设置
export NEWS_API_KEY='your-api-key-here'

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo "export NEWS_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

### 2. 自定义数据源

编辑 `ai_news_fetcher.py` 文件中的配置部分：

```python
# RSS订阅源列表
RSS_FEEDS = [
    'https://openai.com/blog/rss.xml',
    # 添加你想要的RSS源
]

# 爬取的网站列表
WEBSITES_TO_SCRAPE = [
    {
        'name': '网站名称',
        'url': 'https://example.com',
        'list_selector': '.article-list',  # 文章列表选择器
        'title_selector': '.title',         # 标题选择器
        'link_selector': 'a'                # 链接选择器
    }
]
```

### 3. 输出配置

```python
OUTPUT_DIR = './ai_articles'  # 文章保存目录
MAX_ARTICLES_PER_SOURCE = 5   # 每个源最多获取文章数
DAYS_TO_FETCH = 1             # 获取最近几天的新闻
```

## 使用方法

### 手动运行

```bash
python ai_news_fetcher.py
```

### 设置定时任务（Cron）

编辑crontab：

```bash
crontab -e
```

添加定时任务（例如每天早上9点运行）：

```bash
# 每天早上9点运行
0 9 * * * cd /Users/luojie/workspace/scrpit && /usr/bin/python3 ai_news_fetcher.py >> ai_news.log 2>&1

# 或者每天早上8点和下午6点各运行一次
0 8,18 * * * cd /Users/luojie/workspace/scrpit && /usr/bin/python3 ai_news_fetcher.py >> ai_news.log 2>&1
```

查看cron日志：

```bash
tail -f ai_news.log
```

## 输出示例

生成的文章会保存在 `ai_articles/` 目录下，文件名格式为 `ai_news_YYYYMMDD.md`：

```
ai_articles/
├── ai_news_20250322.md
├── ai_news_20250321.md
└── ai_news_20250320.md
```

## 高级功能

### 添加新的数据源

#### RSS源
直接将RSS URL添加到 `RSS_FEEDS` 列表即可。

#### 网站爬取
1. 访问目标网站
2. 使用浏览器开发者工具查看文章列表的HTML结构
3. 找到文章列表项、标题和链接的CSS选择器
4. 添加到 `WEBSITES_TO_SCRAPE` 列表

示例：

```python
{
    'name': '新网站',
    'url': 'https://example.com',
    'list_selector': 'div.article-item',  # 每篇文章的容器
    'title_selector': 'h2.title',         # 标题元素
    'link_selector': 'a'                  # 链接元素
}
```

### 自定义文章模板

修改 `generate_markdown()` 方法来自定义文章的格式和结构。

## 故障排查

### RSS获取失败
- 检查网络连接
- 确认RSS URL是否正确
- 某些RSS可能需要设置User-Agent

### API请求失败
- 检查API密钥是否正确
- 确认API额度是否用完
- 查看错误日志获取详细信息

### 网站爬取失败
- 网站可能更新了HTML结构，需要更新CSS选择器
- 某些网站有反爬虫机制，可能需要添加headers
- 检查网络连接和超时设置

## 注意事项

- 遵守目标网站的robots.txt规则
- 合理设置请求频率，避免对服务器造成压力
- 定期检查和更新CSS选择器，网站结构可能变化
- NewsAPI免费版有请求限制，请合理使用

## 许可证

MIT License
