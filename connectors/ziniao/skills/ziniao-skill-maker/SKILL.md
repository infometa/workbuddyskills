---
name: ziniao-skill-maker
version: 1.2.0
description: "创建 ziniao-cli 自定义 Skill。当用户要把紫鸟浏览器自动化流程封装成可复用 Skill、编排多步页面操作、首次无 SOP 需先 explore、或稳定后加 Python 运行时时使用。"
metadata:
  requires:
    bins: ["ziniao-cli"]
---

> 连接器登录已由 WorkBuddy 完成。不要运行 `ziniao-cli config init`。命令返回未登录或 API Key 无效时，请用户在 WorkBuddy 里重新连接。本 Skill 只教如何产出浏览器自动化 Skill。`scripts/scaffold.py` 与本文件同目录。

# Skill Maker

教 Agent **如何产出 Skill**（必要时加 Runtime），不是替用户写具体业务。

```text
ziniao-skill-maker/
├── SKILL.md                              # 本文件：方法论
└── scripts/
    ├── scaffold.py                       # 生成 Skill + Runtime 骨架
    └── runtime_client.template.py        # ZiniaoClient 模板（复制进 runtime/）
```

`scripts/scaffold.py` 与本 `SKILL.md` 同目录。安装后可能在 `~/.agents/skills/ziniao-skill-maker`、`~/.claude/skills/ziniao-skill-maker` 或 `~/.cursor/skills/ziniao-skill-maker`。**用本文件所在目录**，不要写死 `~/.agents/...`。

---

## 两种交付形态

| 形态 | 何时 | 产出 |
|------|------|------|
| **路径 A · 规范 Skill** | ≤5 步、一次性、DOM 未稳定 | 仅 `SKILL.md`（+ 按需 references） |
| **路径 B · Skill + Runtime** | 多步、重复跑、输入可结构化 | `scaffold.py` 生成的 Kit |

**用户首次往往没有 SOP** → 路径 B 默认 `options.phase=explore`（只采集 raw/截图），禁止首次就跑解析并产出业务结论 JSON。

路径 B 需要本机 `python`（3.10+）。路径 A 不需要。

---

## 路径 A · 规范 Skill

不要跑 scaffold。文件放在 `skills/ziniao-<name>/SKILL.md`。用来编排 **店铺浏览器 + 页面操作**。不要把部门、员工、账号、角色、设备等服务端 API 写进这条路径；本连接器不提供这些 Skill。

### 调研页面能力

先读 [ziniao-store](../ziniao-store/SKILL.md) / [ziniao-page](../ziniao-page/SKILL.md)。不确定参数时看 `--help`，不要猜。

```bash
ziniao-cli store --help
ziniao-cli page --help
ziniao-cli zclaw tools
```

优先级：`store` / `page` 快捷命令 > `zclaw invoke`。已知且唯一的 selector **写进 Skill 步骤**，优先 id / name / `data-testid` / ARIA；执行前用 `page query` 确认命中数。DOM 变了就更新这份 Skill，不要每次从零重探。

### SKILL.md 模板

```markdown
---
name: ziniao-<name>
version: 1.0.0
description: "<功能描述>。当用户需要<触发场景>时使用。"
metadata:
  requires:
    bins: ["ziniao-cli"]
---

# <标题>

**CRITICAL — 开始前 MUST 先用 Read 工具读取 [`../ziniao-shared/SKILL.md`](../ziniao-shared/SKILL.md)**

店铺未打开时先用 [ziniao-store](../ziniao-store/SKILL.md) 取得 `store-id`，页面操作按 [ziniao-page](../ziniao-page/SKILL.md)。

## 步骤

\```bash
# Step 1: 确认/打开店铺，记下 store-id
ziniao-cli store resolve --name "<店铺名>"
ziniao-cli store open --store-id "<id>"

# Step 2: 导航（returncode 0 即成功，成功信息可能在 stderr）
ziniao-cli page visit --store-id "<id>" --url "<url>" --wait-until load

# Step 3: 读取或交互（已知 selector 写在步骤里）
ziniao-cli page query --store-id "<id>" --selector "<css>"
ziniao-cli page click --store-id "<id>" --selector "<css>"
ziniao-cli page content --store-id "<id>" --content-format structured
\```

写入/保存/提交前确认用户意图。说明步骤间如何传递 `store-id`，以及失败时停在哪一步。selector 失效时先 `page query` 再改 Skill，不要沿用旧判断。

## 参考

- [ziniao-shared](../ziniao-shared/SKILL.md) — 认证、doctor、安全
- [ziniao-store](../ziniao-store/SKILL.md)
- [ziniao-page](../ziniao-page/SKILL.md)
```

---

## 路径 B：scaffold 产出结构

```bash
python "<本 Skill 目录>/scripts/scaffold.py" \
  --name my-flow --output ./kits --title "My Flow"
```

```text
ziniao-my-flow-kit/
├── SKILL.md
├── README.md
├── run.ps1 / run.sh
├── data/input.json              # 默认 phase=explore；浏览器场景填 items[].storeId
├── references/                  # 契约、策略、validated-reads 模板
├── scripts/                     # read_input, preflight_validate
└── runtime/
    ├── ziniao_client.py         # 从 runtime_client.template.py 复制
    ├── my_flow_core.py          # 区段编排 + final_gate
    └── run_my_flow.py
```

Agent 填业务：**references 契约、core 区段、validated-reads**；不要改 skill-maker 本身。

---

## 何时从 explore 切到 execute

须全部满足后再改 `data/input.json` → `"options": { "phase": "execute" }`：

1. 同流程 **explore 或 Agent 实跑 ≥2 次**，步骤顺序稳定
2. 完成信号可编程（非「flat text 猜数字」）
3. `output/validated-reads.json` 存在且 **`meta.readyForExecute=true`**
4. 解析逻辑在 **`runtime/*_core.py`**，不在 Skill 正文

任一不满足 → 继续 explore 或走路径 A。

---

## Runtime 硬约束（通用，与业务无关）

1. **单进程** `subprocess.run(..., shell=False)` 连续调 ziniao-cli
2. **Windows**：用 `locate_ziniao_cli_argv()` 直调 `ziniao-cli.exe`（或 `node run.js`），避免 `.cmd` 截断 URL 中的 `&`
3. **`page visit`**：`returncode==0` 即成功，成功信息在 stderr，stdout 可能为空
4. **长 JS 放 Python 文件**，禁止 PowerShell 多层转义
5. **exit 0 ≠ 业务成功** — 须有 `final_gate()`，失败 raise / 非 0
6. **explore** 只写 raw + 截图，不臆造业务字段
7. **stdout 用 UTF-8 bytes 写**，避免 Windows GBK 编码错误

`runtime_client.template.py` 已内置 2–3、7 的 Client 层处理，以及 **`poll_until()`**；scaffold 会复制到 `runtime/ziniao_client.py`。

---

## 原子 I/O 能力（与业务无关）

Runtime 等待、读取、导航的通用原语。业务 Kit 只组合这些原语，不在 template 里写域判定。

### 1. `poll_until(read, ready, timeout_ms, interval_ms)`

```python
from ziniao_client import poll_until

def fetch_section(client, jq_expr: str, min_len: int):
    client.page_visit(url, "load")

    def read():
        return client.page_content_jq(jq_expr) or ""

    def ready(text: str) -> bool:
        return len(text) >= min_len  # min_len / jq_expr 由 Kit validated-reads 定义

    return poll_until(read, ready, timeout_ms=6000, interval_ms=500)
```

- **用途**：SPA / 异步区块「就绪后再读」。
- **与盲 sleep 的区别**：条件满足即停；超时返回最后一次样本，不无限挂起。
- **超时不等于成功**：默认不 raise。调用方须再判 `ready`，或 `raise_on_timeout=True`，或交给 `final_gate`。
- **`--jq` 作用在 ZClaw 载荷上**，不是 CLI `{ok,data}` 信封。具体表达式写在 Kit `references/`，不要写进 skill-maker。

### 2. 导航 vs 读取职责

| 层 | 负责 | 禁止 |
|----|------|------|
| `page visit` | 导航 + `--wait-until` | — |
| `page exec` | 单次读态 / 单次交互 | 长 loop 替代 visit 的 load 等待 |
| `poll_until` | 异步就绪后的重复读 | 无上限、无 ready predicate |

### 3. 导航阶梯（direct-first）

```text
(1) visit 直达目标 URL → poll_until
(2) 未就绪 → visit 中间页 → 必要交互 → poll_until
(3) 仍未就绪 → 写入 raw + 声明 fallback 源 / final_gate 转人工
```

阶梯顺序与 fallback 声明写在 Kit `references/`，不写入 skill-maker。

### 4. 跨区段 fallback（模式，非域逻辑）

当区段 A 的主读法稳定失败，且同次 run 中区段 B 已采集到可编程等价信号：

- 允许 B → A 推断；
- 须在 `validated-reads.json` 声明 `method=fallback_from_<section>`；
- `final_gate` 校验该声明，禁止静默臆造。

### 5. 优化验证

改等待/读取策略后：

- 连跑 ≥3 次，看 `phaseDurationsMs` **中位数**；
- **CLI 次数**与**墙钟**分开报告；
- 禁止单次 run 宣称「优化 X%」。

---

## 反模式（实跑教训，仍保持通用表述）

| 反模式 | 后果 |
|--------|------|
| 无 SOP 首次 execute + 未验证的 regex | 静默错误数据 |
| 跳过 explore 直接写解析 | 大量时间耗在读法试错 |
| 无 final_gate 写 JSON | exit 0 假成功 |
| **已知 selector 不写进 Skill，每次重探** | 步骤不稳定、重复耗时 |
| **selector 失效后不更新 Skill** | 沿用失效定位，点错或空读 |
| PowerShell 内联复杂 JS | 转义地狱 |
| **`visit` 后固定 `time.sleep(N)`** | 就绪仍空等；未就绪仍不够 |
| **`page exec` 内长 loop 等 DOM** | 重复 visit 职责；墙钟膨胀 |
| **状态已就绪仍 poll / 重复 content** | CLI 预算浪费 |
| **把 poll 超时样本当成功** | 未就绪数据流入报告 |
| **单次 run 对比宣称优化** | 页面波动误判 |

---

## Agent 流程

**路径 A：** 读 store/page → 写自动化步骤到 `SKILL.md` → 按步骤执行并确认写入操作。

**路径 B：**

```text
doctor（一次）
→ read_input.py → manifest
→ preflight_validate.py（execute 且无 validated-reads → 拒绝）
→ run_*_core.py --manifest ...
→ explore：Agent 读 raw/，写 validated-reads.json
→ execute：final_gate 通过才算成功
```

---

## 关键原则

- **description 决定触发** — 写能力 +「当用户需要…时使用」，不写具体页面字段
- **CRITICAL 依赖** — 产出的 Skill 必须强制读取 ziniao-shared
- **Skill 编码规范与决策；Runtime 编码步骤**
- **先契约后执行** — preflight 不过不打开浏览器
- **安全** — 写入操作前确认用户意图

## 实跑教训写回哪里

写回**本次产出的 Skill / Kit**，不要改 `ziniao-skill-maker`。

| 路径 | 写什么 |
|------|--------|
| 路径 A `SKILL.md` | 步骤、已知 selector、失败时停在哪 |
| 路径 B `SKILL.md` + `references/` | 步骤意图、io-patterns、failure-retrospective |
| 路径 B `validated-reads.json` / `runtime/*_core.py` | 就绪条件、解析、final_gate |

selector 变了就更新这份 Skill；等待/读取策略变了就更新 Kit 的 `references` 和 Runtime。
