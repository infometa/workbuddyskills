---
name: excalidraw-diagram
description: "Create Excalidraw diagrams for workflows, architectures, protocols, concepts, and system explanations. Use when a user wants a flowchart, architecture sketch, visual explanation, or diagram as a .excalidraw file plus PNG preview. Includes a local Playwright renderer for visual QA and reference files for palette, JSON structure, and reusable element patterns."
description_zh: "Excalidraw 图解生成与渲染校验"
description_en: "Generate Excalidraw diagrams with local rendering validation"
homepage: https://github.com/coleam00/excalidraw-diagram-skill
allowed-tools: Read,Write,Bash
display_name: "excalidraw-diagram"
display_name_en: "excalidraw-diagram"
visibility: "public"
icon: "https://codebuddy-platform-1258344699.cos.accelerate.myqcloud.com/public/45edac6b-2078-4678-89f3-6f9800cf5e5f/avatar/skill/au_d7ebe354-e87.png"
---

# Excalidraw Diagram

用 Excalidraw 生成能够“解释问题”的图，而不是把文字机械摆成卡片。

## 适用场景

当用户要你生成以下内容时使用本 skill：

- 流程图、架构图、协议图、系统关系图
- 把复杂概念可视化
- 需要 `.excalidraw` 源文件，后续还要继续编辑
- 需要先导出 PNG 预览，再迭代布局与视觉层次

## 输出要求

默认产出两份文件：

1. `*.excalidraw`：可继续编辑的源文件
2. `*.png`：本地渲染预览图

**不要只交付 JSON。** 生成后必须本地渲染一次，并根据预览修正明显问题。

## 首次阅读顺序

开始画图前按需读取：

| 任务 | 先读什么 |
|---|---|
| 所有任务 | `references/color-palette.md` |
| 需要写元素 JSON | `references/element-templates.md` |
| 不确定 Excalidraw 文件结构 | `references/json-schema.md` |
| 准备渲染和排查布局 | `references/rendering-workflow.md` |

## 核心方法

### 1. 先判断深度

先决定这张图属于哪一类：

- **概念图**：强调关系、层次、因果，不必塞太多技术细节
- **技术图**：要展示真实事件名、接口名、请求结构、代码片段、输入输出样例

如果是技术图，先查真实资料，再开画。不要用“Service A → Service B”这种空标签糊弄过去。

### 2. 结构先行，不要先写样式

先确定这张图真正想表达什么：

- 是顺序？用时间线或分阶段布局
- 是聚合？用汇聚结构
- 是分发？用扇出结构
- 是对比？用左右并列
- 是层级？用树形或分区

**形状必须服务含义。** 不要默认所有节点都是同尺寸卡片。

### 3. 默认少容器、多层级文字

不是每段文字都需要矩形包住。默认优先：

- 标题、注释、说明：直接用文字
- 只有需要承载语义或承接箭头时，才加形状
- 同一张图里，尽量让容器节点少于总文本节点的三分之一

### 4. 技术图必须给“证据”

技术图至少加入一种真实证据：

- 真实事件名
- JSON payload 样例
- API / method 名称
- 关键代码片段
- 真实输入输出格式

这样图本身就能用于教学，而不是只做装饰。

## 推荐工作流

### Step 1：定义视觉论点

先用一句话写清楚这张图想证明什么。

示例：
- “事件流是从 AI agent 单向推送到前端，而不是轮询”
- “系统的复杂度主要集中在中间编排层”
- “用户看到的是单入口，但底层是多阶段处理”

### Step 2：列出区块

先把图拆成 3-6 个区块，再决定每块内部怎么画。大图一定要分区写，别一次性生成全部元素。

常见分区方式：
- 按阶段：输入 / 处理 / 输出
- 按角色：用户 / 客户端 / 服务端 / 外部系统
- 按层级：界面层 / 编排层 / 数据层

### Step 3：选择视觉模式

按概念选择模式：

| 概念 | 建议模式 |
|---|---|
| 顺序流程 | 时间线 / 横向流程 |
| 一对多分发 | 扇出 |
| 多对一聚合 | 汇聚 |
| 层级结构 | 树形 / 分区 |
| 对比分析 | 左右并列 |
| 循环反馈 | 回环箭头 |

### Step 4：生成 `.excalidraw`

写文件时遵守三条：

1. 使用可读的字符串 ID
2. 大图按区块逐段补元素
3. 坐标和尺寸以可读性优先，不追求“程序算出来”

### Step 5：本地渲染并回看

生成 JSON 后，必须执行本地渲染：

```bash
uv sync --project {baseDir}/scripts
uv run --project {baseDir}/scripts playwright install chromium
uv run --project {baseDir}/scripts python {baseDir}/scripts/render_excalidraw.py /absolute/path/to/diagram.excalidraw --output /absolute/path/to/diagram.png
```

然后读取 PNG，检查：

- 文字有没有被裁切
- 箭头是否落在正确对象上
- 重要节点是否足够醒目
- 区块之间是否太挤或太散
- 是否出现大片无意义空白

### Step 6：修正后再交付

如果预览里出现以下任何问题，先修再交：

- 文本溢出或重叠
- 箭头穿过不该穿过的内容
- 节点尺寸失衡
- 色彩层次混乱
- 技术图没有真实证据片段

## 视觉默认值

- 背景：纯白 `#FFFFFF`
- 线条：干净、克制，默认 `roughness: 0`
- 强调方式：用尺寸、间距、颜色层级，不用透明度堆效果
- 配色：全部从 `references/color-palette.md` 取，不临时发明新颜色

## 安装与依赖

渲染链路依赖 `uv` 和 Playwright。

### 推荐安装

```bash
brew install uv
uv sync --project {baseDir}/scripts
uv run --project {baseDir}/scripts playwright install chromium
```

### 依赖说明

- `uv`：管理 Python 运行环境
- `playwright`：驱动无头 Chromium 把 `.excalidraw` 渲染成 PNG
- 浏览器资源首次安装较慢，属于正常现象

## 交付格式建议

给用户交付时，尽量同时说明：

- 这张图的核心论点
- 你采用的结构（例如分区、时间线、扇出）
- 如为技术图，指出证据片段在哪一块
- 提供 `.excalidraw` 与 `.png` 路径

## 常见误区

### 误区 1：所有节点都画成一样的卡片
这样会让图只剩“排版”，没有论证。

### 误区 2：技术图只写概念，不给实物
如果没有真实事件、接口、数据格式，教学价值会很弱。

### 误区 3：只看 JSON 不看渲染结果
坐标在 JSON 里看着没问题，不代表视觉上真的成立。

### 误区 4：把颜色当装饰
颜色应该承担语义分层，而不是随机好看。

## 最终检查清单

交付前确认：

- [ ] 已生成 `.excalidraw`
- [ ] 已渲染 PNG 预览
- [ ] 没有明显裁切、重叠、错连
- [ ] 结构和论点一致
- [ ] 技术图包含真实证据片段
- [ ] 使用了统一配色与文字层级
