# Testing Guide for Info Command

本文档提供 `/plugin-finder:info` 命令的测试指南。

## 测试前准备

确保 plugin-finder 已安装并且可以访问 marketplace 数据：

```bash
# 检查插件是否已安装
/plugin list | grep plugin-finder

# 确认 marketplace 数据存在
ls ~/.codebuddy/plugins/known_marketplaces.json
ls ~/.claude/plugins/known_marketplaces.json
```

## 测试用例

### 1. 基本功能测试

**测试目标**：验证 info 命令能够正常显示插件信息

#### 测试 1.1：查看本地插件（不指定 marketplace）

```bash
/plugin-finder:info plugin-dev
```

**预期结果**：
- ✅ 显示 plugin-dev 的基本信息（名称、版本、作者）
- ✅ 显示组件统计（7 个 skills, 3 个 agents, 1 个 command）
- ✅ 列出所有组件的详细信息
- ✅ 显示实现概述

#### 测试 1.2：查看插件（指定 marketplace）

```bash
/plugin-finder:info plugin-dev@codebuddy-plugins-official
```

**预期结果**：
- ✅ 与 1.1 相同的结果
- ✅ 明确显示使用的 marketplace

#### 测试 1.3：查看当前插件自身

```bash
/plugin-finder:info plugin-finder
```

**预期结果**：
- ✅ 显示 plugin-finder 自身的信息
- ✅ 包含新增的 info 命令（共 5 个命令）
- ✅ 显示 1 个 agent, 1 个 skill, 1 个 hook

### 2. 不同组件类型的插件测试

#### 测试 2.1：有 MCP 集成的插件

```bash
/plugin-finder:info <mcp-plugin-name>
```

**预期结果**：
- ✅ 显示 MCP servers 部分
- ✅ 列出每个 MCP server 的类型（stdio/sse/http/websocket）

#### 测试 2.2：有 Hooks 的插件

```bash
/plugin-finder:info plugin-finder
```

**预期结果**：
- ✅ 显示 Hooks 部分
- ✅ 列出 hook 事件名称和类型（prompt/command）

#### 测试 2.3：只有 Skills 的插件

找一个只有 skills 没有其他组件的插件测试

**预期结果**：
- ✅ 正确显示 skills 部分
- ✅ 其他组件显示为 0 个

### 3. 错误处理测试

#### 测试 3.1：无参数

```bash
/plugin-finder:info
```

**预期结果**：
- ✅ 显示使用说明
- ✅ 显示示例用法
- ✅ 提示使用 search 命令查找插件

#### 测试 3.2：插件不存在

```bash
/plugin-finder:info non-existent-plugin
```

**预期结果**：
- ✅ 显示"未找到插件"错误
- ✅ 提供建议（检查拼写、使用 search 命令）
- ✅ 列出可用的 marketplace

#### 测试 3.3：Marketplace 不存在

```bash
/plugin-finder:info plugin-dev@non-existent-marketplace
```

**预期结果**：
- ✅ 显示"未找到 marketplace"错误
- ✅ 列出可用的 marketplace
- ✅ 提示如何添加新 marketplace

#### 测试 3.4：插件路径不存在

如果 marketplace 中注册了插件但本地路径不存在：

**预期结果**：
- ✅ 显示警告信息
- ✅ 显示预期路径
- ✅ 建议重新安装插件

### 4. 输出格式测试

#### 测试 4.1：验证输出结构

对任意插件运行 info 命令，检查输出包含：

- ✅ 基本信息部分（📦 名称、版本、作者、描述、关键词）
- ✅ 组件统计部分（🛠️ 显示所有组件类型及数量）
- ✅ Commands 详情（如果有）
- ✅ Agents 详情（如果有）
- ✅ Skills 详情（如果有）
- ✅ Hooks 详情（如果有）
- ✅ MCP 详情（如果有）
- ✅ 实现概述（🔧）
- ✅ Footer 提示（💡 安装、搜索相关插件、查看源码）
- ✅ 统计摘要（📊）

#### 测试 4.2：验证 emoji 和格式

- ✅ 检查所有 emoji 正确显示
- ✅ 检查树形结构 (├─, └─) 正确显示
- ✅ 检查中文和英文混排正确

### 5. 分析脚本单独测试

#### 测试 5.1：直接运行分析脚本

```bash
/Users/laurentzhou/CodeBuddy/marketplace/plugins/plugin-finder/examples/analyze-plugin-info.sh /path/to/plugin
```

**预期结果**：
- ✅ 输出有效的 JSON
- ✅ JSON 包含所有必要字段
- ✅ 组件数量准确

#### 测试 5.2：测试不同结构的插件

测试以下类型的插件：
- 空插件（只有 plugin.json）
- 只有 commands 的插件
- 复杂插件（包含所有组件类型）

**预期结果**：
- ✅ 所有情况下脚本都不报错
- ✅ 正确识别所有组件

### 6. 边界情况测试

#### 测试 6.1：插件名称包含特殊字符

```bash
/plugin-finder:info plugin-name-with-dashes
```

#### 测试 6.2：非常长的插件名称

#### 测试 6.3：Marketplace 名称包含特殊字符

#### 测试 6.4：插件包含大量组件

测试有 10+ 个 commands 或 skills 的插件

**预期结果**：
- ✅ 所有情况下都能正确处理
- ✅ 输出格式不会混乱

## 性能测试

### 测试 7.1：响应时间

运行 info 命令并测量响应时间：

```bash
time /plugin-finder:info plugin-dev
```

**预期结果**：
- ✅ 小型插件：< 2 秒
- ✅ 大型插件：< 5 秒

### 测试 7.2：多次连续调用

连续调用 5 次 info 命令，确保没有性能下降或内存泄漏。

## 集成测试

### 测试 8.1：与 search 命令配合

```bash
# 先搜索
/plugin-finder:search "plugin development"

# 然后查看详情
/plugin-finder:info plugin-dev
```

**预期结果**：
- ✅ 两个命令无缝协作
- ✅ info 提供的信息帮助用户决定是否安装

### 测试 8.2：与 install 命令配合

```bash
# 查看插件详情
/plugin-finder:info some-plugin

# 决定安装
/plugin-finder:install some-plugin@marketplace
```

**预期结果**：
- ✅ info 提供足够信息支持安装决策

## 测试检查清单

在发布前确保以下所有测试通过：

- [ ] 所有基本功能测试通过
- [ ] 所有错误处理测试通过
- [ ] 输出格式正确且美观
- [ ] 分析脚本独立运行正常
- [ ] 所有边界情况处理正确
- [ ] 性能满足要求
- [ ] 与其他命令集成良好

## 已知问题

（目前无已知问题）

## 反馈

如果在测试中发现问题，请记录：
1. 测试用例编号
2. 执行的命令
3. 预期结果
4. 实际结果
5. 错误信息（如果有）

---

**最后更新**: 2026-01-18
