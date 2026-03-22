#!/bin/bash
# 设置AI News Fetcher的定时任务

echo "🕒 设置AI News Fetcher定时任务..."
echo "=================================="

# 获取当前crontab内容
current_cron=$(crontab -l 2>/dev/null || echo "")

# 检查是否已经存在AI News Fetcher的任务
if echo "$current_cron" | grep -q "ai_news_fetcher.py"; then
    echo "⚠️  检测到已存在AI News Fetcher的定时任务"
    echo ""
    echo "当前任务:"
    echo "$current_cron" | grep "ai_news_fetcher.py"
    echo ""
    read -p "是否要删除现有任务并重新设置？(y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 取消设置"
        exit 1
    fi
    # 删除现有任务
    current_cron=$(echo "$current_cron" | grep -v "ai_news_fetcher.py")
fi

# Python路径
PYTHON_PATH=$(which python3)
SCRIPT_DIR="/Users/luojie/workspace/scrpit"
LOG_FILE="$SCRIPT_DIR/ai_news.log"

# 新的定时任务
# 每天9点运行
new_task="0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH ai_news_fetcher.py >> $LOG_FILE 2>&1"

# 添加到crontab
echo ""
echo "📋 将添加以下定时任务:"
echo "$new_task"
echo ""

# 合并现有任务和新任务
(crontab -l 2>/dev/null || echo ""; echo "$new_task") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ 定时任务设置成功！"
    echo ""
    echo "📅 当前所有定时任务:"
    crontab -l
    echo ""
    echo "📝 日志文件: $LOG_FILE"
    echo "⏰ 运行时间: 每天早上9:00"
    echo ""
    echo "🔍 查看日志命令:"
    echo "   tail -f $LOG_FILE"
    echo ""
    echo "🗑️  删除定时任务命令:"
    echo "   crontab -e"
    echo "   然后删除包含 ai_news_fetcher.py 的行"
else
    echo "❌ 定时任务设置失败"
    exit 1
fi
