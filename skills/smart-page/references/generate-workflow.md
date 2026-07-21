# 生成模式 · 模板化生成完整工作流

> SKILL.md「生成模式」一节的详细展开。SKILL.md 只保留模式分流和触发条件，具体步骤以本文件为准。

---

## 触发条件

用户意图明确命中以下 4 类场景之一：

| scene      | 名字                | 典型                                                |
| ---------- | ------------------- | --------------------------------------------------- |
| `proposal` | 向上汇报 / 立项     | 立项、方案评审、ROI、季度述职、战略规划             |
| `sync`     | 周期同步 / 数据复盘 | 周报、双周报、月报、OKR、KPI、归因、A/B             |
| `insight`  | 数据洞察            | KPI 大盘、为什么下跌、爆发归因、A/B 实验            |
| `share`    | 知识传播 / 技术分享 | 技术长文、培训课件、FAQ、公开课、产品理念、杂志长文 |

> ⚠️ 其他场景（邀请函、官网、Landing、简历、画册、H5、PRD、会议纪要等）**不进这条链路**，由通用 agent 处理。

> ⚠️ **关键原则**：agent 根据关键词自行 best-guess 一个 scene（不确定就选最接近的），**立刻起 `serve.py start`**，场景确认/修正由用户在右侧面板完成。**绝不使用 AskUserQuestion 或对话追问来确认场景**。

---

## 四区理念（贯穿生成模式所有模板）

| 区           | 作用              | 典型元素                                         |
| ------------ | ----------------- | ------------------------------------------------ |
| **Overview** | 一屏答完问题      | 一句话结论 / KPI 卡 / 当前假设摘要 / Hero 氛围层 |
| **Controls** | 支持"如果…会怎样" | 滑块、开关、下拉、输入框、场景选择               |
| **Charts**   | 随参数实时响应    | 趋势图 / 结构图 / 敏感性图（Chart.js 动态）      |
| **Logic**    | 让人读懂逻辑      | 假设说明 / 计算口径 / 结论推演 / 风险与边界      |

**必须具备的动效**：滚动揭示、数字 CountUp、Hero 氛围层、Sticky 章节编号、进度条、`prefers-reduced-motion` 降级。

**禁止**：

- 纯静态 + "下一页"按钮（那是 PPT）
- 只放图不放可交互控件（失去可推演性）
- 重要结论藏在折叠里（必须首屏给结论）

---

## 三层正交架构

```
场景（scene · 4）× 叙事范式（narrative · 3/场景，共 12）× 设计皮肤（skin · 12）
```

详见 `architecture.md`。

---

## 工作流总览（agent 逐步推进 stage）

```
用户输入 → 阶段 1 场景初筛 → 阶段 2 问卷路由 → 阶段 3 模板选择
                                                       ↓
                                      阶段 4 骨架 loading
                                                       ↓
                                      阶段 5 生成数据 + inject
                                                       ↓
                                      阶段 6 自检 → 阶段 7 发布腾讯文档
```

**关键设计**：前端页面轮询 `/stage` 来检测变化并 reload，但 **stage 推进需要 agent 调用 `serve.py advance`**。完整步骤：

1. 起 `serve.py start --probe-scene <scene> --probe-reason "<理由>"`
2. **立即**发起 `preview_url` 工具调用打开右侧面板
3. 等 `scene_confirm.json` → `advance --to intent_questionnaire`
4. 等 `answers.json` → `advance --to template_choice`
5. 等 `choice.json`（用户选模板后直接生成）
6. 生成骨架 JSON → `advance --to skeleton_loading --skeleton-file`
7. 读 narrative.md → 生成 data.js → `inject.py` 输出单文件 HTML
8. 自检
9. `publish.sh` 发布 → 发起 `preview_url` 工具调用打开腾讯文档 page 链接

---

## 阶段详解

### 阶段 1 · 场景初筛

**agent 行为**：根据用户输入的关键词自行判断最匹配的 scene，一句话告诉用户"好的，我来帮你做这份 XX"，然后**立刻执行**：

```bash
python3 "$SKILL_DIR/scripts/serve.py" start \
  --theme "<从用户输入提取的主题>" \
  --probe-scene "<proposal|sync|insight|share>" \
  --probe-reason "<≤30 字，为什么选这个 scene>"
```

> 🚫 **禁止**：在起脚本之前用 AskUserQuestion / 对话追问 来确认 scene。用户在右侧面板里可以看到 agent 的 best-guess 并修正。

解析 stdout，具体如下：

**`serve.py start` stdout 协议**（JSON 格式）：

```json
{
  "ok": true,
  "stage": "scene_probe",
  "url": "http://127.0.0.1:17501",
  "workdir": "/tmp/tencent-smart-page-xxx",
  "pid": 12345,
  "theme": "..."
}
```

agent 解析：

- `workdir` → 赋给 `$WD`（后续轮询和 advance 都用这个路径）
- `url` → **立即**发起 `preview_url` 工具调用打开右侧面板（用户需要在面板中确认场景，否则 `scene_confirm.json` 不会生成）

发起 `preview_url` 打开面板后，轮询等待 `$WD/scene_confirm.json`（间隔 2s，超时 180s）。

### 阶段 2-3 · 问卷 + 模板选择（agent 需手动推进 stage）

用户在右侧面板确认场景后，`scene_confirm.json` 出现。agent 需要**依次推进 stage**：

**步骤 1**：检测到 `scene_confirm.json` → 推进到问卷：

```bash
python3 "$SKILL_DIR/scripts/serve.py" advance "$WD" --to intent_questionnaire
```

**步骤 2**：轮询等待 `answers.json`（用户填完问卷后生成，间隔 2s，超时 300s）。

**步骤 3**：检测到 `answers.json` → 推进到模板选择（内部自动调 match.py 打分）：

```bash
python3 "$SKILL_DIR/scripts/serve.py" advance "$WD" --to template_choice
```

**步骤 4**：轮询等待 `choice.json`（用户选模板后由 server 直接写入，间隔 2s，超时 300s）。

`choice.json` 结构：

```json
{
  "scene": "proposal",
  "narrative": "pyramid",
  "narrative_name": "金字塔原理",
  "skin": "tencent-blue",
  "skin_label": "蔚蓝 · 腾讯官方"
}
```

> **腾讯系官方皮肤锁定**：若 `tone=tencent` 或 `skin_pref=tencent`，3 张模板卡的 skin **全部**为 `tencent-blue`，不给第二套皮肤选项。

> **「AI 帮我选」位置**：只出现在模板选择页的 3 张卡下方作为第 4 个兜底入口。点击 = 自动选 DATA[0] + 推荐皮肤，走同一个 `submitChoice` 路径。

### 阶段 4 · 骨架 loading

生成骨架 JSON 保存到 `/tmp/skeleton.json`：

```json
{
  "narrative_name": "金字塔原理",
  "skin_label": "蔚蓝 · 腾讯官方",
  "sections": [
    {
      "title": "抽结论 · S1",
      "role": "Overview",
      "status": "done",
      "bullets": ["..."]
    }
  ]
}
```

切到骨架页：

```bash
python3 "$SKILL_DIR/scripts/serve.py" advance "$WD" --to skeleton_loading \
  --skeleton-file /tmp/skeleton.json
```

### 阶段 5 · 生成数据 + 注入

**必须读两个文件**：

| 文件           | 用途                                               | 读取方式                             |
| -------------- | -------------------------------------------------- | ------------------------------------ |
| `narrative.md` | 数据契约 class 定义（结构骨架）                    | `template_source.py fetch` 或 `curl` |
| `mock-data.js` | **黄金标准示例**（值类型、嵌套结构、compute 写法） | 同上                                 |

```bash
# 读 narrative.md（数据契约）
python3 "$SKILL_DIR/scripts/template_source.py" fetch "scenes/${scene}/${narrative}/narrative.md"

# 读 mock-data.js（黄金标准示例）—— ⚠️ 必读！
python3 "$SKILL_DIR/scripts/template_source.py" fetch "scenes/${scene}/${narrative}/mock-data.js"
```

> ⚠️ **`mock-data.js` 是生成 data.js 的唯一可靠参照**。narrative.md 的 class 定义是简写形式，
> 许多细节（如 `compute` 是一段可执行 JS 字符串、`inputs[].key` 必须与 compute 变量名一致、
> `pros`/`cons` 是字符串数组而非对象数组）**只有看 mock-data.js 才能确认**。

**生成 data.js 的强制步骤**：

1. **先读 mock-data.js**，逐字段确认每个 key 的值类型和嵌套结构
2. 按 narrative.md 的 class 定义确认字段名/约束
3. 生成 `window.data = {...};` 时**严格对齐 mock 结构**：
   - 对象的每个 key 必须存在（不可遗漏）
   - 数组的元素结构必须与 mock 首个元素一致
   - `compute` 字段必须是**含 return 语句的 JS 表达式字符串**（不是函数对象）
   - 数字类型不能写成字符串（`value: 5000` 不是 `value: "5000"`）
   - 数组不能为空（mock 有 3 个就至少给 2 个）
4. `data.js` 推荐使用 `window.data = {...};`；`const data = {...};` / `let data = {...};` / `var data = {...};` 也可被 `validate_data.py` 校验，但注入前会统一转为 `window.data`
5. **只用英文半角引号**，禁止中文引号
6. **必须体现四区**：Overview / Controls / Charts / Logic 各有对应字段

**生成后立即验证**（注入前）：

```bash
python3 "$SKILL_DIR/scripts/validate_data.py" \
  --scene "${scene}" --narrative "${narrative}" --data /tmp/data.js
```

- 退出码 0 = 通过，继续注入
- 退出码 1 = 有错误，**必须根据输出修复 data.js 后重新验证**（最多重试 2 次）
- 退出码 2 = JS 语法错误，data.js 无法被 node 解析

> ⚠️ **验证不通过禁止注入**。修复后必须重新跑 `validate_data.py` 直到通过。

**注入**：

```bash
python3 "$SKILL_DIR/scripts/inject.py" \
  --scene "<scene>" --narrative "<narrative>" --skin "<skin>" \
  --data /tmp/data.js \
  --output "output/${THEME_NAME}.html"
```

输出单文件 HTML（40–60KB）。`<head>` 的 `<title>` 决定腾讯文档 page 标题，必须写正确的 `${THEME_NAME}`。

### 阶段 6 · 自检（脚本 + 人工确认）

**自动检查**（已由 validate_data.py 在阶段 5 完成）：

1. ✅ `window.data` 字段与 mock-data.js 结构完全一致（字段名 + 类型 + 嵌套）
2. ✅ 必填字段无遗漏
3. ✅ 数组长度在合理范围
4. ✅ 无中文引号
5. ✅ JS 可被 node 正常解析

**人工确认**（agent 自行核对）：

6. 文案能体现四区（Overview / Controls / Charts / Logic）
7. 无主观夸张词
8. `inject.py` stdout 有 `OK scene=...`
9. 打开 HTML 能看到：首屏结论 / 滚动揭示 / 数字累加 / 皮肤色值正确

### 阶段 7 · 发布腾讯文档（强制必做）

**最严格规则**：

- HTML 生成完成 ≠ 任务完成
- **拿到 `file_url` 并通过 `preview_url` 工具调用打开 = 任务完成**
- 绝不允许只给本地 HTML 路径就收工
- 整条链路必须在同一次回复里全部跑完

走 SKILL.md「发布到腾讯文档」章节，传 `--html "output/${THEME_NAME}.html" --title "${THEME_NAME}"`。
