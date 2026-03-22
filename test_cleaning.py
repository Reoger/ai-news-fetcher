#!/usr/bin/env python3
"""测试HTML清理功能"""

from bs4 import BeautifulSoup
import re

html_content = """<img id="wx_img" src="https://www.qbitai.com/wp-content/uploads/imgs/qbitai-logo-1.png" width="400" height="400">浙大团队破解多模态模型「盲目自信」：先校准置信度，再分配算力丨CVPR'26听雨2026-03-2215:17:19来源：量子位图都糊成一团了，模型还说"我很确定"？"""

# 清理HTML标签
soup = BeautifulSoup(html_content, 'html.parser')

# 移除所有图片标签
for img in soup.find_all('img'):
    img.decompose()

text = soup.get_text(strip=True)

print("原始文本:")
print(text)
print()

# 清理常见的无关信息（按顺序处理）
# 1. 移除来源信息
text = re.sub(r'来源[:：]\s*量子位.*?(?=\d{4}年|$)', '', text)
print("步骤1（移除来源）:")
print(text)
print()

# 2. 移除作者信息
text = re.sub(r'(允中|听雨|克雷西| West|侧写|明明).*?(?=\d|¥|$)', '', text)
print("步骤2（移除作者）:")
print(text)
print()

# 3. 移除日期时间
text = re.sub(r'\d{4}-\d{1,2}-\d{1,2}\s*\d{1,2}:\d{1,2}:\d{1,2}', '', text)
print("步骤3（移除日期时间）:")
print(text)
print()

# 4. 移除公众号信息
text = re.sub(r'量子位\.?公众号|QbitAI|量子位\s+的头像', '', text)
print("步骤4（移除公众号）:")
print(text)
print()

# 5. 移除"发自"信息
text = re.sub(r'发自\s+凹非寺', '', text)
print("步骤5（移除发自）:")
print(text)
print()

# 6. 移除"量子位"重复
text = re.sub(r'量子位\s+量子位', '量子位', text)
print("步骤6（移除重复）:")
print(text)
print()

# 移除多余的空白字符和分隔符
text = re.sub(r'\s+', ' ', text)
text = re.sub(r'[·|\-]\s*', ' ', text)
text = text.strip()

print("最终结果:")
print(text)
print()
print(f"长度: {len(text)}")
