# lexiang-skills

**乐享知识库 MCP Skill（v2.0.0）**

为 AI Agent 提供乐享知识库的全功能操作能力，包括搜索阅读、文档写入、Block 编辑、文件上传、外部导入等。

---

## 快速开始

### WorkBuddy 用户

WorkBuddy 已内置乐享连接器，**无需手动配置**：

1. 在 WorkBuddy「集成」页面找到「乐享」连接器
2. 点击「授权」完成 OAuth 登录，连接器自动激活

### 其他平台（OpenClaw、Claude 等）

访问 [https://lexiangla.com/mcp](https://lexiangla.com/mcp) 获取 `COMPANY_FROM` 和 `LEXIANG_TOKEN`，填入 `mcp.json`：

```json
{
  "mcpServers": {
    "lexiang": {
      "enabled": true,
      "url": "https://mcp.lexiang-app.com/mcp?company_from=你的COMPANY_FROM",
      "transportType": "streamable-http",
      "headers": {
        "Authorization": "Bearer 你的LEXIANG_TOKEN"
      }
    }
  }
}
```

---

## 目录结构

```
lexiang-skills/
├── SKILL.md              # 顶层路由入口（意图识别 → 子模块）
├── mcp.json              # MCP 配置模板
├── base/
│   └── SKILL.md         # 基础知识层：数据模型、URL 规则、安全规则、工具发现
├── setup/
│   └── SKILL.md         # MCP 配置、Token 续期、故障排查
├── search/
│   └── SKILL.md         # 搜索与内容阅读
├── writer/
│   └── SKILL.md         # 文档创建与写入
├── blocks/
│   └── SKILL.md         # 已有页面 Block 级编辑
├── files/
│   └── SKILL.md         # 二进制文件上传/下载
├── connectors/
│   └── SKILL.md         # 腾讯会议录制导入、iWiki 迁移
├── references/           # 详细参考文档（11 份）
└── scripts/              # 辅助脚本
```

---

## 子模块说明

| 子模块 | 触发场景 |
|--------|---------|
| `setup` | 配置乐享、Token 过期、401 错误、切换企业 |
| `search` | 搜索文档、阅读页面、浏览知识库目录 |
| `writer` | 创建文档、保存内容、导入公众号文章 |
| `blocks` | 修改已有页面、追加内容、调整排版 |
| `files` | 上传 PDF/Word/图片等二进制文件 |
| `connectors` | 导入腾讯会议录制、迁移 iWiki 页面 |

---

## 核心规则

- **写入安全**：必须基于用户明确提供的目标（URL/ID/确认），禁止自行遍历猜测
- **链接生成**：使用 `whoami().company.company_domain` 作为域名；顶级域名需追加 `?company_from=`（优先取 mcp.json，其次取 `whoami().company.code`）
- **401 处理**：不重试，引导用户续期（点续期按钮即可恢复，无需重新配置）

---

## 辅助脚本

| 脚本 | 说明 |
|------|------|
| `scripts/upload-files.py` | 批量文件上传（支持单文件/文件夹/并行/dry-run） |
| `scripts/sync-folder.ts` | 文件夹增量同步到乐享知识库 |

```bash
# 单文件上传
python scripts/upload-files.py --files doc.md --entry-id <parent_entry_id>

# 文件夹批量上传（5 并行）
python scripts/upload-files.py --folder ./docs --entry-id <parent_entry_id> --parallel 5
```

---

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/common-errors.md` | 高频错误速查与修复 |
| `references/block-schema.md` | Block 类型完整字段定义 |
| `references/mcp-examples.md` | 复杂 Block 结构示例 |
| `references/doc-templates.md` | 文档大纲模板（推广/技术/操作指南） |
| `references/markdown-import.md` | Markdown 导入详解 |
| `references/markdown-to-block.md` | Markdown 转 Block 指南 |
| `references/folder-sync.md` | 文件夹同步方案 |
| `references/content-reorganize.md` | 文档结构重组 |
| `references/block-update.md` | 批量更新 Block 方法 |
| `references/theme-config.md` | 主题配色配置 |

---

## 相关链接

- 乐享平台：https://lexiangla.com
- 获取 MCP 配置：https://lexiangla.com/mcp
- MCP 协议：https://modelcontextprotocol.io
