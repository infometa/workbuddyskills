# 阶段5 · 验证（Verify）

> **目标**：注册成功后，验证 MCP 工具**能否成功调用**、**权限是否符合预期**，作为上线前的质量门禁。
> **约束**：本阶段只做编排，核心测试委派 `modules/mcp.md#test`，能力专属测试（如 authz 权限用例）委派对应能力的 `#test` 锚点。

---

## 5.0 入口

| 来源 | 是否执行 §5 |
|------|-------------|
| 路线 A / C / B选3（完整部署后） | ✅ 执行 |
| 路线 B选1/2（仅改 skill/prompt，未动 mcp_server/ 与能力产物） | 跳过，直接输出完成 |

---

## 5.1 准备测试输入

1. 定位 Bridge 可达地址：
   - 本机：`http://127.0.0.1:$(cat {mcpDir}/.bridge-port)/mcp`
   - 容器内：通过 deploy provider 的 `remote-exec` 在容器侧执行（读 `.bridge-port`）
2. 已启用能力清单：读 `boost-state.json` 的 `capabilities` 段，获取本次启用的能力及其 `configRef`
3. 各能力 test 输入：按 `modules/registry.md` §3.2 的 `testScript` 列，准备各能力 test 脚本所需的环境变量

> 测试身份（authz 专用，其他能力按需）：`ADMIN_STAFF`（名单/DB 样例，取不到则询问用户给一个）、`NONADMIN_STAFF`（默认合成名）。

---

## 5.2 执行测试

> **核心层与能力层分离**（见 `modules/registry.md` §7）：
> - **核心测试**（L1 连通 + L2 可调用）：`test-mcp.sh` 一次调用，所有应用必跑，报告 `.agent/mcp-test-report.json`
> - **能力测试**（L3 及各能力专属）：按注册表顺序，对每个 `enabled=true` 的能力调用其 `#test` 锚点
>   - 有 `testScript` 的能力：模型传环境变量调脚本（如 authz 调 `test-authz.sh`）
>   - 无 `testScript` 的能力：复用核心脚本的能力层 hook（如 authz 通过 `AUTHZ_MANIFEST` 触发 `test-mcp.sh` L3）

### 5.2.1 核心测试（L1 + L2，所有应用必跑）

```bash
MCP_LOCAL_URL="http://127.0.0.1:$(cat {mcpDir}/.bridge-port)/mcp" \
REPORT_OUT="{projectDir}/.agent/mcp-test-report.json" \
bash ${SKILL_DIR}/scripts/test-mcp.sh
```

### 5.2.2 【CAPABILITY HOOK · test】（按已启用能力逐一执行）

> 按 `modules/registry.md` §3.1 能力清单表顺序，对每个 `enabled=true` 的能力调用其 `#test` 锚点。
> 主线不硬编码任何能力名——各能力的 test 执行方式见对应 `modules/{name}.md#test`。

**执行方式**：

1. 读 `boost-state.json` 的 `capabilities` 段，获取本次启用的能力清单
2. 按 `modules/registry.md` §3.1 能力清单表顺序，对每个 `enabled=true` 的能力：
   - 加载 `modules/{name}.md`，读取其 `#test` 锚点定义的执行方式
   - 有 `testScript`（注册表 §3.2 声明）：模型传环境变量调脚本，环境变量清单见各模块 `#test` 段
   - 无 `testScript`：模型按 `#test` 锚点描述直接执行（如复用核心脚本的 hook 机制）
3. 各能力测试报告独立落到 `.agent/{name}/test-report.json`（路径见各模块 `#test` 段定义）
4. 收集各能力 `summary.gate`，汇入 §5.3 门禁判定

> 三层测试语义与破坏性防护见 `modules/mcp.md#test`。
> 容器内测试：把环境变量与命令通过 `scripts/remote-exec.sh` 在容器侧执行同一脚本。
> 后续新增能力：按其 `modules/{name}.md#test` 定义的方式执行，本文件无需改动。

---

## 5.3 结果处理

**门禁汇总**：`gate = mcp.gate AND 所有能力 gate`

- 各报告路径：
  - 核心：`.agent/mcp-test-report.json` 的 `summary.gate`
  - 各能力：`.agent/{name}/test-report.json` 的 `summary.gate`（路径见各模块 `#test` 段定义）
  - 例外：若某能力的 test 当前合并到核心报告（如 authz 复用 `test-mcp.sh` L3），则读核心报告对应段
- `gate=true` → 质量门禁通过，进入 §5.4 完成。
- `gate=false` → 按失败层定位：
  - 核心 L1 失败 → `troubleshooting.md` §1/§3
  - 核心 L2 工具调不通 → 回 §3 修 `PROJECT_TOOLS` / 补新增 API
  - 某能力 test 失败 → 见该能力 `modules/{name}.md#test` 的结果判定表，回 §3 调对应 `#inject` 修复
  - 修复后重跑对应 test 脚本（幂等），直至通过或用户接受当前结果。

> 未启用某能力时，其 test 不执行，gate 不含该项。

---

## 5.4 最终输出（🔴 gate 通过或用户接受后）

读取 `{projectDir}/.deploy-state.json`（page-deliver 部署时写入），取 `ip` 和 `port` 字段拼为预览地址 `http://{ip}:{port}`。

**输出模板**：

```
✅ 完成

🧠 Agent    ：{agentName} (已加载)
🔌 MCP 工具 ：{toolCount} 个 · L2 可调用 {l2Pass}/{l2Total}
🔐 能力     ：{按已启用能力逐项展示 test 结果}
              如：🔐 API 鉴权 · L3 {l3通过}/{l3总数}
📅 定时任务 ：对 Agent 说「每周一上午9点生成周报」
🌐 预览     ：[点击预览](http://{ip}:{port})
📌 后续     ：运行 /page-upload 命令完成应用上线
```

> 至此主线结束。boost-state.json 已在 §4 注册时写入 `state=deployed`。
