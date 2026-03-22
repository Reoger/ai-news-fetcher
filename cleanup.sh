#!/bin/bash
# 清理测试脚本

echo "🧹 清理测试文件..."

# 删除测试脚本
rm -f test_api.py test_qbitai.py

echo "✅ 清理完成！"
echo ""
echo "保留的文件:"
ls -lh *.py *.sh *.md 2>/dev/null | grep -v total
