<!-- AGENT READ THIS FIRST -->
# ⚠️ Agent 指令（非用户内容，务必先读完本节）

你正在阅读**任务状态机文档**。请按以下顺序工作：

1. 定位下方「全局信息」中的 **当前状态** 和 **运行模式** 字段
2. 你只能执行**当前状态**指向、且**未被运行模式跳过**的步骤
3. 每执行完一步，必须：
   - 在本文档对应步骤处把 `[ ]` 改为 `[x]`
   - 填入「完成时间」「产出文件」「关键指标」
   - 调用 `plan_gate.py --mark-done N` 原子更新全局状态
4. 在回复用户时，必须附带「📋 执行计划状态」回显块

**违反上述契约 = 任务失败，必须回滚重做。**
<!-- END AGENT INSTRUCTIONS -->

---

# 漏洞分析执行计划

## 全局信息

- **任务 ID**: {{TASK_ID}}
- **当前状态**: **STEP_1_PENDING**
- **运行模式**: **{{MODE}}**  <!-- extract-only | with-intel | with-knowledge | full -->
- **启动时间**: {{START_TIME}}
- **最后更新**: {{START_TIME}}
- **任务目录**: `{{TASK_DIR}}`  <!-- 所有产物都落在此目录，互不干扰 -->
- **输入报告**: {{INPUT_REPORT}}
- **Providers 配置**: {{PROVIDERS_PATH}}
  - knowledge_provider.enabled: {{KB_ENABLED}}
  - intel_provider.enabled: {{INTEL_ENABLED}}

> 状态机取值：
> `STEP_1_PENDING` → `STEP_2_PENDING` → `STEP_3_PENDING` → `STEP_4_PENDING` → `DONE`
> 跳过分支：`STEP_N_SKIPPED`（Provider 未启用时由 `--skip-step N` 设置）
> 失败分支：`STEP_N_FAILED`（由 `--mark-failed N` 设置）

---

## 步骤 1：提取漏洞数据

**状态**: `[ ]` ⏸️ PENDING

**前置依赖**: 无

**门禁检查**（开始前必须全部 YES）:
- [ ] 输入报告文件存在且可读？
- [ ] 任务目录 `{{TASK_DIR}}` 已创建（由 `--init` 自动完成）？

**执行契约**:
- ✅ 必须调用 `scripts/extract_vulns.py`
- ❌ 禁止调用白名单外的脚本
- ❌ 禁止跳过本步直接做本地分析

**完成判定**:
- [ ] `vulnerabilities.json` 已生成
- [ ] JSON 包含 `vulnerabilities` 数组且 `len > 0`

**待回填字段**:
- 开始时间: ________
- 完成时间: ________
- 报告格式: ________
- 漏洞总数: ________
- 产出文件: ________

---

## 步骤 2：查询知识库 Provider 🔒 LOCKED

**状态**: `[ ]` 🔒 LOCKED（被步骤 1 阻塞）

**是否参与本次运行**: {{KB_ENABLED}}（false 时本步骤将被 `--skip-step 2` 自动跳过）

**解锁条件**: 步骤 1 状态变为 DONE

**前置依赖**:
- [ ] 步骤 1 完成

**门禁检查**:
- [ ] `vulnerabilities.json` 可读？
- [ ] CVE 去重列表已生成（`unique_cves.json`）？
- [ ] `knowledge_provider.enabled = true` 时：MCP server `<knowledge_provider.server_name>` 可用？

**执行契约**（**关键：必须以 CVE ID 去重后再查询**）:
1. ✅ 先调用 `scripts/dedupe_cves.py` 生成唯一 CVE 列表（**始终执行**）
2. ✅ 若 Provider 启用：对每个**唯一** CVE 调用 `use_mcp_tool(serverName=<knowledge_provider.server_name>, ...)`
3. ✅ 同一 CVE 只查询一次，结果 fan-out 回所有持有该 CVE 的漏洞记录
4. ❌ 禁止用本地 Python 统计替代真实 Provider 查询
5. ❌ 禁止对同一 CVE 重复调用 Provider
6. ❌ 禁止调用 `mcp_get_tool_description` / `mcp_list_tools` 等伪工具名
7. ❌ 禁止硬编码 token / api_key，必须用 `providers.yaml` 的 `${ENV_VAR}` 占位符

**完成判定**（Provider 启用时）:
- [ ] `unique_cves.json` 已生成
- [ ] `knot_results.json` 已生成
- [ ] 所有唯一 CVE 都有查询记录（命中或未命中）
- [ ] 命中率已记录到本文档

**完成判定**（Provider 未启用时）:
- [ ] `unique_cves.json` 已生成
- [ ] `knot_results.json` 写入空骨架（`provider_disabled: true`）
- [ ] 状态推进到 STEP_2_SKIPPED 或 STEP_3_PENDING

**待回填字段**:
- 开始时间: ________
- 完成时间: ________
- 唯一 CVE 数: ________
- 知识库命中数: ________
- 命中率: ________
- 未命中 CVE 数（转步骤 3）: ________

---

## 步骤 3：查询威胁情报 Provider 🔒 LOCKED

**状态**: `[ ]` 🔒 LOCKED（被步骤 2 阻塞）

**是否参与本次运行**: {{INTEL_ENABLED}}（false 时本步骤将被 `--skip-step 3` 自动跳过）

**解锁条件**: 步骤 2 状态变为 DONE 或 SKIPPED

**前置依赖**:
- [ ] 步骤 2 完成或跳过
- [ ] `knot_results.json` 中存在未命中的 CVE（或 provider_disabled = true）

**门禁检查**:
- [ ] 从 `knot_results.json` 筛选出 `found=false` 的 CVE 列表？
- [ ] `intel_provider.enabled = true` 时：MCP server `<intel_provider.server_name>` 可用？

**执行契约**:
1. ✅ 仅对知识库**未命中**的唯一 CVE 调用 `use_mcp_tool(serverName=<intel_provider.server_name>, ...)`
2. ✅ 若无 CVE 编号，使用漏洞名称关键词查询（精简版，去版本号）
3. ❌ 禁止对知识库已命中的 CVE 重复查询情报源（浪费配额）

**完成判定**（Provider 启用时）:
- [ ] `xti_results.json` 已生成
- [ ] 所有未命中 CVE 都有情报查询记录

**完成判定**（Provider 未启用时）:
- [ ] `xti_results.json` 写入空骨架（`provider_disabled: true`）
- [ ] 状态推进到 STEP_3_SKIPPED 或 STEP_4_PENDING

**待回填字段**:
- 开始时间: ________
- 完成时间: ________
- 查询 CVE 数: ________
- 情报命中数: ________
- 有公开利用的高危数: ________

---

## 步骤 4：生成综合分析报告 🔒 LOCKED

**状态**: `[ ]` 🔒 LOCKED（被步骤 3 阻塞）

**解锁条件**: 步骤 3 状态变为 DONE 或 SKIPPED

**前置依赖**:
- [ ] 步骤 1 完成
- [ ] 步骤 2、3 完成或跳过
- [ ] `vulnerabilities.json` 必须存在

**门禁检查**:
- [ ] `vulnerabilities.json` 存在？
- [ ] `unique_cves.json` 存在或 mode=extract-only？
- [ ] `knot_results.json` 存在或 KB_ENABLED=false？
- [ ] `xti_results.json` 存在或 INTEL_ENABLED=false？

**执行契约**:
1. ✅ 调用 `scripts/render_report.py` 自动渲染（统计数字由代码算）
2. ✅ 报告模板遵循 `assets/report_template.md`
3. ✅ 未启用的 Provider 章节渲染为"未启用"提示，不留空白
4. ❌ 禁止凭"本地统计"就宣布完成，必须真正融合已启用 Provider 的数据

**完成判定**:
- [ ] `漏洞分析报告_YYYY-MM-DD_<来源>.md` 已生成
- [ ] 报告包含 7 个规定章节
- [ ] 已启用 Provider 的章节都有真实数据引用

**待回填字段**:
- 开始时间: ________
- 完成时间: ________
- 报告文件路径: ________
- 报告字数: ________

---

## 🚨 门禁规则（Agent 必读）

1. **顺序门禁**：必须按 1→2→3→4 顺序，当前全局状态不是 `STEP_N_PENDING` 时禁止执行 N+1
2. **回写义务**：每次步骤完成必须立即调用 `plan_gate.py --mark-done N` 或 `--skip-step N`
3. **自检规则**：每次准备执行新步骤前，**必须**先调用 `plan_gate.py --check-step N`
4. **去重义务**：步骤 2/3 的 Provider 查询必须基于 `unique_cves.json` 的去重列表
5. **跳过判定**：当 Provider `enabled=false` 时使用 `--skip-step N`，**不是** `--mark-failed`
6. **违规判定**：跳步/重复查询/虚假打勾/硬编码密钥 = 任务失败

---

## 📋 执行历史（Agent 每次更新都在这里追加一行）

| 时间 | 动作 | 结果 | 备注 |
|------|------|------|------|
| {{START_TIME}} | 计划初始化 | OK | 模式={{MODE}}，等待步骤 1 |
