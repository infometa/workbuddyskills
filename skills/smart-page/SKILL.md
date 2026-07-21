---
name: smart-page
description: "腾讯文档智能页面（Smart Page）是可交互在线汇报网页生成工具，适用于汇报、述职、周报、复盘、数据看板、课件、培训、调研报告、会议纪要和本地 HTML 上云。区别于 PPT 与普通网页，内置叙事骨架、动效模板，生成后可在线编辑、分享并沉淀到腾讯文档。"
description_zh: "腾讯文档智能页面，生成可编辑可分享的在线汇报网页内容"
description_en: "Create interactive Tencent Docs smart pages for reports and presentations"
version: 1.0.1
allowed-tools: Read,Write,Bash
---

# 腾讯文档智能页面 · Smart Page

腾讯文档新产品——智能页面 · Smart Page，打造下一代可交互的 AI 原生范式分享汇报网页。

## 工作模式分流（关键决策）

用户请求进来时，agent 自行判断走哪条路：

```
用户输入
  ├─ 已有 HTML：本地路径 / 「把 HTML 上传腾讯文档」      → 走【上云模式 · 本地 HTML 一键上云】
  ├─ 模板生成：明确命中 4 类已做好模板的场景               → 走【生成模式 · 模板化生成链路】
  │    （向上汇报/立项、周期同步/复盘、数据洞察、知识传播/技术分享）
  └─ 不在本 skill 范围：其他所有场景（邀请函、官网、Landing、
        简历、H5、画册、PRD、会议纪要、婚礼/年会/发布会邀请等） → 【退出本 skill，交给通用 agent】
```

---

## 上云模式 · 本地 HTML 一键上云

**触发条件**：

- 用户给出 `.html` 文件路径（或拖附件）
- 触发词：「把这个 HTML 导入腾讯文档」「上传本地 HTML」「.html 路径 + 上传/发布/上云」

**跳过全部问卷流程**，直接走「发布到腾讯文档」章节（不传 `--title`，自动从 HTML `<title>` 读取）。

---

## 生成模式 · 模板化生成链路（概览）

**触发条件**：用户意图命中 4 类场景之一（`proposal` 向上汇报/立项、`sync` 周期同步/复盘、`insight` 数据洞察、`share` 知识传播/技术分享）。

> ⚠️ **核心原则**：agent 自行 best-guess scene（不确定就选最接近的），**立刻起 `serve.py start`**，场景确认/修正由用户在右侧面板完成。**绝不使用 AskUserQuestion 或对话追问**。

**工作流总览**：

```
阶段 1 场景初筛 → 阶段 2 问卷路由 → 阶段 3 模板选择 → 阶段 4 骨架 loading → 阶段 5 生成数据 + inject → 阶段 6 自检 → 阶段 7 发布
```

> 📖 **完整流程见 `references/generate-workflow.md`**：含 4 类场景细表、四区理念、三层架构、阶段 1–7 的全部命令、JSON 协议和数据契约。**首次执行生成模式时必读**。

阶段 7 走下方「发布到腾讯文档」章节。

---

## 发布到腾讯文档

所有模式最终上云都走 `scripts/publish.sh`（脚本内有完整 Usage，执行 `publish.sh --help` 可查看）。

**行为约束**：

- ⚠️ **禁止手动调用 MCP**：不要自行拼接 `pre_import` / `async_import` 调用链，必须且只能通过 `bash scripts/publish.sh --html <path>` 完成发布。`publish.sh` 内部会自动完成 `.aipage` 打包、上传、轮询全链路。
- 拿到 `FILE_URL` 后必须独立发起 `preview_url` 工具调用，然后告诉用户「已完成，在线地址如下 ↓」
- 失败时重试最多 2 次（间隔 5s），仍失败则把 stderr 和 TRACE_ID（如有）告诉用户，建议检查 MCP 配置
- 不要静默吞掉错误

---

## 核心原则

1. **模式分流优先**：先判断「上云模式 / 生成模式 / 不在本 skill 范围」，不要把所有场景都塞进生成模式的固定模板流
2. **不在本 skill 范围的请求不进管线**：交给通用 agent 按当次意图自由生成
3. **生成模式四区必须都有**：Overview / Controls / Charts / Logic 缺一视为 PPT 化
4. **叙事 ≠ 视觉**：换皮肤不改 section 顺序，换叙事不改色值
5. **首屏给结论**：不允许把 TL;DR 藏在折叠里
6. **腾讯系优先**：司内汇报默认 `tencent-blue`，且 `tone=tencent` 时锁定单一皮肤
7. **单文件分发**：inject.py 产物必须可独立打开
8. **`prefers-reduced-motion` 必须降级**
9. **等待用 shell 循环**：`for+sleep+test -f`，禁止 heredoc 写长 python 脚本或自定义进程管理
10. **data.js 必须同时读 narrative.md + mock-data.js 再写**：`narrative.md` 提供字段契约，`mock-data.js` 提供值类型、嵌套结构和 compute 写法，两者都必读
11. **注入前必跑 validate_data.py**：`validate_data.py --scene --narrative --data` 退出码 0 才允许注入，失败则修复后重跑（最多 2 次）

---

## 附录

### 外部依赖

| 依赖                      | 用途                         | 缺失时处理                                        |
| ------------------------- | ---------------------------- | ------------------------------------------------- |
| `tencent-docs` MCP        | 阶段 7 / 上云模式发布环节    | 提示用户在 WorkBuddy 中授权 `tencent-docs` 连接器 |
| `tdocs-trace-query` skill | 发布异常时用 trace_id 查链路 | 可跳过，直接把错误信息告诉用户                    |

### 参考文档

| 文档                              | 何时读取                                                                     |
| --------------------------------- | ---------------------------------------------------------------------------- |
| `references/generate-workflow.md` | 首次执行生成模式时必读（含完整工作流和阶段细节）                             |
| `references/command-reference.md` | 首次执行生成模式时必读（含完整等待协议和目录结构）                           |
| `references/intent-mapping.md`    | 模式分流 / scene 推断 / 「AI 帮我选」时查表（关键词 → scene/narrative/skin） |
| `references/architecture.md`      | 理解四区理念 / 三层正交（场景 × 叙事 × 皮肤）时按需读取                      |
| `references/data-truthfulness.md` | 生成数据前必读（防捏造、信息补全规则）                                       |
