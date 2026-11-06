# 委托本技能的 PPT 渲染工作流 生成 PPT（步骤 3 生成环节）

本文件把 `cnki-edu-gen-ppt` 已确认的两级大纲与风格映射，**对接到本技能内置的 PPT 渲染工作流**（SlideDSL + `slidep` 工具链）完成 `.pptx` 渲染。本技能负责"需求/大纲/资料/配图规划"，渲染工作流负责"按设计稿逐页渲染"。

> 进入本步骤前：Gate 1（基础信息）与 Gate 2（大纲）必须已确认。因此跳过渲染工作流自身的"需求对齐/风格预览卡"重复环节（风格已在 Gate 1 锁定），直接进入 叙事 → 设计 → 创建 → 逐页生成。

## 一、渲染工作流必读文档

在步骤 3 开始时，**直接按下述文档执行渲染流程**（文档已随本技能打包，无需联网，也无需加载其他技能）：

- `references/create-from-scratch.md`：整体工作流（STORY/DESIGN/create/逐页）。
- `references/design-principle.md`：通用设计宪法（三区母版、色彩面积、字号阶梯、密度门禁、配图 L1/L2/L3、页面映射表）。
- 用到的组件规范：`component-slide.md`（画布/高度/安全区）、`component-image.md`（配图前置/ImageGen/SVG）、`component-box.md`、`component-text.md`、`component-table.md`、`component-svg.md`、`component-diagram.md`（时间轴/流程图）等。

## 二、project_dir 结构（每个 PPT 一个独立目录）

在用户 `workspace_dir` 下建项目目录（目录名 = pptx 文件名去 `.pptx` 后缀），例如 `光合作用/`：

```text
<workspace_dir>/
├── 光合作用/                      # project_dir
│   ├── DESIGN.md                 # 由本技能 types-and-styles 推导
│   ├── STORY.md                  # 由 Gate 2 大纲推导
│   ├── assets/                   # 所有 ImageGen 图 / 材料图（英文短名）
│   ├── slides/                   # 每页一个 .slide
│   │   ├── 01.slide              # 封面
│   │   ├── 02.slide              # 目录
│   │   ├── 03.slide ...          # 过渡/内容页
│   │   └── NN.slide              # 总结页（末页）
│   └── 光合作用.pptx             # 最终演示文稿
```

资源文件禁用中文/空格/特殊字符；图片一律落 `assets/` 后引用。

## 三、由本技能产物推导 STORY.md / DESIGN.md

### 3.1 STORY.md（来自 Gate 2 两级大纲）

把确认后的大纲直接转为叙事逻辑：一级标题 = 章节/模块，二级标题 = 页面，内容摘要 = 该页要点。固定末章"总结"。示例：

```markdown
# STORY · 光合作用（初中生物教学课件）
- 封面（hero）：标题/副标题/授课人
- 课标导入：情境激趣（图文右图）
- 知识讲解：概念界定（表格）/ 过程剖析（时间轴）/ 影响因素（数据大字）
- 例题活动：巩固练习（双栏）/ 探究建议（卡片）
- 总结（尾页）：核心结论与要点回顾
```

### 3.2 DESIGN.md（来自 types-and-styles 风格映射）

把 `types-and-styles.md` 的低饱和配色转成 `PPT 渲染工作流` 的**色彩池（≤4 hex）**、字号阶梯、母版三区（A/B/C）、**版式映射表**、**配图 L1/L2/L3 清单**。示例（清新绿）：

```markdown
# DESIGN · 清新绿（低饱和）
色彩池：bg #EDF5EE / 主色 #2F4A3A / 强调 #5E8C6A / 中性 #6F9C7B
字号：封面主标 64px / 章节大字 64px / 页标题 34px / 正文 24px / 锚点数字 80px / 页脚 14px
字体：标题 思源黑体 / 正文 思源黑体（教育亲和，避免默认无衬线单调）
母版三区：A 标题块 0–120 / B 内容区 120–660 / C 页脚条 660–720（NN/TOTAL）
版式映射：封面→全屏视觉+骑线文字；目录→左标题右图文；内容页按 STORY 建议版式轮换
配图清单：01_cover hero_plant.png(L1) / 03_concept scene_leaf.png(L2) / ... 全篇统一插画风
```

> 若命中 `PPT 渲染工作流` 预设领域（学术/咨询/红金），按其 `designs/design-principle.<id>.md` 执行；否则走通用 `design-principle.md`。本技能的低饱和偏好作为 override 优先。

## 四、逐页生成工作流（硬约束）

1. **`slidep create` 创建并立即预览（进入逐页前必须）**：
   ```bash
   slidep create "<project_dir>/光合作用.pptx"
   ```
   返回 `ok:true` 后**立即** `present_files` 打开该 .pptx（后续逐页即可实时看渲染）。
2. **逐页循环**（按 STORY 顺序从第 1 页到第 N 页）：
   - **配图前置（仅本页）**：先生成**本页**所需 ImageGen 图 → Read 核对（内容/比例/清晰/风格统一）→ 存 `assets/英文短名.png` → 再写该页。严禁一次生成全部图再写页。
   - 写页面源文件到 `slides/{NN}.slide`（最后表达式必须是 `<Slide>`，无 import/export）。
   - **写完立即校验（命令为 `slidep lint`）**：
     ```bash
     slidep lint "<pptx路径>" --dsl-file "slides/{NN}.slide"
     ```
     未通过则按返回的 `error` 字段修复 `.slide` 后重新校验，直到通过。**`slidep` 只有 `create` / `lint` / `upsert-dsl` 三个子命令，没有 `validate`；校验对象是 `.pptx` + `--dsl-file`，不要写成对 `.slide` 单文件或 `--project` 的调用。**
   - **校验通过后提交**：`slidep upsert-dsl "<pptx路径>" --dsl-file "slides/{NN}.slide"`（追加省略 `--page-index` 或 `-1`；替换用 `--page-index N`，0-based）。返回 `ok:true` 才继续下一页。
3. **校验要点（每页提交前）**：母版三区齐全（A 标题/B 内容/C 页脚 NN/TOTAL）；画布 720px 不溢出；每页 ≥1 视觉锚点；版式不与上页重复；只用 DESIGN 列出的 ≤4 hex 与 ≤2 字体；配图风格全篇统一。
4. **缺图降级**：ImageGen 重试 2 次仍不合格 → SVG 兜底并记原因；实在无图 → 该页退化为纯文字版式，**绝不中断**生成。

## 五、五类页面 → SlideDSL 映射（cheat sheet）

> 通用容器：`<Slide style={{padding:'20px 70px'}}>` + A 区 `<Box>` 标题(34px bold) + B 区内容 + C 区页脚(`NN / TOTAL`, 14px 灰)。写每页前先读对应 `component-*.md`。

| 页面 | 版式要点 | 关键组件 |
|---|---|---|
| **封面** | 全屏 L1 主视觉(≥B区40%) + 骑线大标题(60–96px) + 副标/落款 | `<Image>`(L1) + `<Text>` |
| **目录** | 左标题"目录" + 右 N 个并列条目（每项 ≥30 字） | `<Text>` 列表 / `<Box>` 卡片 |
| **过渡页** | 章节大字(60–80px) + 一句小标 + 1 张 L1 | `<Text>` + `<Image>`(L1) |
| **内容页·图文** | 左文右图(image_right) 或 左图右文(image_left)，图 L1/L2 | `<Box>`(flex) + `<Text>` + `<Image>` |
| **内容页·双栏** | 两栏等宽，中间细分隔线 | `<Box display:flex>` 两子 `<Box>` |
| **内容页·卡片** | 2–4 张等高圆角卡，卡内标题+正文(≥100字/卡) | `<Box borderRadius>` 卡片组 |
| **内容页·时间轴** | 纵向时间轴节点(可用 `<SVG>` 画轴+节点) | `<SVG>` + `<Text>` |
| **内容页·对比** | 左右两卡(A/B) 并列对比 | 两个 `<Box>` 卡 |
| **内容页·数据大字** | ≥1 个 72–120px 锚点数字 + 洞察文字 | `<Text>`(大数字) + `<Text>` |
| **内容页·表格** | 标题 + 表格（表头强调色） | `<Table>` |
| **内容页·引言** | 居中大字引文 + 作者，留白围绕焦点 | `<Text>`(italic,居中) |
| **总结页（尾页）** | 收束金句/3 条核心结论回顾，可配 0–1 图 | `<Text>` 列表 |

## 六、SlideDSL 片段示例（图文右图页）

```jsx
<Slide style={{ padding: '20px 70px', background: '#EDF5EE' }}>
  <Box style={{ height: 120 }}>
    <Text style={{ fontSize: 34, fontWeight: 'bold', color: '#2F4A3A' }}>过程剖析</Text>
  </Box>
  <Box style={{ display: 'flex', height: 520, gap: 30 }}>
    <Box style={{ flex: 1 }}>
      <Text style={{ fontSize: 24, color: '#2F4A3A', lineHeight: 1.5 }}>
        • 光反应：类囊体上进行，产生 ATP 与 NADPH{'\n'}
        • 暗反应：基质中进行，固定 CO₂ 合成糖类
      </Text>
    </Box>
    <Box style={{ flex: 1 }}>
      <Image src="assets/scene_chloroplast.png" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: 12 }} />
    </Box>
  </Box>
  <Box style={{ position: 'absolute', bottom: 20, right: 70 }}>
    <Text style={{ fontSize: 14, color: '#6F9C7B' }}>05 / 12</Text>
  </Box>
</Slide>
```

## 七、注意事项

- 图片 `src` 必为 `assets/` 本地相对路径；严禁 `http(s)://`、在线 URL、`image://` 占位符。
- 正文页不用全屏背景图；大图以独立组件出现（占 50% 宽/高），四周保留默认背景。
- 全篇配图同一视觉类型（插画/3D/摄影），生图 prompt 复用同一组风格词，禁止混用。
- 知网推荐**不写入 STORY/DESIGN/不进入 PPT**，于最终交付时**紧接 PPT 卡片下方**以「知网推荐」列表呈现：每条**仅展示文献名、作者、来源三项**，**严禁在可见文案中暴露任何元数据**（发表时间、卷期、doi、数据库名、内部 id、链接地址明文等），**仅文献名可点击**且**带跳转链接**、点击**一次直达该篇在知网研学平台的研读页面**（**直接取用检索接口返回的 `url` 字段，原样使用**），**不附带悬停提示、条目文本中不出现地址明文**（见 `cnki-guide.md`）。
- **生成过程与思考过程展示**：步骤 3 执行期间须按 `SKILL.md` 规则 13 **实时展示「生成过程（阶段进度）」与「思考过程（决策随想）」**——阶段进度告知"做到哪了"（解析需求→检索资料→生成配图→渲染PPT→生成知网推荐），思考随想以轻松口吻流露关键设计/内容决策（如版式取舍、章节合并逻辑、检索亮点），均为用户视角、不暴露工具名与内部细节。
- 生成完成后 `present_files` 打开预览；编辑交由平台本地 Office 编辑能力。
