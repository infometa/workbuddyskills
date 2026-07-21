# Ralph Loop Plugin

在 CodeBuddy Code 中实现 Ralph Wiggum 技术，用于迭代式、自我引用的 AI 开发循环。

## 什么是 Ralph Loop？

Ralph Loop 是一种基于持续 AI Agent 循环的开发方法论。正如 Geoffrey Huntley 所描述的：**"Ralph 是一个 Bash 循环"** — 一个简单的 `while true` 循环，反复向 AI Agent 提供一个提示文件，使其能够迭代改进工作直到完成。

这种技术灵感来源于 Ralph Wiggum 编程技术（以《辛普森一家》中的角色命名），体现了面对挫折时持续迭代的理念。

### 核心概念

该插件使用 **Stop Hook** 来实现 Ralph，通过拦截 CodeBuddy 的退出尝试：

```bash
# 你只需运行一次：
/ralph-loop "你的任务描述" --completion-promise "DONE"

# 然后 CodeBuddy Code 会自动：
# 1. 处理任务
# 2. 尝试退出
# 3. Stop hook 阻止退出
# 4. Stop hook 将相同的提示反馈回来
# 5. 重复直到完成
```

循环发生在**你当前的会话内部** — 不需要外部的 bash 循环。`hooks/stop-hook.sh` 中的 Stop hook 通过阻止正常的会话退出创建自我引用的反馈循环。

这创建了一个**自我引用的反馈循环**，其中：
- 提示在迭代之间保持不变
- CodeBuddy 之前的工作保留在文件中
- 每次迭代都能看到修改后的文件和 git 历史
- CodeBuddy 通过读取文件中自己过去的工作自主改进

## 快速开始

```bash
/ralph-loop "构建一个待办事项的 REST API。要求：CRUD 操作、输入验证、测试。完成后输出 <promise>COMPLETE</promise>。" --completion-promise "COMPLETE" --max-iterations 50
```

CodeBuddy 将会：
- 迭代实现 API
- 运行测试并查看失败
- 根据测试输出修复 bug
- 迭代直到满足所有要求
- 完成后输出完成承诺

## 命令

### /ralph-loop

在当前会话中启动一个 Ralph 循环。

**用法：**
```bash
/ralph-loop "<提示>" --max-iterations <n> --completion-promise "<文本>"
```

**选项：**
- `--max-iterations <n>` - 在 N 次迭代后停止（默认：无限制）
- `--completion-promise <文本>` - 表示完成的短语

### /cancel-ralph

取消当前活动的 Ralph 循环。

**用法：**
```bash
/cancel-ralph
```

## 提示编写最佳实践

### 1. 明确的完成标准

❌ 不好的写法："构建一个待办事项 API 并做好它。"

✅ 好的写法：
```markdown
构建一个待办事项的 REST API。

完成时：
- 所有 CRUD 端点正常工作
- 输入验证已就位
- 测试通过（覆盖率 > 80%）
- 包含 API 文档的 README
- 输出：<promise>COMPLETE</promise>
```

### 2. 渐进式目标

❌ 不好的写法："创建一个完整的电商平台。"

✅ 好的写法：
```markdown
阶段 1：用户认证（JWT、测试）
阶段 2：产品目录（列表/搜索、测试）
阶段 3：购物车（添加/删除、测试）

所有阶段完成后输出 <promise>COMPLETE</promise>。
```

### 3. 自我修正

❌ 不好的写法："为功能 X 编写代码。"

✅ 好的写法：
```markdown
遵循 TDD 实现功能 X：
1. 编写失败的测试
2. 实现功能
3. 运行测试
4. 如果有失败，调试并修复
5. 如需则重构
6. 重复直到全部通过
7. 输出：<promise>COMPLETE</promise>
```

### 4. 安全退出机制

始终使用 `--max-iterations` 作为安全网，以防止在不可能完成的任务上出现无限循环：

```bash
# 推荐：始终设置合理的迭代限制
/ralph-loop "尝试实现功能 X" --max-iterations 20

# 在你的提示中，包含遇到困难时的处理方式：
# "15 次迭代后，如果未完成：
#  - 记录阻碍进展的因素
#  - 列出已尝试的方法
#  - 建议替代方案"
```

**注意**：`--completion-promise` 使用精确字符串匹配，因此你不能将其用于多个完成条件（如 "SUCCESS" vs "BLOCKED"）。始终依赖 `--max-iterations` 作为你主要的安全机制。

## 理念

Ralph 体现了几个关键原则：

### 1. 迭代 > 完美
不要追求一次完美。让循环来完善工作。

### 2. 失败即数据
"确定性的坏"意味着失败是可预测且具有信息量的。利用它们来调整提示。

### 3. 操作者技能很重要
成功取决于编写好的提示，而不仅仅是拥有好的模型。

### 4. 坚持致胜
持续尝试直到成功。循环会自动处理重试逻辑。

## 何时使用 Ralph

**适用于：**
- 有明确成功标准的明确定义的任务
- 需要迭代和改进的任务（例如，让测试通过）
- 可以离开的绿地项目
- 具有自动验证的任务（测试、linter）

**不适用于：**
- 需要人类判断或设计决策的任务
- 一次性操作
- 成功标准不明确的任务
- 生产环境调试（应使用有针对性的调试）

## 真实世界成果

- 在 Y Combinator 黑客马拉松测试中一夜之间成功生成 6 个代码仓库
- 一份价值 5 万美元的合同仅花费 297 美元的 API 费用就完成了
- 使用这种方法在 3 个月内创建了完整的编程语言（"cursed"）

## 了解更多

- 原始技术：https://ghuntley.com/ralph/
- Ralph Orchestrator：https://github.com/mikeyobrien/ralph-orchestrator

## 获取帮助

在 CodeBuddy Code 中运行 `/help` 以获取详细的命令参考和示例。
