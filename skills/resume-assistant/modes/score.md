# mode: score · 给简历对某 JD 打覆盖率/差距分

> **前置**：先读 [`_shared.md`](_shared.md)。本文件只讲 score 的差异。

## 触发条件

- 用户说："我这版简历投 XX 岗位能打几分 / 匹配度多少 / 差距在哪"
- 用户提供 JD + 指定某个 `version_id`（默认 `_master`）
- 明确 `mode: "score"`

## 输入

- `target_job.jd_content`：必填
- `version_control.version_id`：被评分的简历版本，默认 `_master`

## 与骨架的差异

评分是只读操作，不改写简历：

| Step | 差异 |
|---|---|
| Step 0 | mode 已定 |
| Step 1 | 读取指定 version 的 `result.json` 作为素材；不追问 |
| Step 2 | 必跑 `parse_jd.py` |
| Step 3 | 只记录推断的 `role_family / archetype`，不用于改写 |
| **Step 4** | **跳过改写** |
| **Step 5** | 三维度 Provenance **跳过**（内容未变）|
| Step 6 | 核心步骤 · 生成 `jd-match-report.md`：<br>• 关键词覆盖率（hard/soft/industry 分类）<br>• 缺失关键词清单 + 是否在 master 中找得到相近素材<br>• seniority 对齐判断<br>• archetype 对齐判断（若有）<br>• 综合分 0-100（权重公式见 keyword-taxonomy §权重区间）|
| Step 7 | 输出到 `resume-output/<version_id>/jd-match-report-<jd-hash>.md`（**不覆盖**已有 `jd-match-report.md`）|
| **Step 8** | **跳过**用户审核（score 是诊断工具，无需确认）|

## 评分公式（简化示意，见 keyword-taxonomy.md 权重说明）

```
score = 100 × (
    0.5 × hard_skills_coverage
  + 0.3 × industry_terms_coverage
  + 0.1 × seniority_match
  + 0.1 × archetype_match
)
```

## score 独有的 NEVER

- **NEVER** 修改 simulated 简历内容
- **NEVER** 生成 diff 或 provenance 条目（纯只读）
- **NEVER** 覆盖同目录下已有的 `jd-match-report.md`（改用带 jd-hash 的文件名）

## 成功判定

- `jd-match-report-<jd-hash>.md` 生成
- 报告含综合分、分类覆盖率、差距建议
