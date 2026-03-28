#!/bin/bash
# 设置正确的PATH环境变量（包含nvm路径）
export PATH="/usr/local/bin:/usr/bin:/bin:/Users/luojie/.nvm/versions/node/v24.14.0/bin"

cd /Users/luojie/workspace/scrpit

# 清理Python缓存
find . -name "*.pyc" -delete 2>/dev/null
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 运行脚本（使用-B避免生成缓存）
# 注意：保持PATH环境变量传递给Python进程
exec python3 -B ai_news_fetcher.py
