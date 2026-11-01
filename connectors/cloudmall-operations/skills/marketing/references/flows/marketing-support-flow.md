# 营销域 — 运营流程：协议与导入导出（支持流程）

> 概念知识见 `references/domains/marketing-concepts.md`，状态与枚举见 `references/domains/marketing-enums.md`。
> 全部写操作遵守入口 SKILL.md 的风险档位与确认纪律。
> **能力标识约定**：本文为行文简洁使用模块短名（如 `cps-activity.save`、`popup.review`），实际调用 capability 必须使用全限定 id = `ops.marketing.` + 短名（即 `ops.marketing.cps-activity.save`），禁止把短名直接作为 capability 传入。
> 对应契约：`agreement-query.md` / `agreement-action.md`、`export-task.md`（导出轮询）、各模块 `*.export`（入 `*-query.md`）与 `*.import`（入 `*-action.md`）。

---

## 协议管理

**场景**：9 类协议的新建→发布→结束生命周期。

```
新建（agreement.create，🟡 未发布 0，富文本 HTML ≤30000 字符，服务端安全净化）
  → [可选] 编辑（agreement.update，仅未发布 0；title/content 均必填）
  → 发布（agreement.publish，🔴 C 端即刻按新版本展示；**同类型当前已发布的旧协议自动转已结束**——发布前向用户确认该影响）
  → [可选] 结束（agreement.end，🔴 已结束 2 终态；结束后该类型 C 端无生效协议）
  → 删除（agreement.delete，🔴 物理删除；已发布不可删需先结束）
```

- 查询：`agreement.search`（title/type/status 筛选）/ `detail`（编辑前必读；content 图片 src 为 30 分钟临时 URL）/ `preview`（轻量预览）。
- 协议类型 1..9 见 `marketing-enums.md` 枚举字典；同类型同时只有一个"已发布"版本。

---

## 数据导入导出（跨模块通用）

**场景**：运营要求把名单/明细落成 Excel，或按模板批量导入。

### 导出（异步任务三步闭环）

```
① 选定 *.export 能力（与对应分页查询同构的筛选条件）
   → ② 返回任务 ID（String）
   → ③ export-task.get 轮询：PENDING/PROCESSING 继续（间隔 ≥ 数秒）→ COMPLETED 取 downloadUrl（约 30 分钟时效）/ FAILED 停止并报告
```

- 已开放导出：导购 / 分销员 / 话术 / 提成明细 / 素材复制记录 / 结算明细（按活动与全局）/ 活动推广报表 / 商品推广 / 分销订单。
- `downloadUrl` 不持久化、不当稳定链接转述；导出大数据量时 PROCESSING 可能较久，告知用户等待。
- **提现列表导出后端未实现**（前后端契约缺口），命中时说明不可执行。

### 导入（multipart Excel，仅文件型 capability）

```
用户给出模板文件（当前运行时提供文件输入）
   → 对应 *.import 能力（目标计划需 planId 路径参数）
   → 返回成功/失败明细 → 失败行修正后重导；执行后回读列表核验落库结果
```

- 已开放导入：分销员 / 导购 / 话术 / 目标计划目标行。
- 模板列结构以运营端页面下载为准；**不要在无文件输入时凭空构造导入调用**（会失败）；也不要用分页查询数据"模拟导入结果"。
- 导入创建的主体（分销员等）遵循对应实体状态机（如分销员创建即启用）。

---
