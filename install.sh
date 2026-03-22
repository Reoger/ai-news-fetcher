#!/bin/bash
# AI News Fetcher 安装脚本

echo "🤖 AI News Fetcher 安装向导"
echo "=========================="

# 检查Python版本
echo "📋 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装Python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ 找到: $PYTHON_VERSION"

# 安装依赖
echo ""
echo "📦 安装Python依赖包..."
pip3 install -r requirements.txt

# 创建输出目录
echo ""
echo "📁 创建输出目录..."
mkdir -p ai_articles

# 复制环境变量示例
echo ""
echo "⚙️  配置环境变量..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo "⚠️  请编辑 .env 文件添加你的NEWS_API_KEY（可选）"
else
    echo "ℹ️  .env 文件已存在"
fi

# 设置执行权限
echo ""
echo "🔐 设置脚本执行权限..."
chmod +x ai_news_fetcher.py

# 测试运行
echo ""
echo "🧪 测试运行脚本..."
echo "=========================="
python3 ai_news_fetcher.py

echo ""
echo "=========================="
echo "✅ 安装完成！"
echo ""
echo "📝 后续步骤:"
echo "1. (可选) 编辑 .env 文件添加NEWS_API_KEY"
echo "2. (可选) 编辑 ai_news_fetcher.py 自定义数据源"
echo "3. 运行脚本: python3 ai_news_fetcher.py"
echo "4. 设置定时任务: crontab -e"
echo ""
echo "查看生成的文章: ls -la ai_articles/"
