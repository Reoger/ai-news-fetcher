# 🌐 翻译功能配置指南

## ✅ 已完成的功能

- 自动检测英文内容
- 自动翻译为中文
- 支持标题和简介翻译
- 翻译缓存，避免重复翻译
- 集成到自动化流程中

## 🔑 配置OpenAI API密钥

### 第一步：获取API密钥

1. 访问 OpenAI 平台：https://platform.openai.com/api-keys
2. 登录或注册账号
3. 点击 "Create new secret key"
4. 复制生成的API密钥

### 第二步：配置到项目中

```bash
# 编辑 .env 文件
cd /Users/luojie/workspace/scrpit
nano .env  # 或使用你喜欢的编辑器
```

添加以下内容：
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 第三步：测试翻译功能

```bash
# 测试翻译功能
python3 test_translation.py
```

## 📊 翻译功能说明

### 自动翻译范围
- ✅ 文章标题（英文）
- ✅ 文章简介（英文）
- ✅ 保持链接原样
- ✅ 中文内容不翻译

### 翻译质量
- 使用 OpenAI GPT-3.5-turbo 模型
- 保持专业术语准确性
- 语言流畅自然
- 保持原意不变

### 性能优化
- 翻译缓存：相同内容不重复翻译
- 智能检测：只翻译英文内容
- 错误重试：失败时自动重试2次
- 失败保护：翻译失败时保留原文

## 🚀 自动化运行

### 已集成到定时任务
```bash
# 每天早上9点自动运行
# 包括：
# 1. 抓取最新AI动态
# 2. 自动翻译英文内容 ✅ 新增
# 3. 生成Markdown文章
# 4. 发送到飞书
```

### 手动运行
```bash
python3 ai_news_fetcher.py
```

## 📝 示例对比

### 之前（英文）
```markdown
#### 1. Introducing GPT-5.4 mini and nano

**时间**: Tue, 17 Mar 2026 10:00:00 GMT
**简介**: GPT 5.4 mini and nano are smaller, faster versions of GPT 5.4 optimized for coding, tool use, multimodal reasoning, and high volume API and sub agent workloads.
```

### 现在（中文翻译）
```markdown
#### 1. 介绍 GPT-5.4 mini 和 nano

**时间**: Tue, 17 Mar 2026 10:00:00 GMT
**简介**: GPT 5.4 mini 和 nano 是 GPT 5.4 的更小、更快的版本，针对编程、工具使用、多模态推理以及大容量API和子代理工作负载进行了优化。
```

## 💰 费用说明

### OpenAI API定价
- **模型**: gpt-3.5-turbo
- **输入**: $0.50 / 1M tokens
- **输出**: $1.50 / 1M tokens

### 估算成本
- 每篇文章翻译约：100-200 tokens
- 每天约10篇文章：约2,000 tokens
- **每月成本**：约 $0.003 (3美分)

## ⚙️ 配置选项

### 调整翻译行为
在 `ai_news_fetcher.py` 中可以调整：

```python
# 英文检测阈值（默认0.4，即40%英文）
english_ratio = 0.4

# 翻译重试次数（默认2次）
max_retries = 2

# 使用的模型（默认gpt-3.5-turbo）
model="gpt-3.5-turbo"
```

## 🛠️ 故障排查

### 翻译功能未启用
```
⚠️  未配置OPENAI_API_KEY，翻译功能已禁用
```
**解决方法**: 检查 .env 文件中的 API 密钥配置

### 翻译失败
```
⚠️  翻译失败: ...
```
**可能原因**:
1. API密钥无效或过期
2. 网络连接问题
3. API额度用完

**解决方法**:
1. 检查API密钥是否正确
2. 检查网络连接
3. 查看OpenAI账户余额

### 翻译质量不满意
**解决方法**:
1. 可以调整翻译prompt（在_translate_text方法中）
2. 升级到GPT-4模型（修改model参数）

## 📋 检查清单

- [ ] 获取OpenAI API密钥
- [ ] 配置到.env文件
- [ ] 运行测试脚本验证
- [ ] 手动运行主脚本测试
- [ ] 检查生成的文章是否翻译
- [ ] 确认定时任务正常

---

**状态**: ✅ 功能已开发完成，等待配置API密钥

**下一步**: 配置API密钥后，每天自动运行的AI动态日报将包含翻译后的中文内容
