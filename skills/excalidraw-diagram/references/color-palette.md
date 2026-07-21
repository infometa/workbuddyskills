# Excalidraw Diagram Color Palette

默认采用白底、轻量、可读性优先的配色。

## Base

- Background: `#FFFFFF`
- Border / Main stroke: `#1F2937`
- Secondary stroke: `#475467`
- Divider / light border: `#D0D5DD`
- Primary text: `#111827`
- Secondary text: `#475467`
- Tertiary text: `#667085`

## Semantic fills

| Purpose | Fill | Stroke | Notes |
|---|---|---|---|
| Neutral / default | `#F8FAFC` | `#334155` | 普通节点 |
| Start / input | `#ECFDF3` | `#027A48` | 起点、输入、触发 |
| End / output | `#EFF8FF` | `#175CD3` | 输出、结果 |
| Decision | `#FFF7ED` | `#C4320A` | 决策、条件分支 |
| Warning / risk | `#FEF3F2` | `#D92D20` | 风险、错误、异常 |
| AI / reasoning | `#F5F3FF` | `#7A5AF8` | Agent、模型、推理模块 |
| External system | `#F4F3FF` | `#6941C6` | 第三方系统、外部依赖 |
| Data / storage | `#F0F9FF` | `#026AA2` | 数据、缓存、存储 |

## Evidence artifacts

用于代码块、JSON、事件流等“证据片段”。

- Evidence background: `#101828`
- Evidence border: `#344054`
- Evidence title: `#F8FAFC`
- Code keyword: `#7DD3FC`
- Code string: `#86EFAC`
- Code value / highlight: `#F9A8D4`
- Code comment / hint: `#98A2B3`

## Usage rules

1. 同一语义尽量复用同一组 fill + stroke。
2. 如果拿不准，用 Neutral，不要临时发明颜色。
3. 文字层级靠字号、粗细、颜色深浅区分，不靠透明度。
4. 代码或 JSON 证据块统一使用深色底，避免与主画布混色。
