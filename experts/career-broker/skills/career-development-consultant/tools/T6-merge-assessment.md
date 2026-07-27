# T6 · 测评结果回流 profile

## 触发条件
用户贴回来 DNA 结果码（教练用正则识别到 `DNA:...|A:...|S:...|P:...`）。

> **职责边界**：本工具只做「写盘 + 简短 ack」，**不做深度解读**。
> 如果用户在 ack 之后追问「帮我看看这个 DNA 怎么样」「八锚分别什么意思」「我适合什么方向」——
> **这些是 ai-career-agent skill 的职责**。教练应识别意图，由主入口路由到 ai-career-agent。
> 教练自己继续走 12 步主流程，**不复刻测评解读**。

---

## 调用链

> **脚本位置已迁移**到 ai-career-agent skill。本工具调它两个脚本。

```bash
# 1. 解析 DNA
python skills/ai-career-agent/scripts/parse_result_code.py "<DNA 全串>"
# 输出 JSON 含 result.{anchors, scales, psy_state, ...}

# 2. 把 result 字段抽出来调 merge
python skills/ai-career-agent/scripts/merge_assessment_into_profile.py \
  --rtx <用户 rtx> \
  --result-json '<上一步输出的 result 部分>'
```

执行后：
- `~/.workbuddy/career-broker/<rtx>/profile.json` schema 升 v2.1
- 新增顶层字段 `assessment` 含 dna_short / top_anchors / top_scales / psy_state
- 不动原有 skills / experiences / traits

---

## 教练动作（静默执行，不让用户感到"流程"）

```
1. 收到 DNA 码 → 后台执行 parse + merge
2. 给用户一个**简短**的 ack（≤ 50 字）：

  "拿到了，<TEC×CR> 组合——你冰山下确实是<一句结论>的味道。"

3. 立刻接回刚才的对话（不要让用户感觉打断）：

  "我们继续刚才的话题——你刚说<复述用户最后一句>。"
```

**禁止**：
- 长篇 dump 测评结果（让用户看 8 锚 / 6 维 / 心理状态全列表）
- 跳出对话节奏说"我已成功保存你的测评结果"
- 在用户没问的情况下解读 P 维度心理状态（很敏感）

---

## 一句话结论怎么生成

根据 top_anchors 和 psy_state，**用模板**生成（不要让 LLM 自由发挥）：

```
top_anchor 主导词：
  TEC 专业深耕 → "想在专业里继续深"
  CHL 挑战驱动 → "需要硬骨头才有劲儿"
  ENT 创业自主 → "想要自己说了算的空间"
  MGT 管理影响 → "想带团队 / 影响更多人"
  AUT 独立自由 → "想要自己掌控节奏"
  SER 服务奉献 → "做的事得对人有用才有意义"
  SEC 稳定生活 → "想稳一点"
  LIF 生活平衡 → "工作之外的部分一样重要"

psy_state.B 倦怠：
  ≥ 3.5 → "+但最近能量不太够"
  < 2.5 → "+状态不错"
  其他  → 不提
```

---

## 隐私

- DNA 短码（如 TCA-CR/AN）写入 profile.json
- 原始 DNA 全串只在 raw/ 留底，不进 profile.json
- assessment 整段标 P0 仅本地
- 上云时 cloud_payload.json 只包含**提炼后的一句话结论**，不含 anchors 分数

---

## 已实测

```
DNA: DNA:TCA-CR/AN|A:TEC8CHL7ENT5MGT4AUT3SER3SEC2LIF1|S:CR4AN3CN2TC2SY1EM0|P:B2.5O4.0E3.5
解析结果：
  - top_anchors: TEC(8) / CHL(7) / ENT(5)
  - top_scales:  CR(4) / AN(3)
  - psy_state:   B=2.5(轻倦怠) / O=4.0 / E=3.5
profile.json schema 升 v2.1，assessment 字段已写入 ✅
```
