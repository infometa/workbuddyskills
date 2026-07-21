# Plugin Finder 使用指南

本指南提供 plugin-finder 的详细使用说明和最佳实践。

## 快速开始

### 1. 安装验证

重启 CodeBuddy Code 后，验证插件已加载：

```bash
/plugin list
```

应该看到：
```
plugin-finder@local-dev
  智能插件发现和管理助手 - 帮助用户从插件市场中发现、安装和比较插件
```

### 2. 第一次使用

尝试搜索插件：

```bash
/plugin-finder:search "代码审查"
```

系统会：
1. AI 理解您的需求
2. 搜索所有 marketplace
3. 展示相关插件列表（可多选）
4. 批量安装您选择的插件
5. 提醒您重启 CodeBuddy Code

## 核心功能

### 🔍 智能搜索插件

**命令：** `/plugin-finder:search [需求描述]`

**用法示例：**

```bash
# 搜索代码审查工具
/plugin-finder:search "代码审查"

# 搜索测试工具
/plugin-finder:search "自动化测试"

# 搜索部署相关
/plugin-finder:search "deployment tools"

# 搜索数据库工具
/plugin-finder:search "数据库管理"
```

**工作流程：**
1. 输入需求描述（中英文均可）
2. AI 语义理解您的需求
3. 匹配所有已添加 marketplace 中的插件
4. 按相关度排序展示结果
5. 多选您想安装的插件
6. 自动批量安装

**匹配算法：**
- 描述语义匹配：50 分
- 关键词精确匹配：30 分
- 分类匹配：15 分
- 标签/名称匹配：5 分

推荐阈值：≥40 分

### 📦 手动安装插件

**命令：** `/plugin-finder:install [plugin@marketplace] ...`

**用法示例：**

```bash
# 安装单个插件
/plugin-finder:install code-review@claude-plugins-official

# 批量安装多个插件
/plugin-finder:install \
  code-review@claude-plugins-official \
  security-guidance@claude-plugins-official \
  typescript-lsp@claude-plugins-official
```

**适用场景：**
- 知道确切的插件名称
- 需要安装特定版本
- 批量安装已知插件列表

### 🔄 多插件比较

**命令：** `/plugin-finder:multi-run [任务描述]`

**用法示例：**

```bash
# 比较代码审查工具
/plugin-finder:multi-run "审查这段代码的质量问题"

# 比较安全检查工具
/plugin-finder:multi-run "检查代码安全漏洞"

# 比较测试生成工具
/plugin-finder:multi-run "为这个函数生成测试用例"
```

**工作流程：**
1. 分析任务需求
2. 识别所有相关的已安装插件
3. 并行执行每个插件
4. 收集结果和输出
5. AI 分析比较质量、速度、输出等维度
6. 生成详细的对比报告

**比较维度：**
- ⭐ 质量：完整性、准确性、深度、可操作性
- ⚡ 性能：执行时间、资源使用
- 📄 输出：格式、生成的文件、可读性
- 👤 体验：易用性、清晰度

**报告格式：**
- 摘要表格
- 详细分析
- 推荐建议
- 使用场景指南

### 🤖 智能推荐

**触发方式：** 自动（当您表达需求时）

**示例场景：**

```
您："我想检查代码质量"
系统：自动触发 plugin-recommender agent
      → 搜索相关插件
      → 展示推荐列表
      → 协助安装
```

**触发条件：**
- 您表达了某种功能需求
- 但没有明确提到"插件"
- 系统判断可能有插件能帮助您

**控制推荐：**
通过配置文件控制是否自动推荐：
```yaml
# ~/.codebuddy/.local.md
---
auto_recommend: true  # false 关闭自动推荐
---
```

### 💡 插件许愿

**命令：** `/plugin-finder:wish [需求描述]`

**用法示例：**

```bash
# 许愿新功能的插件
/plugin-finder:wish "我需要一个能自动生成 API 文档的插件"

# 许愿集成类插件
/plugin-finder:wish "希望有 Notion 集成插件，能在 CodeBuddy 中直接操作 Notion"

# 许愿工具类插件
/plugin-finder:wish "需要一个数据库迁移管理工具"
```

**工作流程：**
1. 输入您的需求描述
2. AI 分析并整理需求
3. 生成详细的许愿邮件
4. 保存到本地文件：`plugin-wish-[timestamp].txt`
5. 提供发送指引

**邮件发送方式：**

**方式 1：复制粘贴（推荐）**
```bash
1. 打开文件：plugin-wish-[timestamp].txt
2. 复制全部内容
3. 发送邮件到：codebuddy@tencent.com
```

**方式 2：命令行发送**
```bash
mail -s "插件许愿" codebuddy@tencent.com < plugin-wish-[timestamp].txt
```

**方式 3：GitHub Issues**
```
1. 访问：https://github.com/codebuddy/plugins/issues
2. 创建新 Issue
3. 粘贴邮件内容
```

**许愿技巧：**
- 尽可能详细描述需求
- 说明具体的使用场景
- 提供参考工具（如果知道）
- 解释为什么需要这个插件

**期望管理：**
- CodeBuddy 团队会认真考虑每个许愿
- 但无法保证全部实现
- 会根据用户需求量和优先级排期
- 也欢迎您自己开发插件！

**什么时候许愿？**
- 搜索不到需要的插件时
- 推荐的插件都不满意时
- 发现插件生态的缺失时
- 有好的插件创意时

## 配置选项

### 创建配置文件

复制示例配置：

```bash
cp ~/.codebuddy/plugins/local/plugin-finder/.codebuddy/.local.md.example \
   ~/.codebuddy/.local.md
```

### 配置项说明

#### auto_recommend
**类型：** Boolean  
**默认：** true  
**说明：** 是否自动推荐插件

```yaml
auto_recommend: false  # 禁用自动推荐
```

#### recommendation_threshold
**类型：** String (high/medium/low)  
**默认：** medium  
**说明：** 推荐匹配阈值

```yaml
recommendation_threshold: high   # 只推荐高度相关的 (≥50分)
recommendation_threshold: medium # 推荐相关的 (≥40分)
recommendation_threshold: low    # 推荐可能相关的 (≥30分)
```

#### show_install_count
**类型：** Boolean  
**默认：** true  
**说明：** 显示插件安装量

```yaml
show_install_count: true  # 显示热度
```

#### preferred_marketplaces
**类型：** Array  
**默认：** 所有 marketplace  
**说明：** 优先搜索的市场

```yaml
preferred_marketplaces:
  - codebuddy-plugins-official
  - claude-plugins-official
```

#### comparison_output_format
**类型：** String (markdown/json/html)  
**默认：** markdown  
**说明：** 比较报告格式

```yaml
comparison_output_format: markdown  # 或 json, html
```

#### preferred_plugins
**类型：** Array  
**默认：** 无  
**说明：** 多插件比较时优先使用

```yaml
preferred_plugins:
  - code-review@claude-plugins-official
  - security-guidance@claude-plugins-official
```

### 配置示例

**保守配置：**
```yaml
---
auto_recommend: false
recommendation_threshold: high
preferred_marketplaces:
  - claude-plugins-official
---
```

**激进配置：**
```yaml
---
auto_recommend: true
recommendation_threshold: low
show_install_count: true
---
```

**团队配置：**
```yaml
---
auto_recommend: true
recommendation_threshold: medium
preferred_marketplaces:
  - codebuddy-plugins-official
preferred_plugins:
  - plugin-dev@claude-plugins-official
  - code-review@claude-plugins-official
  - security-guidance@claude-plugins-official
---
```

## 最佳实践

### 1. 搜索技巧

**使用具体的需求描述：**
```bash
# ✅ 好
/plugin-finder:search "自动化 API 文档生成"

# ❌ 不好
/plugin-finder:search "文档"
```

**使用关键功能词：**
```bash
# ✅ 好
/plugin-finder:search "代码质量检查和审查"

# ❌ 不好
/plugin-finder:search "让代码更好"
```

**中英文混用：**
```bash
# ✅ 可以
/plugin-finder:search "TypeScript language server 代码补全"
```

### 2. 安装管理

**批量安装节省时间：**
```bash
# ✅ 一次安装多个
/plugin-finder:install plugin1@market1 plugin2@market2 plugin3@market3

# ❌ 分多次安装
/plugin-finder:install plugin1@market1
/plugin-finder:install plugin2@market2
/plugin-finder:install plugin3@market3
```

**记得重启：**
安装后必须重启 CodeBuddy Code 才能生效！

### 3. 多插件比较

**先安装多个相关插件：**
```bash
# 安装多个代码审查工具
/plugin-finder:install \
  code-review@claude-plugins-official \
  security-guidance@claude-plugins-official

# 然后比较
/plugin-finder:multi-run "审查代码质量"
```

**任务描述要具体：**
```bash
# ✅ 好
/plugin-finder:multi-run "检查这个 API 函数的安全漏洞"

# ❌ 不好
/plugin-finder:multi-run "看看代码"
```

### 4. 自动推荐

**合理使用：**
- 如果觉得推荐太频繁，设置 `auto_recommend: false`
- 如果想要更多推荐，设置 `recommendation_threshold: low`

**主动寻求帮助：**
```
"我需要部署工具"  → 触发推荐
"有部署插件吗？"  → 触发推荐
```

## 常见问题

### Q1: 为什么 `/plugin list` 看不到 plugin-finder？

**A:** 需要重启 CodeBuddy Code。插件在会话启动时加载。

### Q2: 搜索找不到我想要的插件？

**A:** 可能的原因：
1. 插件不在已添加的 marketplace 中
2. 搜索词太具体或太宽泛
3. Marketplace 需要更新

**解决方法：**
```bash
# 更新 marketplace
/plugin marketplace update

# 尝试不同的搜索词
/plugin-finder:search "更广泛的描述"

# 查看所有插件
/plugin > Discover
```

### Q3: 安装失败怎么办？

**A:** 常见原因：
- 网络连接问题
- 插件源不可用
- 磁盘空间不足
- 权限不足

**解决方法：**
1. 检查网络连接
2. 重试安装
3. 查看错误信息
4. 手动安装：`/plugin install plugin@marketplace`

### Q4: 多插件比较只找到一个插件？

**A:** 需要先安装多个相关插件才能比较。

**解决方法：**
```bash
# 搜索并安装多个相关插件
/plugin-finder:search "代码审查"
# 选择并安装多个

# 重启后再比较
/plugin-finder:multi-run "任务描述"
```

### Q5: 如何禁用自动推荐？

**A:** 创建配置文件：
```bash
echo "---
auto_recommend: false
---" > ~/.codebuddy/.local.md
```

### Q6: 比较报告在哪里？

**A:** 报告生成在当前目录：
```
plugin-comparison-report-[timestamp].md
```

使用 `/read` 命令查看。

## 高级用法

### 1. 组合使用命令

```bash
# 搜索 → 安装 → 比较 工作流
/plugin-finder:search "测试工具"
# [安装多个测试工具]

# 重启 CodeBuddy Code

/plugin-finder:multi-run "为这个函数生成测试"
# [查看比较报告，选择最佳工具]
```

### 2. 自定义搜索脚本

使用提供的 shell 脚本：

```bash
~/.codebuddy/plugins/local/plugin-finder/scripts/search-plugins.sh "keyword"
```

### 3. 编程式访问

读取 marketplace 数据：

```bash
# CodeBuddy marketplaces
cat ~/.codebuddy/plugins/known_marketplaces.json | jq

# Claude marketplaces
cat ~/.claude/plugins/known_marketplaces.json | jq
```

### 4. 批量操作

安装一组预定义插件：

```bash
# 创建插件列表文件
cat > my-plugins.txt <<EOF
code-review@claude-plugins-official
security-guidance@claude-plugins-official
typescript-lsp@claude-plugins-official
EOF

# 批量安装
/plugin-finder:install $(cat my-plugins.txt | tr '\n' ' ')
```

### 5. 反馈和许愿

**找不到需要的插件？**

```bash
# 许愿新插件
/plugin-finder:wish "详细描述您的需求"

# 生成的邮件文件
cat plugin-wish-*.txt

# 发送到
# codebuddy@tencent.com
```

**许愿流程：**
1. 描述需求
2. AI 生成详细邮件
3. 保存到本地
4. 您发送邮件
5. 团队评估和排期

## 故障排查

### 检查插件状态

```bash
# 查看已安装插件
/plugin list

# 查看 marketplace
/plugin marketplace list

# 验证插件文件
ls -la ~/.codebuddy/plugins/local/plugin-finder/
```

### 查看日志

CodeBuddy Code 日志位置（如果有问题）：
```
~/.codebuddy/logs/
```

### 重新安装插件

如果插件出现问题：

```bash
# 1. 备份配置
cp ~/.codebuddy/.local.md ~/.codebuddy/.local.md.backup

# 2. 卸载
/plugin uninstall plugin-finder

# 3. 重新安装
/plugin install plugin-finder@local-dev

# 4. 重启 CodeBuddy Code
```

## 获取帮助

### 命令帮助

```bash
# 查看所有 plugin-finder 命令
/help plugin-finder

# 查看特定命令帮助
/help plugin-finder:search
/help plugin-finder:install
/help plugin-finder:multi-run
```

### 查看文档

```bash
# 查看 README
@~/.codebuddy/plugins/local/plugin-finder/README.md

# 查看本指南
@~/.codebuddy/plugins/local/plugin-finder/USAGE_GUIDE.md

# 查看 skill 文档
@~/.codebuddy/plugins/local/plugin-finder/skills/plugin-discovery/SKILL.md
```

### 反馈问题

如果遇到 bug 或有功能建议，请：
1. 记录详细的错误信息
2. 记录复现步骤
3. 联系插件维护者

## 下一步

### 扩展学习

1. **了解插件开发**
   - 安装 plugin-dev: `/plugin install plugin-dev@claude-plugins-official`
   - 学习如何创建自己的插件

2. **探索更多插件**
   - 浏览 marketplace: `/plugin > Discover`
   - 阅读插件文档

3. **优化工作流**
   - 配置自动推荐阈值
   - 设置偏好 marketplace
   - 创建常用插件列表

### 贡献

如果您想贡献代码或改进：
1. 插件位置：`~/.codebuddy/plugins/local/plugin-finder/`
2. 修改代码
3. 测试更改
4. 提交反馈

---

**需要更多帮助？**
- 询问 CodeBuddy Code："如何使用 plugin-finder？"
- 查看 `/help` 命令
- 阅读插件文档
