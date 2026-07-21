---
name: lexiang-knowledge-base
version: 2.0.0
description: "乐享知识库 MCP 全功能 Skill。当用户提到「乐享」「知识库」「lexiang」，或提供 lexiangla.com 链接，或涉及知识库的搜索/写入/编辑/文件/配置等操作时使用。"
sub_skills:
  - base/SKILL.md
  - setup/SKILL.md
  - search/SKILL.md
  - writer/SKILL.md
  - blocks/SKILL.md
  - files/SKILL.md
  - connectors/SKILL.md
---

# 乐享知识库 MCP Skill

当用户提到「**乐享**」「**知识库**」「**lexiang**」，或提供 `lexiangla.com` 链接，或给出 `space_id`、`entry_id`、`/spaces/`、`/pages/` 等乐享标识时，读取本 Skill。

---

## ⛔ MANDATORY RULES — 必须遵守

1. **遇到 401 错误**：立即停止重试，读取 `setup/SKILL.md` 引导续期
2. **写入操作**：必须基于用户明确提供的目标（URL/ID/名称确认），**禁止**自行遍历或猜测目标
3. **链接生成**：必须使用 `whoami()` 返回的 `company.company_domain` 作为域名，**禁止**使用 MCP endpoint 拼接用户链接
4. **company_from**：不能拼接为子域名，只能作 `?company_from=xxx` 查询参数

---

## 📋 意图路由表

根据用户意图，读取对应子模块 SKILL.md：

| 用户意图 | 读取子模块 | 典型触发词 |
|---------|-----------|-----------|
| 配置乐享 / 401 错误 / Token 过期 | `setup/SKILL.md` | 「配置乐享」「token 过期」「连不上」「401」 |
| 搜索 / 查找 / 阅读 / 浏览 | `search/SKILL.md` | 「找一下」「搜索」「读一下这个页面」「打开链接」 |
| 创建文档 / 写入 / 保存 / 导入 | `writer/SKILL.md` | 「写到乐享」「创建文档」「保存到知识库」「导入」 |
| 编辑已有页面 / Block 操作 | `blocks/SKILL.md` | 「修改这个页面」「加个标题」「删掉这段」「在 /pages/xxx 里…」 |
| 上传/下载文件（PDF/Word/图片等） | `files/SKILL.md` | 「传个 PDF」「上传文件」「下载这个文件」 |
| 导入腾讯会议 / iWiki | `connectors/SKILL.md` | 「把会议录制导入」「迁移 iWiki 页面」 |

### ⚠️ 易混淆场景

| 场景 | 正确模块 | 说明 |
|------|---------|------|
| 用户提供 `/pages/xxx` 链接 + 要求「加内容/修改」 | `blocks/SKILL.md` | 操作**已有页面** |
| 用户提供 `/spaces/xxx` 链接 + 要求「写入/创建」 | `writer/SKILL.md` | 在知识库下**新建文档** |
| 用户提供 `/pages/xxx` 链接 + 仅要求「读/总结」 | `search/SKILL.md` | **只读**操作 |
| 上传 PDF/Word/图片 | `files/SKILL.md` | 二进制文件，非文本文档 |
| 创建 Markdown 文本文档 | `writer/SKILL.md` | 文本内容，非二进制 |

### ⚠️ 跨模块任务

需要同时读取多个子模块时，按流程顺序读取：

- **搜索后写入**：先 `search/SKILL.md` → 再 `writer/SKILL.md`
- **读取后编辑**：先 `search/SKILL.md` → 再 `blocks/SKILL.md`
- **上传后记录**：先 `files/SKILL.md` → 再 `writer/SKILL.md`

---

## 🔑 凭证检查

执行任何乐享操作前，确认 MCP 已连接。通过 `whoami()` 检查：

```
MCP Tool: whoami
→ 成功：返回用户信息，继续执行
→ 401：读取 setup/SKILL.md，引导续期（点续期按钮，无需重新配置）
→ 连接失败：读取 setup/SKILL.md，引导完成初始配置
```

---

## 🔗 链接生成规则（全局通用）

所有操作完成后返回链接时，统一遵循（完整规则见 `base/SKILL.md`）：

| `company.company_domain` 类型 | 链接格式 | 示例 |
|------------------------------|----------|------|
| 包含三级域名（如 `csig.lexiangla.com`） | `{domain}/pages/{entry_id}` | `https://csig.lexiangla.com/pages/abc` |
| 顶级域名（如 `lexiangla.com`） | `{domain}/pages/{entry_id}?company_from={company_from}` | `https://lexiangla.com/pages/abc?company_from=csig` |

**`{company_from}` 获取优先级：**
1. mcp.json `url` 字段中的 `company_from` 参数
2. 若无，使用 `whoami().company.code`

---

## 📚 子模块索引

> **按需加载**：根据意图路由表，只读取对应子模块的 SKILL.md，无需一次性加载全部。

| 子模块 | 文件 | 职责 |
|--------|------|------|
| 配置与认证 | `setup/SKILL.md` | Token 配置、续期、WorkBuddy OAuth、故障排查 |
| 搜索与阅读 | `search/SKILL.md` | 关键词/语义搜索、内容读取、目录浏览 |
| 文档写入 | `writer/SKILL.md` | 新建文档、导入内容、公众号收藏 |
| Block 编辑 | `blocks/SKILL.md` | 已有页面的 Block 级增删改移 |
| 文件管理 | `files/SKILL.md` | 二进制文件上传/下载（三步流程） |
| 外部导入 | `connectors/SKILL.md` | 腾讯会议录制导入、iWiki 迁移 |

---

> Skill version: **2.0.0**
