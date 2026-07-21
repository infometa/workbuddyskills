# 增量合并规则

当有新材料加入时：

1. 先保留原有高置信结论
2. 用新证据补充细节、例子和边界条件
3. 只有在新材料直接推翻旧结论时才改写原结论
4. 优先更新以下部分：
   - Judgment 中的追问和否决标准
   - Management 中的汇报与报风险规则
   - Persona 中的口头禅、压力状态和雷区

输出必须分成三块：

- judgment_patch
- management_patch
- persona_patch
