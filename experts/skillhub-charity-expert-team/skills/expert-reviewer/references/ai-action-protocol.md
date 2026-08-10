# ai_actions 协议（expert-reviewer 专用）

本文档定义 `review.py` 输出的 `ai_actions` 列表中各 `action_type` 的语义、context 字段约定、外部提交处理口径，以及弹窗触发条件。

---

## 一、action_type 总览

| action_type | 用途 | 默认 priority | 外部提交处理 | 规范出处 |
|-------------|------|--------------|--------------|---------|
| `team-rule-check` | 校验主理人 prompt 是否含 TeamCreate 铁律 + 5 条红线 + 协作规则 | required | BLOCKER | CODEBUDDY §4.4 / WorkBuddy §5.2.1 |
| `member-rule-check` | 校验成员 prompt 是否含角色定义/擅长领域/分析框架/输出模板/SendMessage | required（前 5 项）+ recommended（SendMessage） | BLOCKER / SUGGESTION | CODEBUDDY §4.5.3 |
| `prompt-completeness` | Agent MD frontmatter displayName / profession 字段 | recommended | SUGGESTION | CODEBUDDY §4.1 / WorkBuddy §4.2 |
| `display-text-quality` | displayDescription 字数、defaultInitPrompt 与 quickPrompts[0] 一致 | recommended | SUGGESTION | CODEBUDDY §3.5 / WorkBuddy §3.3 |
| `category-validity` | categoryId ∈ §十一 13 个分类 | required | BLOCKER | CODEBUDDY §十一 |
| `agent-name-semantics` | agentName 是否有业务语义（非 team-lead 等通用名） | required | BLOCKER | CODEBUDDY §3.3 / §十三-1 |
| `tools-field-completeness` | Agent frontmatter tools 字段要么不加要么写全 | required | BLOCKER | CODEBUDDY §4.1 / §十三-6 |
| `finance-compliance` | 金融类外露文案 / 免责声明 / 数据来源 | required | BLOCKER / SUGGESTION | CODEBUDDY §十八 |
| `security-hygiene-review` | 凭据硬编码、危险命令、内网域名、个人路径、平台路径、CDN @latest 等安全与通用性复核 | recommended | BLOCKER / SUGGESTION | 安全规则 / CODEBUDDY §十七 |
| `dependency-guide-check` | bin/scripts/环境变量/外部依赖的安装、版本、配置、验证说明 | recommended | BLOCKER / SUGGESTION | CODEBUDDY §五 / §六 / §十七 |
| `deep-quality-review` | 专家包 11 维度语义质量评审 | recommended | SUGGESTION | 本文 §七 / skill-reviewer v3.7.1 |


---

## 二、单条 ai_action 完整结构

```json
{
  "id": "AI-01",
  "action_type": "team-rule-check",
  "priority": "required",

  "target_file": "agents/xxx-team-lead.md",
  "reference_doc": "CODEBUDDY.md §4.4 / WorkBuddy专家开发规范.md §5.2.1",
  "instruction": "请阅读 CODEBUDDY.md §4.4 与 WorkBuddy专家开发规范.md §5.2.1，逐项判断 target_file 中是否包含：(1) 团队协作机制铁律章节 (2) 4 条正则 (3) 5 条红线 (4) 协作规则。若缺失任一项，列入 BLOCKER。",
  "context": {
    "expert_type": "team",
    "team_size": 4,
    "lead_agent": "xxx-team-lead",
    "members": ["a", "b", "c"]
  }
}
```

**字段说明**：

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✅ | 在本次 review 输出中唯一 |
| `action_type` | ✅ | 见上表 |
| `priority` | ✅ | required / recommended / optional |

| `target_file` | ✅ | 相对 `expert_dir` 的路径 |
| `reference_doc` | ✅ | 规范出处，便于报告引用 |
| `instruction` | ✅ | 给 LLM 的具体判断指令 |
| `context` | 推荐 | 辅助信息，如 expert_type、members 列表等 |

---

## 三、LLM 执行 ai_action 的标准流程

```
对每个 action ∈ ai_actions:
  Step 1: 已在第二步读完 reference_doc 指向的章节，无需重读
  Step 2: read_file(action.target_file) 取原文
  Step 3: 严格按 instruction 逐条对照规范
  Step 4: 输出结论：
          ✅ 全部通过 → 不进报告
          ❌ 关键项缺失 → 进 BLOCKER 区
          ⚠️ 部分缺失 → 进 SUGGESTION 区
  Step 5: 报告条目必须含「现状（原文引用）+ 规范依据 + 修复方案」
```

---

## 四、弹窗触发条件

### 一律 AI 自决（不弹窗）

- 形状层修复（字段顺序、编码归一）
- 字数精简（displayDescription 超 50 字）
- 翻译补全（description_zh 缺失但 description 完整）
- 唯一修复方式的违反项（如 `members[].role` 是对象而非字符串）

### 必须弹窗

| 触发场景 | 模板 |
|---------|------|
| 涉及修改业务 prompt 内容（如代写主理人铁律段落） | 模板 1：给具体提案让用户确认 |
| 金融合规违反需改外露文案 | 模板 1：给重写提案让用户确认 |
| 修复方式跨多个合理选项（如 displayDescription 重写多种风格） | 模板 2：多选 |
| 涉及不可逆修改（删除文件、覆盖历史 prompt） | 模板 3：兜底选项 |

### 弹窗模板

**模板 1：给提案让用户确认**

```json
{
  "title": "<plugin_name> - <决策点一句话>",
  "questions": [{
    "id": "<field>_<plugin_name>",
    "question": "AI 建议: <具体提案>\n规范依据: <章节>\n请选择:",
    "options": [
      "采纳并修复",
      "修改后采纳（请告诉我改什么）",
      "我手动处理",
      "跳过此项（报告标注）"
    ],
    "multiSelect": false
  }]
}
```

**模板 2：选项封闭多选**

```json
{
  "title": "<plugin_name> - <决策点>",
  "questions": [{
    "id": "<field>_<plugin_name>",
    "question": "AI 推荐: <推荐项> | 理由: <一句话>\n<context 关键信息>",
    "options": ["选项A", "选项B", "选项C"],
    "multiSelect": true
  }]
}
```

**模板 3：阻断兜底**

```json
{
  "title": "<plugin_name> - <blocker_id> 处理方式",
  "questions": [{
    "id": "blocker_<id>_<plugin_name>",
    "question": "<blocker_id>: <描述>\n上下文: <context>\nAI 建议: <建议>",
    "options": [
      "采纳 AI 建议并修复",
      "跳过此项（不上架）",
      "标记例外放行（报告记录）",
      "我手动处理，暂停等我"
    ],
    "multiSelect": false
  }]
}
```

### 批量聚合

- 单专家审查：先跑完所有自决部分，需要弹窗的合并成一组（每组最多 4 个 question_item）
- 单次审查最多弹 2 轮：scan 阶段 1 轮 + fix 阶段 1 轮
- 弹窗超过 2 轮则提示用户「本次决策较多，可在报告里批量手动处理」

---

## 五、安全/依赖/深度质量 ai_action 执行细则

### `security-hygiene-review`

- 必须读取 `context` 中命中的文件原文，不能只看扫描摘要。
- 真实凭据、密钥、token、password 硬编码：列 BLOCKER。
- 内网域名、个人路径、平台路径、危险 shell、CDN `@latest`：结合用途判断，通常列 SUGGESTION；若会导致专家不可用或存在明显供应链风险，可升级为 BLOCKER。
- 报告必须给出替代方案：环境变量、相对路径、公网降级、版本锁定、删除危险命令等。

### `dependency-guide-check`

- 触发条件：包内存在 `bin/`、`scripts/`、环境变量、外部 CLI/API 服务依赖。
- 必查项：安装命令、版本要求、环境变量名、获取方式、配置方式、验证命令。
- 核心依赖完全没有引导：BLOCKER；只有部分平台/部分变量缺失：SUGGESTION。

### `deep-quality-review`

- 唯一跳过条件：`context.skip_deep_review == true`。
- 必须阅读核心 `agents/*.md`、`README.md`、`skills/*/SKILL.md`，按 11 维度输出表格。
- 11 维度：AI 可执行性、路由/触发清晰度、上下文效率、容错降级、角色边界、团队编排、用户体验、受众适配、可移植性、领域准确性、可维护性。
- 所有结论均为 SUGGESTION，不改变总体上架结论。


