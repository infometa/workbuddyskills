# 半自动化 CLI 调用示例

> v0.2 起 SKILL.md 调用方式段从 body 拆出（v0.7 R3 优化），减少 body 体积。

```bash
SKILL=.cursor/skills/knowledge-framework-builder

# Step 1 · 输入闸门：验证 + 模式 / 深度判定
python3 $SKILL/scripts/validate_input.py \
    --input input.json --out build_plan.json --pretty

# Step 2-3 · LLM 按 build_plan 的 next_step_for_llm 产出 framework_tree（单顶层 dict）
#         → 写入 tree.json + (可选) questions.json

# Step 4 · 装配：自动算 tree_stats / provenance_summary / warnings，校验 100/5 上限
python3 $SKILL/scripts/assemble_result.py \
    --input input.json --tree tree.json --questions questions.json \
    --out result.json --pretty

# Step 7 · Provenance 审计（topic_only → skipped；material_first/hybrid → ngram 匹配）
python3 $SKILL/scripts/verify_provenance.py \
    --result result.json [--material textbook.md notes.md] \
    --out provenance-audit.json --pretty

# Step 8 · 4 格式渲染（banner 自动驱动）
python3 $SKILL/scripts/render_outputs.py result.json
#  → framework.md / framework.markmap.html / framework.mermaid.md / framework.opml
```

**端到端 dogfood 参考**：`demos/knowledge-framework-builder/result-fixtures/topic-only-cet/`

所有 5 脚本退出码语义化（`0=ok / 1=参数错 / 2=约束违反或非法输入`），便于 CI 集成。

## 路线图历史

| 版本 | 关键特性 |
|---|---|
| v0.1 | 需求文档 + Skill 骨架（`SKILL.md` + `_skill_meta.json` + 目录占位）|
| v0.2 | 跑通 topic_only × skim 全链路（4 脚本 + 5 references + topic-only-cet dogfood）|
| v0.3 | 加入 guided 模式（5-10 重点节点 + 200-500 字讲解）|
| v0.4 | 加入 deep + 概念依赖（全节点讲解 + 6 类依赖箭头）|
| v0.5 | 用户材料模式 + N-gram 真闭环（material-markdown-ml fixture 32 high / 1 故意 failed）|
| v0.6 | HTML 报告模板 + CP-A/B/C/D 检查点设计 |
| v0.6.1 | skill-assistant blind_hybrid 评审：补 NEVER 列表 + description 加速器 |
| v1.0 | 5 条护城河完整：三档 + 概念依赖 + Provenance + 多格式 + 子 Skill 接口 |
| v1.1 | 备考扩展（内置 CET-4/6 / 考研政治 / 408 课纲 + Anki CSV / .xmind 输出）|
| v1.2 | 学习路径推荐（按依赖关系生成 N 周学习计划）|
| v2.0 | 增量更新（用户在导图上手动改 → Skill 不覆盖）|

> v0.6.1 起本节移到 references/，body 不再追加版本细节。
