# 聚焦模式（--focus high）

> 引用方: commands/project.md（`focusMode == "high"` 时 Read）
> 适用范围: project + light/deep
>
> 聚焦模式仅关注可直接远程造成命令执行(RCE)和大量信息泄漏的高危风险，
> 以及能组合达成此场景的线索。

---

## 设计原则

1. **确定性兜底**：`verifier.py focus-filter` 纯函数做最后把关，不依赖 LLM
2. **信号匹配**：verifier Agent 用结构化信号匹配替代开放式推理（弱模型友好）
3. **按需加载**：聚焦逻辑全部在本文件，commands/project.md 仅做入口跳转

---

## 阶段1: 探索

不变。需全量索引以发现组合线索。

> 聚焦规则定义：Read `${CODEBUDDY_PLUGIN_ROOT}/resource/high-focus-sinks.yaml` 获取黑名单和组合线索类型。

输出摘要追加：

```
  **聚焦模式已启用**：仅关注高危以上风险（远程直接利用 / RCE / 大量数据泄漏）
```

---

## 阶段2: 扫描

### Light 模式：Sink 过滤

聚焦模式下，阶段2仅分析 S1(critical) + S2(high) 级别的 Sink：

```bash
# 替代原有 sinks-by-severity --limit 30
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/index_db.py" query \
  --batch-dir "$batch_dir" \
  --preset sinks-by-severity --limit 30 \
  --min-severity-level 2
```

> 若 `--min-severity-level` 参数不被 `index_db.py query` 支持，使用 `--preset sinks-by-severity --limit 30` 后由编排器手动过滤 `severity_level <= 2` 的结果。

聚焦模式下 LLM 内联扫描：
- **仅分析 S1/S2 级别的 Sink**，直接跳过 S3/S4
- 对每个高危 Sink，检查 ±30 行上下文是否存在组合线索 Sink
  （按 `high-focus-sinks.yaml > combo_clue_types` 匹配）
- 若存在组合线索，在高危 finding 追加 `comboClue` 字段

输出摘要追加：

```
  **[2.0]** 聚焦模式过滤：Sink 候选从 **{totalSinkCount}** 收敛至 **{highFocusSinkCount}** 个高危 Sink
```

### Deep 模式：子 Agent 聚焦指令

在启动 vuln-scan / logic-scan / red-team 的 Task prompt 中追加以下聚焦指令：

```
[聚焦模式] scanFocus = "high"
仅产出 severity 为 critical 或 high 的 finding。
对于 medium 级别的类型（SSRF、路径穿越、访问控制缺失、文件上传、信息泄露），
仅在与高危 Sink 位于同一文件或同一调用链时，作为 comboClue 附加输出。
禁止产出独立的 Medium/Low finding。
```

---

## 阶段3: 验证

### Light 模式

编排器内联验证时，对每个 Critical/High finding 回答三问（信号匹配，见 §信号速查表）。
不确定时 → 降级 medium → 由后续 focus-filter 排除。

### Deep 模式

启动 verifier Agent 时注入聚焦挑战 prompt（详见 `agents/verifier.md > 聚焦挑战模式`）。

> **关键约束**：聚焦模式下 verifier Agent **不读取** `chain-verify-results.json` 和
> `challenge-results.json`，保持判断独立性。

### 确定性过滤（Light/Deep 共用）

merge-verify 完成后，**必须**执行确定性聚焦过滤：

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/scripts/verifier.py" focus-filter \
  --batch-dir "$batch_dir"
```

> focus-filter 是纯函数，不依赖 LLM / index.db。
> 输入: `merged-verified.json`
> 输出: `focus-filtered.json`（保留）、`focus-excluded.json`（排除 + 原因）
> 更新: `merged-verified.json`、`summary.json`

验证通过后输出：

```
  **[3.X]** 聚焦过滤完成：保留 **{kept}** 个高危 finding，排除 **{excluded}** 个非聚焦风险
```

---

## 阶段4: 报告

使用 focus-filter 后的 `merged-verified.json` 生成报告。

> 门禁规则不变（`gate-policy.yaml` 本身已有 `high_severity_threshold` 规则）。
> 聚焦模式下 `mediumRisk` 和 `lowRisk` 计数为 0（被聚焦过滤），
> `summary.json` 中新增 `focusFiltered` 字段记录排除数量。

输出摘要追加：

```
聚焦模式：输出 **{N}** 个高危 finding（已排除 **{M}** 个非聚焦风险），**{C}** 条组合攻击线索
```

---

## 信号速查表

编排器/verifier Agent 聚焦挑战时使用。**匹配信号 → 判定结论，不要求开放推理。**

### 第一问：公网可达？

| Grep 目标 | 代码信号 | → 结论 |
|----------|---------|--------|
| 入口注解/装饰器 | `@InternalOnly` / `@RequireInternalIp` / `internal_only` | internal_only |
| IP 白名单 | `allowlist` / `whitelist` 仅含 `10.` `172.16-31` `192.168.` | internal_only |
| 来源校验 | `req.remote_addr` / `request.remoteAddress` 仅允许内网段 | internal_only |
| 触发方式 | `@Scheduled` / `@Cron` / MQ consumer / 无 HTTP 入口 | internal_only |
| K8s 网络 | `ClusterIP` / Service 间通信 / 无 Ingress | internal_only |
| 容器网络 | 仅 `localhost` / `127.0.0.1` 绑定 | internal_only |
| 以上无一命中 | — | 假设公网可达 |

### 第二问：可直接利用？

| Grep 目标 | 代码信号 | → 结论 |
|----------|---------|--------|
| 认证注解 | `@PreAuthorize` / `@RequireAuth` / `@Authenticated` | require_auth |
| Session 校验 | `req.session` / `getSession()` / JWT cookie | require_auth |
| 权限校验 | `@RolesAllowed` / `hasRole(` / `require_admin` | require_privilege |
| CSRF 防护 | `_csrf` / `@CSRF` / 状态变更需 token | require_user_context |
| 回调验签 | webhook callback + 签名校验 | require_callback_sig |
| 多因素 | 需 MFA / 二次验证 / 手机验证码 | require_mfa |
| 以上无一命中 | — | 假设可直接访问 |

### 第三问：危害过高？

| Grep 目标 | 代码信号 | → 结论 |
|----------|---------|--------|
| DB 权限 | `readonly` / `SELECT_ONLY` / 只读连接串 | limited_db_privilege |
| 容器限制 | `SecurityContext` / `runAsNonRoot` / `readOnlyRootFilesystem` | sandboxed |
| 命令范围 | 命令白名单仅含安全指令 / 参数强校验 | limited_command_scope |
| 数据范围 | Sink 输出仅限当前用户自己的数据 | self_contained |
| 以上无一命中 | — | 假设危害确实过高 |

### 判定矩阵（强制）

| 公网可达 | 可直接利用 | 危害过高 | → challengeVerdict |
|---------|-----------|---------|-------------------|
| 是 | 是 | 是 | confirmed |
| 是 | 是 | 否 | downgraded（降一级） |
| 是 | 否 | — | downgraded（降一级） |
| 否 | — | — | downgraded（reason: internal_only） |

---

## 错误处理

1. focus-filter 执行失败 → 输出 warning，降级使用未过滤的 merged-verified.json，不阻塞报告生成
2. high-focus-sinks.yaml 不存在 → 使用内置默认黑名单（verifier.py 硬编码），不中断流程
3. comboClue 发现失败 → 仅输出警告，不影响高危 finding 产出
