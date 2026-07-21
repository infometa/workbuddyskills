# 架构 · 四区理念 + 三层正交

> 生成模式所有页面都遵循的"信息架构（四区）+ 资源拼装（三层）"双重契约。

---

## 四区理念（每页都必须具备）

| 区           | 作用              | 典型元素                                         |
| ------------ | ----------------- | ------------------------------------------------ |
| **Overview** | 一屏答完问题      | 一句话结论 / KPI 卡 / 当前假设摘要 / Hero 氛围层 |
| **Controls** | 支持"如果…会怎样" | 滑块、开关、下拉、输入框、场景选择               |
| **Charts**   | 随参数实时响应    | 趋势图 / 结构图 / 敏感性图（Chart.js 动态）      |
| **Logic**    | 让人读懂逻辑      | 假设说明 / 计算口径 / 结论推演 / 风险与边界      |

**必备动效**：滚动揭示、数字 CountUp、Hero 氛围层、Sticky 章节编号、进度条、`prefers-reduced-motion` 降级。

**禁止**：

- 纯静态 + "下一页"按钮（那是 PPT）
- 只放图不放可交互控件（失去可推演性）
- 重要结论藏在折叠里（首屏必须给结论）

---

## 三层正交架构

```
场景（scene · 4）× 叙事范式（narrative · 12）× 设计皮肤（skin · 12）
```

三层互不耦合：换皮肤不动 section 顺序，换叙事不动色值。

---

### L1 · 场景（4 个）

| scene      | 名字                | 典型                       |
| ---------- | ------------------- | -------------------------- |
| `proposal` | 向上汇报 / 立项     | 立项、方案、ROI、资源申请  |
| `sync`     | 周期同步 / 双周报   | 周报、月报、OKR、进度      |
| `insight`  | 数据洞察 / 产品分析 | KPI、归因、A/B、dashboard  |
| `share`    | 知识传播 / 技术分享 | 技术分享、长文、培训、杂志 |

### L2 · 叙事范式（每场景 3 套，共 12 套）

| 场景       | 叙事 1                     | 叙事 2               | 叙事 3              |
| ---------- | -------------------------- | -------------------- | ------------------- |
| `proposal` | `pyramid` 金字塔           | `scqa` SCQA 冲突     | `blm` BLM 战略      |
| `sync`     | `prep` PREP 回环           | `star` STAR 复盘     | `okr` OKR 对齐      |
| `insight`  | `pyramid-data` 金字塔·数据 | `attribution` 归因树 | `contrast` 对比叙事 |
| `share`    | `story-arc` 故事曲线       | `qa-driven` 问题驱动 | `magazine` 杂志深读 |

每个叙事的 section 骨架与数据契约见 `scenes/{scene}/{narrative}/narrative.md`（COS 远端，`template_source.py fetch` 拉取）。

### L3 · 设计皮肤（12 套，35 变量合同）

| skin               | 气质                | 色锚              | 用途                  |
| ------------------ | ------------------- | ----------------- | --------------------- |
| `stillwater`       | 沉静 · 精准克制     | #5E6AD2           | proposal / sync 默认  |
| `monolith`         | 建筑 · 严谨机构     | #0A0A0A           | 委员会、合规          |
| `letterpad`        | 手札 · 温暖编辑     | #A0562C           | share 默认            |
| `hearth`           | 炉火 · 叙事         | #CC785C           | story-arc / qa-driven |
| `prism`            | 流光 · 优雅传播     | #635BFF           | 对外传播              |
| `pulse`            | 脉冲 · 数据仪表盘   | #F54E00           | insight 默认          |
| `tencent-blue`     | **蔚蓝 · 腾讯官方** | #0052D9 / #FBAE40 | **司内汇报首选**      |
| `ink-press`        | 墨刊                | #0a0a0b           | share · magazine      |
| `indigo-porcelain` | 靛瓷                | #0a1f3d           | share · magazine      |
| `forest-press`     | 林墨                | #1a2e1f           | share · magazine      |
| `kraft-press`      | 牛皮                | #2a1e13           | share · magazine      |
| `dune-press`       | 沙丘                | #1f1a14           | share · magazine      |

**皮肤推荐规则**：

- **腾讯系三套**（用户选"腾讯官方"时）：`tencent-blue` · `stillwater` · `prism`
- **杂志深刊五套**（narrative=`magazine` 时强制）：`ink-press` / `indigo-porcelain` / `forest-press` / `kraft-press` / `dune-press`
- **司内汇报首选**：`tencent-blue`

---

## 模板资源全量列表（动态查询）

每个 `scene × narrative` 支持的皮肤集合、默认皮肤、特色描述等数据**以 COS `_index.json` 为唯一真源**，不在本文档硬编码（避免文档滞后）。

```bash
# 查全量
python3 "$SKILL_DIR/scripts/template_source.py" index

# 查单个资源 URL
python3 "$SKILL_DIR/scripts/template_source.py" url scenes/proposal/pyramid/template.html
```

---

## 数据契约（agent 生成 data.js 前必读）

agent 生成 `data.js` 时**必须同时读取两个文件**：

```
scenes/{scene}/{narrative}/narrative.md
scenes/{scene}/{narrative}/mock-data.js
```

`narrative.md` 含 Role · 叙事骨架 · 输入前置检查 · CoT 推理链 · 数据契约 · 视觉契约 · 约束；`mock-data.js` 是值类型、嵌套结构、数组元素形态和 `compute` 写法的黄金示例。

**禁止读 `template.html`**（27–36KB，浪费 token），由 `inject.py` 处理。
