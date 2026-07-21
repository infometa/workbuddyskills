# mode: rewrite · 基于 master 做润色改写（不绑特定 JD）

> **前置**：先读 [`_shared.md`](_shared.md)。本文件只讲 rewrite 的差异。

## 触发条件

- 用户说："简历润色 / 简历优化 / 我的简历写得不太好，帮我改改"
- 提供了简历素材但**未**提供 JD
- 明确 `mode: "rewrite"`

## 输出定位

- 若目的是**更新 master 本体** → 写入 `resume-output/_master/` 并把旧 master 留档为 `_master-archive-<ts>/`（不删除！）
- 若目的是产出**润色版而不替换 master** → 写入 `resume-output/<version_label>/`，`parent_id: _master`，`is_master: false`

**默认策略**：询问用户要覆盖 master 还是留档另存；不主动覆盖。

## 与骨架的差异

| Step | 差异 |
|---|---|
| Step 0 | mode 已定 |
| **Step 0.5** | **必跑** · Preflight 三选项：模板 / 长度 / 语言（v0.3.2 · 铁律 #15 · `references/preflight-questions.md`）。若 master 已有 preferences 字段且用户未明确改，**继承 master**，仅在用户主动改某项时再问 |
| Step 1 | 以 master 为素材源；用户提供新素材时合并（不 force overwrite master）|
| **Step 2** | **跳过 JD 解析**（rewrite 不绑 JD）|
| **Step 3** | role_family 沿用 master 记录的 `result.role_family`；archetype 若 master 未记录则不推断 |
| Step 4 | 改写焦点 = 通用表达质量：动词强度 / 量化补全 / 去冗余 / 去 AI 味 |
| Step 5 | 三维度必跑；**维度三 AI 味重点检查**（润色最容易过度修辞）|
| **Step 6** | **跳过** JD 覆盖率（无 JD）|
| Step 7 | 写入位置看上面"输出定位"；派生版必生成 `diff-report.html`（base=master） |
| Step 8 | 审核要点：每条改写都需对照"前 vs 后"让用户看动词/语气/结构变化 |

## rewrite 独有的 NEVER

- **NEVER** 未经用户确认就覆盖 master（Master-First 原则）
- **NEVER** 用 rewrite 引入 master 不存在的事实（这是 generate 的职责）

## 成功判定

- 用户确认覆盖或派生策略
- 三维度审计通过 + Step 8 approved
- 若派生：`diff-report.html` 已生成；若覆盖：旧 master 已归档到 `_master-archive-<ts>/`
