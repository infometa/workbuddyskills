# 执行规则速查 / 已知 quirk / 排查口径

> 以下规则**全部由 `scripts/resume_pipeline.py` 代码强制执行**（finalize / build-report），模型不得绕过脚本自行判定。此表用于理解脚本行为、对齐线上行为与排查问题，不要求模型在执行时背诵。

## 关键规则速查（红线）

1. **可见性由解析阶段决定**（analysis-resume-rules.md）：字段 SHOW ⟺ `值非空 || canHidden==false`；模块须在 `visibleModuleMap` 内且有值/非全可隐藏。**canHidden=true 的空白字段不进完整度分母、不记 NO_FILL**。两个方向都成立：**hidden=false 的空模块也要生成空白 SHOW 记录**（实习人群 workExperience → 6 条 NO_FILL）；**hidden=true 但解析出内容的模块照常 SHOW**（campusActivities / rewardRecords）。有内容分支**不过滤 showOnPage**（showOnPage=false 的字段空白也记 NO_FILL）。
2. **NO_FILL 按 `moduleCode+dataFieldCode` 聚合**，同一字段多条记录只记一次。
3. **NO_DATA 组合内逐模块独立判定**（不是组合全空才记）；网申人群用 `professionalSkills`，其余用 `professionalSkillsNonOnline`；模块无任何可见记录时仍记 NO_DATA（空流 quirk 保留）。
4. **学习能力只看 qualification**，不取 classRank（`classRank` 字段已从配置删除）；学历值须精确匹配（"大学本科"≠"本科"）。脚本在 finalize 时自动归一化（"本科"→"大学本科"，映射表 analysis-resume-rules.md §2.1）——模型填值时照抄原文即可。
5. **职场能力月数**：按 dataId 配对起止时间，`yyyy-MM` 解析，`betweenMonth(start,end,true)+1`；无结束时间的段不计；"至今"归一化为当前月。
6. **DESCRIPTION_SUGGEST**：LLM 输出解析不出 `suggestion` 即跳过（"暂无修改建议"不产生明细）；同字段多条按 dataSort 编"描述建议1/2/3"（脚本按描述建议编号）。批量任务单中跳过不写的任务 = 「暂无修改建议」。
7. **经历描述分**走独立的 LLM 评分一次调用（输入由脚本按 `模块名N：\n值\n` 拼好，隐藏模块已跳过），与 12 份诊断 Prompt 互不相关；校内活动因 key 错配（LLM 返回"校内工作"匹配不上"校内活动"）永不计分。
8. **报告排序**：模块按解析阶段赋的 sort 升序（显示模块在前按配置数组序，隐藏模块在后）；模块内 NO_DATA → NO_FILL（字段配置下标）→ DESCRIPTION_SUGGEST。

## 已知 quirk（原样保留）

- **校内活动评分 key 错配**：`resume-score-prompt.txt` Rules 中键为"校内工作"，配置 `scoreGptConfig.fieldList` 中模块名为"校内活动"，GPT 返回键匹配不上 → 校内活动**永不计分**。对应真实接口行为，不要"修复"。
- **score=100 无 beatPercent 区间**：`scoreList` 左闭右开，100 分命中不了任何区间 → beatPercent 为 null，HTML 显示"击败了 0% 的求职者"。
- **学历映射**：初中/小学在 `qualificationScoreMap` 中无 key → 学习能力得 0 分。
- **学习能力不含 classRank**：教育经历的 `classRank` 字段已从配置删除，不再参与完整度与学习能力评分。
- **NO_DATA 空流判定**：隐藏/无可见记录的模块仍会报"可以为你加分哦"（空流 quirk，保留）。
- **非网申类型**：`languageClassify`/`certificateName`/`softwareName` 只存在于网申版 `professionalSkills`，不在非网申的 visibleModuleMap → 专业能力只能命中 `professionalSkillsNonOnline` 三字段（languageSkill / softwareOperation / qualificationCertificate）。
- **诊断 prompt 原文 quirk**（见 diagnose-prompts.md）：校内工作 prompt（1760）Addition 3 笔误为"实践经历"；爱好特长 prompt（1761）`## Rules：` 全角冒号。JSON 中按原文保留，不修正。
- **成绩排名选项校验（classRank）不参与任何逻辑**：字段已从配置删除，skill 不实现。
- **LLM 残余主观差异**：诊断建议与评分的具体话术/分值存在 LLM 主观性，属不可消除差异（尤其 selfEvaluation 文案等）。判定纪律已尽力收敛（见 diagnose-prompts.md）。

## 排查口径

| 现象 | 排查方向 |
|---|---|
| score / beatPercent 与预期不符 | 确认 `--resume-type` 键名、filled 是否漏填（尤其 qualification 原文、workCity/position/address、技能模块）；score=100 无 beatPercent 属正常 quirk |
| NO_FILL / NO_DATA 明细缺失或多余 | 对照红线 1/2/3：字段是否 canHidden、模块是否在 visibleModuleMap、showFields 状态 |
| 描述建议没有出现 | 检查 llm.json 里该 (moduleCode, fieldCode, dataSort) 是否遗漏；判"暂无修改建议"= 正常跳过 |
| 经历描述分为 0 | 检查 scoreGptInput 是否为空（隐藏模块跳过）；校内活动永不计分属正常 quirk |
| emit-llm-tasks 报缺 Prompt | 确认 diagnose-prompts.json 与 resume-score-config.json 的 diagnosePromptMap 同步 |
| HTML 占位符未替换 | orchestrate verify 会直接报错；手工渲染时对照 diagnose-output-template.md 第 3 节 |
| Windows heredoc 解析失败 | 一律用 Write 工具写 tmp/*.json + 文件参数传路径，不要用 `<<'JSON'` |

## 线上配置同步

任一权威配置 / Prompt 原文变更时，同步更新对应 references（见 SKILL.md 资源表），并跑一次冒烟样例（scripts 冒烟流程见 diagnose-output-template.md 或对照 `report_lyx` 基准）。
