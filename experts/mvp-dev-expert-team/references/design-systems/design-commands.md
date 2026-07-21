---
id: design-commands
title: 设计动作命令库（23 个商业级设计动作 + 寄存器 + 平台轴）
domain: design-systems
quality_score: 95
last_updated: 2026-07-19
---

# 设计动作命令库

把"设计"拆成 23 个可调用动作，而不是一个含糊的"做设计"。每条命令有明确入口、明确出口、明确检查项；寄存器与平台是两条正交判断轴，决定动作的标杆与边界；a11y 单独走审计通道，不在设计期触发，避免模型过度谨慎产出保守方案。

## 1. 设计寄存器判断（Brand vs Product — 设计前必判）

收到需求的第一步不是选字体，是判寄存器。寄存器错了，后续所有标杆都错。

### Brand 寄存器：设计 IS 产品

交付物本身就是产品：营销页、落地页、品牌站、作品集、长篇内容、活动页。访客的"印象"就是被生产的东西。

- 标杆是**独特性**。判据：把作品截图发给一个设计师朋友，他若脱口而出"这是 AI 做的"，就失败了。
- 跨越多条美学通道：科技极简、奢侈、编辑杂志、消费温度、brutalist。不要默认只走一条。
- 调色板可以是 Committed / Full palette / Drenched，调色板即口音。
- 字体往往 2 族以上，fluid `clamp()` 阶梯，步进比 ≥1.25。
- 当 brief 暗示图像时（餐厅、酒店、杂志、摄影），缺图是 bug，不是克制。
- 入场动效允许一处精心编排，反对每节都 fade-on-scroll。

### Product 寄存器：设计服务产品

交付物服务于产品：app UI、后台、仪表板、设置面板、数据表、工具。

- 标杆是**赢得熟悉感**。判据：Linear / Figma / Notion / Raycast / Stripe 的熟手用户坐下来是否信任这个界面，还是在每个略奇怪的组件上停顿。
- 失败模式不是平淡，而是无目的的奇怪：装饰过度的按钮、不匹配的表单控件、无功能的动效。
- 调色板默认 Restrained，强调色只用于主操作、当前选中、状态指示。
- 字体一族往往够用，固定 `rem` 阶梯，步进比 1.125–1.2。
- 每个交互组件必须全状态：default / hover / focus / active / disabled / loading / error / success。
- 动效 150–250 ms，传递状态而非装饰，无页面加载编排。

### 寄存器差异表

下列动作在两个寄存器间有分歧，命令执行时需要切换标杆：

| 动作 | Brand 寄存器 | Product 寄存器 |
|---|---|---|
| typeset | 多族、fluid clamp、≥1.25 比 | 一族、固定 rem、1.125–1.2 比 |
| colorize | Committed / Full / Drenched 都允许 | 默认 Restrained，语义优先 |
| layout | 不对称、fluid、可破网格 | 可预测网格、结构化响应式 |
| animate | 一次精心编排的入场 | 状态切换 150–250 ms，无开场 |
| bolder | POV 更强、比例更狠 | 层级更清、密度更狠（不是戏剧） |
| quieter | 调色板更克制、留白更多 | 装饰更少、卡片更平、动效更短 |
| delight | 分布在文案/转场/发现奖励 | 集中在完成/首次/错误恢复等节点 |

### 判断流程

1. 看路径形态：`/about` `/pricing` `/blog/*` 落页形 → brand；`/app/*` `/dashboard` `/settings` 表单表格 → product。
2. 看 PRODUCT.md 的 `## Register` 字段（裸值 `brand` 或 `product`）。
3. 信号真分裂时（产品里有个大营销落地页），问用户哪个是**主要**表面，写入默认。
4. 单一任务可临时覆盖寄存器，但项目级默认必须先定。

## 2. 平台正交轴（Web / iOS / Android / Adaptive）

寄存器回答"设计是产品还是服务产品"，平台回答"交付目标是什么、哪套原生规范适用"。两者正交。

| 平台 | 规则书 | 何时加载 |
|---|---|---|
| **web** | 无额外规则书，通用规则 + 寄存器参考覆盖 | 默认 |
| **ios** | Apple HIG 精要 | 原生 iOS / iPadOS app |
| **android** | Material Design 3 精要 | 原生 Android app |
| **adaptive** | 同时加载 iOS + Android | 一套代码出两端，按 OS 自适应 |

### iOS 精要（HIG 浓缩）

- 安全区内布局，避开 notch / Dynamic Island / home indicator。
- 系统导航：2–5 个顶级 section 用 tab bar，层级用导航栈，自包含任务用 sheet。
- 左边缘回滑手势是肌肉记忆，永不 disable 或覆盖。
- 大标题在顶层屏，滚动时塌缩为内联。
- 触控目标 44×44 pt 起。
- Dynamic Type 系统文字样式，不硬编码 point size；SF Pro 承载 UI。
- 语义系统色（label / secondaryLabel / systemBackground / separator / tint），自动适配深色模式与增强对比度。
- 平台控件优先（Switch / Segmented / Stepper / 系统选择器 / Action Sheet / Alert / Context Menu / Swipe Action），SF Symbols 图标。
- 系统转场（push 滑入 / sheet 升起 / dismiss 反转），尊重 Reduce Motion。

### Android 精要（Material 3 浓缩）

- Material 导航按宽度适配：compact 用底部 navigation bar，expanded 用 rail 或 drawer。手机底部条原样塞到平板上是错的。
- 系统返回手势 / 返回键永远工作，预测性返回要 honor。
- edge-to-edge + window insets 处理状态栏 / 导航栏 / cutout / IME。
- 触控目标 48×48 dp 起，间隔至少 8 dp。
- Material 字体阶梯（Display / Headline / Title / Body / Label 各 large/medium/small），映射到角色，不按屏幕手挑 size。
- Roboto 系统字体，sp 单位不写 px。
- Material 色彩角色（primary / on-primary / surface / surface-variant / secondary-container / outline / error），自动解析 light/dark/contrast。
- Dynamic Color（Material You）从壁纸取色，Android 12+ 启用，配静态 fallback。
- Material 组件（filled / tonal / outlined / text 按钮、FAB、switch、chip、snackbar、bottom sheet、Material dialog），一个 FAB 一个主操作。
- 容器变换 / 共享轴 / fade-through，标准 easing 与时长；honor 系统 Remove animations。

### Adaptive 判据

按**渲染的设计语言**判，不是按工具链判。Flutter 默认 Material-everywhere 一套视觉打两端，算 `android`（同视觉）；真正 Cupertino on iOS + Material on Android 的才算 `adaptive`。

### Live / Hook 仅 Web

Live 模式（浏览器内变体热替换）与设计检测 Hook 仅在 web 项目启用。Native 项目（含 RN / Flutter）由 `.tsx/.ts/.js` 组成，Hook 会误报，所以路由直接跳过。

## 3. 23 个设计动作命令

每个命令含：用途 / 适用场景 / 执行步骤 / 检查项 / 反模式。

### 精修与审计类

#### polish — 精修

功能完整后的最后一道。对齐设计系统，系统化精修视觉、IA、排版、交互、动效、无障碍。

- **执行步骤**：发现设计系统 → 标注偏离并分类（缺 token / 重复实现 / 概念错位）→ 评估完整度与质量标杆 → 三分类问题（外观 vs 功能，紧急 vs 可缓）→ 系统化修整 → 自用一遍 + 真机测一遍。
- **检查项**：对齐到 token、IA 形态匹配邻近功能、所有交互态完整、对比度达标、`prefers-reduced-motion` 被尊重、无 console 错、无 CLS。
- **反模式**：功能没完成就开始 polish；不查设计系统就修；用一次性组件替代已存在的共享组件；硬编码本应是 token 的值；只完美一个角落其他地方粗略。

#### audit — 审计

无障碍与质量门禁检查。a11y 只在这里做，不在设计时做（见 §5）。

- **执行步骤**：5 维度扫描（a11y / 性能 / 主题化 / 响应式 / 反模式）→ 每维 0–4 评分 → 出报告（健康分、严重度 P0–P3、模式性问题、正面发现、推荐命令）。
- **检查项**：对比度 ≥4.5:1（正文）/ 3:1（UI 组件）、ARIA 角色与标签、键盘顺序与焦点、语义 HTML、alt 文本、表单标签；CLS、LCP、INP、bundle 体积；token 覆盖率与暗色模式；触控目标 44px、断点覆盖；AI slop tell（梯度文字、glassmorphism、紫蓝梯度、英雄指标卡网格）。
- **反模式**：报告问题不说影响；给模糊建议（"改善可访问性"）；跳过正面发现；不分级（全 P0）；把 detector 的 clean 结果当作设计好的证据。

#### critique — 评审

独立评审产出优先级问题清单，作为 polish 的输入。

- **执行步骤**：解析目标到具体文件或 URL → 双盲双 agent 评估（A 设计评审 / B detector + 浏览器证据，两者隔离直到合成）→ 合成报告（Nielsen 10 启发式 0–4 评分、AI slop 判决、认知负荷、情感旅程、Persona 红旗、P0–P3 优先问题）→ 持久化快照。
- **检查项**：报告首行声明评估路径（双 agent 还是降级单 context）；具体到元素与交互，不是"某些组件"；每条问题配 Why it matters + Fix + Suggested command。
- **反模式**：跳过子 agent 直接单线程跑（必须出降级横幅）；detector 与设计评审共享上下文（detector 会锚定判断）；只列问题不给修复方向；软化学术批评。

### 色彩与排版类

#### colorize — 配色

基于寄存器 + 品牌选配色方案，token 化。

- **执行步骤**：评估当前配色机会（缺色 / 误用 / 语义空缺）→ 选策略（Restrained / Committed / Full palette / Drenched）→ 60-30-10 视觉重量分配 → OKLCH 色彩空间 → 写 token。
- **检查项**：OKLCH 而非 HSL（感知均匀）；中性带微量 chroma 倾向品牌色而非纯灰；语义色完整（success/error/warning/info）；WCAG AA 达标；不靠颜色单一传递信息；无紫蓝梯度（AI slop）；`border-left/right > 1px` 的色条绝对禁止。
- **反模式**：彩虹大杂烩；灰色字压在彩色底上（用同色更暗的色阶或透明度）；默认紫蓝梯度；用 alpha 透明度代替显式覆盖色（alpha 是设计气味）。

#### typeset — 排版

字体阶梯 / 字重 / 行高 / 字距。寄存器间有分歧。

- **执行步骤**：双盲评估（A 排版评估 + B 机械预扫描，detector 输出不能先于视觉判断进入上下文）→ 字体选择流程（3 个具象品牌口音词 → 反射拒绝清单 → 真实字体目录浏览 → 交叉验证）→ 阶梯与权重策略 → 可读性修整 → OpenType 细节。
- **检查项**：body ≥16px、行宽 45–75ch、行高随字号反比、暗底亮字 +0.05–0.1 行高 + 微字距；全大写标签加 5–12% letter-spacing；`font-display: swap` + fallback metric 匹配；变量字体 3+ 字重比静态多文件小；不硬编码 px，用 rem；不 disable 缩放。
- **反模式**：反射性选 Inter / Roboto / Fraunces / Playfair / Space Grotesk（训练数据默认）；14/15/16px 这种扁平阶梯；一族里挑两个相似 sans 配对；装饰字用于正文；`user-scalable=no`。

#### bolder — 加粗

增强视觉重量与层级对比。**Bold ≠ 多特效**，AI 默认会塞紫青梯度 + glassmorphism + 霓虹暗底，这些恰恰是 bold 的反面。

- **执行步骤**：先拒绝 AI 套路 → 评估 weakness 来源（通用 / 阶梯太平 / 对比过低 / 静态 / 可预测 / 层级扁平）→ 设计系统锁（系统是边界，先在系统内放大）→ 一次放大（焦点 / 系统杠杆 / 风险预算 / 层级对比）。
- **检查项**：先放大现有语言再加新元素；新颜色 / 梯度 / 阴影 / 圆角 / 字体要么不存在要么明确批准并文档化；主从对比是放大目标，不是所有元素都更响；"AI 加粗了这个"的盲测不成立。
- **反模式**：未批准就引入新设计系统原语；用装饰盖住弱层级；所有元素同时放大（结果更扁平不是更 bold）；牺牲可读性换美学；每节 scroll-fade-rise（饱和 AI 默认）。

#### quieter — 减弱

降低视觉噪音，让重点突出。Quiet 比 bold 难，需要精度。

- **执行步骤**：评估强度来源（饱和度 / 对比极值 / 视觉重量 / 动效过度 / 复杂度 / 尺寸）→ 策略（调色 / 层级 / 简化 / 精致）→ 系统化降低强度（色 / 视觉重量 / 简化 / 动效 / 构图）。
- **检查项**：饱和度降到 70–85%；中性带品牌色微量倾向；900→600、700→500 的字重降级；增加留白减少密度；边框变薄或移除；动效距离从 40px 降到 10–20px；移除装饰动效保留功能动效；POV 在剪裁后存活。
- **反模式**：所有元素同尺寸同字重（层级还是要）；quiet = 灰度；抹除个性变通用；功能性元素失去清晰 affordance。

### 布局与形状类

#### layout — 布局

网格 / 间距 / 容器 / 响应式。寄存器间有分歧。

- **执行步骤**：双盲评估（A 布局评估 + B detector 预扫描）→ 评估间距 / 层级 / 网格 / 节奏 / 密度 → 立间距系统（4pt 基础比 8pt 更细）→ 创造节奏（紧组 + 朗松分离）→ 选工具（Flex 1D / Grid 2D / container query 组件级）→ 破卡片网格单调 → 强化层级 → 光学校正。
- **检查项**：间距全来自定义集；紧组（8–12px 兄弟）+ 大分离（48–96px 节）交替；触控目标 44×44 最小（视觉元素更小时用 padding 或伪元素扩大命中区）；卡片不嵌套卡片；用 squint test 验层级。
- **反模式**：任意间距值（13px 这种）；所有间距相等；什么都包卡片；卡片嵌卡片；到处都是 icon + heading + text 重复网格；默认英雄指标卡布局。

#### shape — 塑形

信息架构与流程形状，匹配系统而非只改表面。

- **执行步骤**：Phase 1 发现访谈（目的 / 内容 / 设计方向 / 范围 / 约束 / 反目标，2–3 题一轮，1 轮默认）→ 可选视觉方向探针（仅 mid-fi+ 且 harness 有原生图像生成时）→ Phase 2 设计 brief（10 节结构化或 3–5 bullet 紧凑式，按 brief 清晰度选）→ 停下等用户确认。
- **检查项**：未确认 brief 不写代码；视觉决策三件套（色彩策略 / 场景句子 / 2–3 个具名锚点参考）；状态列表完整（default/empty/loading/error/success/edge）；推荐参考文件列表指向实现期最该读的命令。
- **反模式**：把 shape 当成实现命令；跳过访谈直接合成完整 brief；视觉方向探针取代 brief；4 选项菜单式提问（应该 assert-then-confirm）。

#### delight — 愉悦感

微交互 / 惊喜细节。寄存器间有分歧。

- **执行步骤**：找自然 delight 时刻（成功 / 空状态 / 加载 / 成就 / 交互 / 错误 / 彩蛋）→ 选策略（微妙精致 / 俏皮个性 / 帮助惊喜 / 感官丰富）→ 实施（微交互 / 个性化文案 / 插画 / 满足感交互 / 声音 / 彩蛋）。
- **检查项**：delight 时刻 <1 秒、不阻塞功能、可跳过；隐藏细节奖励探索；匹配品牌个性与情感时刻；重复使用仍新鲜（变化响应）；空状态文案是产品特定的不是 AI 填充（"Herding pixels" 这类要拒绝）。
- **反模式**：为 delight 延迟核心功能；每个交互都 delight（特殊时刻不再特殊）；用 delight 掩盖差 UX；忽略 `prefers-reduced-motion`；银行 app 用俏皮文案（读空气）。

### 动效与交互类

#### animate — 动效

动效系统 / 缓动 / 时长 / 空间连续。寄存器间有分歧。

- **执行步骤**：评估动效机会（缺反馈 / 突兀切换 / 关系不清 / 缺 delight / 缺引导）→ 策略（一个 hero 时刻 + 反馈层 + 转场层 + delight 层）→ 实施（入场 / 微交互 / 状态转场 / 导航流 / 反馈引导）。
- **检查项**：100/300/500 时长规则（100–150 ms 即时反馈 / 200–300 ms 状态切换 / 300–500 ms 布局变化 / 500–800 ms 入场）；用 ease-out-quart/quint/expo，**永不** bounce 或 elastic；退场比入场快约 75%；`prefers-reduced-motion` 必尊重；不随意动画 `width/height/top/left/margin`，用 transform / FLIP / grid-template-rows。
- **反模式**：bounce / elastic 缓动；反馈动效 >500 ms；无目的动效；动画一切（疲劳）；忽略 reduced motion；阻塞交互。

#### craft — 工艺

组件细节打磨，阴影 / 边框 / 圆角 / 过渡。多门控流程，不可压缩。

- **执行步骤**：Step 0 项目基础（用现有框架 / 组件库 / 图标集）→ Step 1 shape → Step 2 加载参考 → Step 3 视觉方向与资产（harness 有原生图像生成时走完整 codex 流程，无则一行声明跳过）→ Step 4 生产级实现 → Step 5 浏览器内视觉迭代 → Step 6 呈现。
- **检查项**：真实内容（无占位文案 / 占位图 / 死链 / 假控件）；保留 approved mock 的主要成分；语义优先（真实标题 / landmarks / labels / 状态播报）；全状态覆盖；触控目标；图片 URL 已验证；尊重构建管线（不直接写 `build/` `dist/`）。
- **反模式**：把 shape 确认当作 code-green（shape 之后还有方向 / 调色 / mock 几道门）；用卡片 / 项目符号 / emoji / 假指标 / CSS 面板代替必需图像；压缩门控；不读截图就声称迭代完成。

### 提取与蒸馏类

#### extract — 提取

从现有代码 / 设计提取设计系统。

- **执行步骤**：发现设计系统 → 识别模式（重复组件 / 硬编码值 / 不一致变体 / 组合模式 / 类型样式 / 动效模式）→ 评估价值（仅 3+ 次同意图才提取）→ 计划（组件 / token / 变体 / 命名 / 迁移路径）→ 提取并丰富 → 迁移 → 文档。
- **检查项**：组件有清晰 props API + 合理默认 + 完整变体 + a11y 内建 + 文档；token 语义命名（primitive vs semantic）；删除被替代的旧实现。
- **反模式**：提取一次性上下文特定的实现；过度通用化到无用；为每个值建 token（token 要有语义含义）；意图不同的两按钮合并（外观相似但目的不同应分开）。

#### distill — 蒸馏

把复杂设计系统精简为核心规则。

- **执行步骤**：评估复杂度来源（元素过多 / 变体过多 / 信息过载 / 视觉噪音 / 层级混乱 / 功能蔓延）→ 找本质（一个核心用户目标、20% 价值来源）→ 系统化简化（IA / 视觉 / 布局 / 交互 / 内容 / 代码）。
- **检查项**：任务完成更快；认知负荷更低；必要功能仍可达；层级更清；性能更好。
- **反模式**：移除必要功能（简化 ≠ 功能缺失）；牺牲 a11y；过度简化到神秘（mystery ≠ minimalism）；移除用户决策所需信息；完全消除层级。

#### document — 文档

生成 DESIGN.md 设计规范文档。

- **执行步骤**：扫描模式（默认）或种子模式（pre-implementation）→ 找设计资产（CSS custom properties / Tailwind config / CSS-in-JS / token 文件 / 组件库 / 全局样式 / 渲染输出）→ 自动提取（色彩 / 字体 / 阴影 / 组件）→ 暂存 frontmatter → 问质性输入（Creative North Star / Overview voice / 色彩性格 / 阴影哲学 / 组件哲学）→ 写 DESIGN.md（YAML frontmatter + 6 节固定顺序）。
- **检查项**：frontmatter 用 `{path.to.token}` 引用；色彩按项目姿态选 OKLCH 或 hex（不分裂真相源）；组件 sub-token 限 8 prop（backgroundColor/textColor/typography/rounded/padding/size/height/width）；6 节字符精确匹配 spec（Overview / Colors / Typography / Elevation / Components / Do's and Don'ts）；不额外加顶节。
- **反模式**：silent overwrite 已存在 DESIGN.md；编排额外顶节（Layout Principles / Motion 等）塞进 spec 之外；用 Material 默认名重命名项目已用的 scale key。

### 强化与优化类

#### harden — 加固

边界情况 / 错误状态 / 防御性设计。

- **执行步骤**：测极端输入（超长 / 超短 / emoji / RTL / 大数 / 千项 / 空数据）→ 测错误场景（网络 / API / 验证 / 权限 / 限流 / 并发）→ 测 i18n（德语 +30% / RTL / CJK / 日期 / 货币 / 复数）→ 系统化加固（文本溢出 / i18n / 错误处理 / 边界 / 输入校验 / a11y 韧性 / 性能韧性）。
- **检查项**：`text-overflow: ellipsis` / `-webkit-line-clamp` / `overflow-wrap: break-word`；`min-width: 0` 让 flex/grid 子项可缩；逻辑属性 `margin-inline-start` 而非 `margin-left`；`Intl.DateTimeFormat` / `Intl.NumberFormat`；空状态 / 加载 / 大数据集 / 并发 / 权限状态全覆盖；防双提交（loading 时 disable）。
- **反模式**：假设完美输入；忽略 i18n；通用错误消息（"Error occurred"）；信任客户端校验；固定宽度文本容器；假设英语长度；一个组件出错阻塞整个界面。

#### optimize — 优化

性能与加载优化。CLS / 图片 / 懒加载。

- **执行步骤**：测当前状态（Core Web Vitals / bundle / runtime / 网络）→ 找瓶颈 → 加载优化（图片 / JS bundle / CSS / 字体 / 加载策略）→ 渲染优化（避免 layout thrashing / `contain` / `content-visibility`）→ 动效优化（GPU 加速 / 60fps / IntersectionObserver）→ Core Web Vitals（LCP <2.5s / INP <200ms / CLS <0.1）。
- **检查项**：现代图片格式（WebP / AVIF）；`srcset` + `sizes` 响应式图；`loading="lazy"` 折叠下；`font-display: swap` + subset + preload 关键字重；`aspect-ratio` 预留图位防 CLS；批量读后批量写避免 layout thrashing。
- **反模式**：未测就优化（过早优化）；牺牲 a11y 换性能；`will-change` 到处用（建层耗内存）；折叠上内容懒加载；微优化忽略主要瓶颈；忘记移动端（更慢设备更慢网络）。

#### clarify — 澄清

文案与信息层级清晰化。

- **执行步骤**：找清晰度问题（jargon / 歧义 / 被动 / 长度 / 假设 / 缺上下文 / 语气错位）→ 策略（主信息 / 行动 / 语气 / 约束）→ 系统化改写（错误消息 / 表单标签 / 按钮 CTA / 帮助文本 / 空状态 / 成功消息 / 加载态 / 确认对话框 / 导航）。
- **检查项**：错误消息公式（发生了什么 + 为什么 + 怎么修）；按钮"verb + object"（"Save changes" 不是 "OK"）；破坏性操作命名破坏（"Delete 5 items" 不是 "Delete selected"）；术语一致（Delete / Settings / Sign in / Create 各选一个）；空状态是 onboarding 时刻；加载文案产品特定（不"Herding pixels"）；链接文本独立有意义。
- **反模式**：jargon 不解释；责备用户（"You made an error"）；模糊错误（"Something went wrong"）；为变体换术语；错误用幽默；占位符当唯一标签。

#### overdrive — 超驱

突破常规的视觉冲击，用于品牌页。**Propose Before Building**，必须先提 2–3 方向等用户选。

- **执行步骤**：评估"非凡"在此上下文含义（视觉/营销面 → 感官；功能 UI → 手感；性能关键 UI → 隐形但感觉得到；数据密集 UI → 流畅）→ 提 2–3 方向（不同技术 / 野心级别 / 美学）→ 等用户选 → 浏览器自动化迭代（技术上 ambitious 的效果几乎一次不成）。
- **检查项**：渐进增强非协商（每技术都要 graceful degrade）；60fps 目标，跌破 50 就简化；`prefers-reduced-motion` 必尊重并给静态替代；lazy 初始化重资源（WebGL / WASM）；暂停屏外渲染；中端真机测试。
- **反模式**：跳过 propose 直接实现（最高 misfire 风险）；用 bleeding-edge API 无 fallback；声音未明示 opt-in；技术野心盖住弱设计基础（先用其他命令修）；多层竞争非凡时刻（焦点制造冲击，过度制造噪音）。

### 初始化与适配类

#### init — 初始化

项目设计系统搭建。判断寄存器 + 平台 + 生成 DESIGN.md。

- **执行步骤**：Step 1 加载当前状态（PRODUCT.md / DESIGN.md / live config 是否存在）→ Step 2 探索代码库（README / package.json / 组件 / 品牌资产 / token / 形成 register 与 platform 假设）→ Step 3 战略访谈（register 先 → platform 紧随 → 用户与目的 → 定位 → 品牌个性 → 反参考 → 转化与证明仅 brand → a11y）→ Step 4 写 PRODUCT.md → Step 5 决定 DESIGN.md（scan 模式或 seed 模式）→ Step 6 配置 live mode（仅 web + 有代码）→ Step 7 推荐下一步命令。
- **检查项**：register / platform 裸值不写散文；从代码爬到的假设要用户确认；未确认不写 PRODUCT.md；至少一轮真实用户回答；不问颜色 / 字体 / 圆角（那是 DESIGN.md 的事）。
- **反模式**：从原始 task prompt 单独合成 PRODUCT.md；把 brand-only 问题（转化与证明）和决定 register 的问题混一轮；silent overwrite 已有文件；给 native 项目配置 live mode。

#### adapt — 适配

响应式与多平台适配。**适配不是缩放像素，是为新上下文重新思考体验**。

- **执行步骤**：评估适配挑战（源上下文假设 / 目标上下文约束 / 适配挑战）→ 策略（移动 / 平板 / 桌面 / 打印 / 邮件各自策略）→ 实施（响应式断点 / 布局技术 / 触控适配 / 内容适配 / 导航适配）。
- **检查项**：mobile-first（`min-width` 查询叠加复杂度）；内容驱动断点而非设备尺寸；检测输入方式（`@media (pointer: fine/coarse)` `@media (hover: hover/none)`）；`env(safe-area-inset-*)` + `viewport-fit=cover`；`srcset` + `sizes` 响应式图；触控 44×44；不依赖 hover 传递功能。
- **反模式**：desktop-first；设备检测代替特性检测；分离 mobile/desktop 代码库；忽略平板与横屏；假设所有移动设备都强；隐藏核心功能；跨上下文用不同 IA（混淆）。

#### onboard — 引导

设计系统对齐与新成员引导。**Onboarding 的任务不是教产品，是把人带到证明产品值得花时间的那一刻**。

- **执行步骤**：评估 onboarding 需求（用户目标 / 困惑点 / 卡点 / aha 时刻 / 用户经验 / 动机 / 时间）→ 定义成功（最小学习量 / 关键行动 / 完成率 / time-to-value）→ 设计体验（初始产品 onboarding / 功能发现 / 导览 / 交互教程 / 文档与帮助 / 空状态）。
- **检查项**：show don't tell（工作示例不是描述）；可选可跳过（experienced 用户可绕过）；time-to-value（前 20% 概念出 80% 价值）；上下文优于仪式（在需要时教，而不是开场灌输）；尊重用户智商；空状态四件套（会有什么 / 为何重要 / 如何开始 / 视觉兴趣）。
- **反模式**：强迫走长 onboarding 才让用产品；居高临下 obvious 解释；同一 tooltip 反复显示（尊重 dismiss）；tour 期间锁全 UI；与真实产品脱节的教程模式；前置信息轰炸；藏起 Skip。

### 工具命令

#### live — 实时变体

浏览器内选元素 → 选设计动作 → AI 生成 HTML+CSS 变体热替换。仅 web。

- **执行步骤**：boot → 打开 app URL（不是 helper port）→ 长轮询循环（generate / steer / accept / discard / prefetch / manual_edit_apply / timeout / exit）→ 失败用 `live-status` / `live-resume` 恢复（持久化 journal）。
- **检查项**：PRODUCT.md 战略决策赢，DESIGN.md 视觉决策赢；不贴 PRODUCT/DESIGN 全文进 chat；变体必须声明签名参数（color-amount / scale / density / structure 等）；无 DESIGN.md 时从 CSS 变量 + 计算样式 + 兄弟组件提取身份，身份保留是默认，偏离要明确触发。
- **反模式**：把 helper port 当 app URL；短 `--timeout=`（必须长轮询）；chat 啰嗦 recap；忽略持久化 journal。

#### hooks — 设计检测钩子

管理 per-project 设计检测器。edit 后 post-tool-use 推 reminder（Claude Code / Codex / Copilot）或 preToolUse 阻止坏写（Cursor）。

- **执行步骤**：路由 action（status / on / off / ignore-rule / ignore-file / ignore-value / reset）→ 调 `hook-admin.mjs` → 用户验证后持久化例外。
- **检查项**：例外收窄到最具体（`ignore-value` 优于 `ignore-rule`，file-scoped 优于 `ignore-file`）；共享 config 默认，`--local` 仅用户明确要私人例外；inline 注释 disable marker 仅随导出文件离开仓库时用。
- **反模式**：手工编辑项目设计 config（必须走 admin 脚本保 schema 一致）；detector clean 当作设计好的证据；用 `ignore-file` 静音真 UI 文件（应 `ignore-value "*" --file`）。

## 4. 反 AI 散文 denylist（构建期校验）

设计文档与用户面文案都要通过。clean 不是合格证明，是底线。

### 硬禁（构建期失败）

英文 AI 套路词，构建期 regex 直接失败：

| Banned | Rationale | 替换 |
|---|---|---|
| `seamless` / `seamlessly` | 空心正词，不指明何处无摩擦 | 说具体无摩擦的是什么 |
| `robust` / `robustness` | 空心正词，不引失败模式 | 引具体处理的失败模式 |
| `elevate` / `elevates` | 营销动词 | 用具体动词（improve / raise / sharpen） |
| `empower` / `empowers` | 营销动词 | "let you" / "make possible" |
| `underscore` / `underscores` | AI tell | "show" / "make clear" |
| `pivotal` | 空心正词 | "central" / "key" 或描述角色 |
| `tapestry` | AI 风景名词 | 删 |
| `data-driven` | 空心营销形容词 | 引数据来源（"validated against 15 briefs"） |
| `delve` / `delves` / `delved` | 最被 flag 的 AI tell | "look at" / "explore" 或删 |
| `load-bearing` | 几乎总是含糊 | 名具体作用（"the decision that shapes the rest"） |
| `highest-leverage` | 含糊影响声明 | 说具体收益（"the change that moves the design most"） |
| `biggest unlock` | 营销话 | 描述实际变化 |
| `reflex defaults` | eval 团队行话 | "instincts" / "first guesses" |
| `collapses into monoculture` | eval 论文腔 | 描述具体出错（"every model picked the same three fonts"） |
| `in today's …` | 通用开场 | 直接进入要点 |
| `gone are the days` | 陈词开场 | 直接说 |
| `whether you're …` | 讨好受众不指任何人 | 选一个读者写给他 |
| `let's dive in` | 清嗓子 | 直接开始 |
| `in summary` / `in conclusion` | 复述刚说的 | 用最强句子结尾，信任读者 |
| `moreover` / `furthermore` | 节拍器过渡 | 删或用 "also" 或重构 |
| Em dash `—` / `--` | 决策回避（没选子句关系） | 逗号 / 冒号 / 分号 / 句号 / 括号，选关系 |

### 中文等价（同义禁止）

空洞词，AI 散文中文变体：

- 无缝 / 无缝衔接
- 赋能（除非技术语境"power"）
- 抓手 / 闭环 / 沉淀 / 生态 / 链路 / 打通
- 全面提升 / 全方位 / 多维度（不引数字的正词）
- 助力 / 助推 / 赋智
- 一站式（除非真有站点）
- 智能化（除非真有 ML 且说清楚）
- 数字化转型（除非真在转且说清转什么）
- 用户至上 / 体验为王（口号非信息）
- 极致 / 顶级 / 卓越（无数字无标准）

替换原则：能换成具体数字 / 具体文件 / 具体版本 / 具体失败模式就换。不能换的，删。

### 结构性问题（需人工判断，构建期 regex 抓不到）

- **否定枢纽**："不是 X，而是 Y" / " less about X, more about Y"。比任何词汇都更强的 AI tell。少用，多数应替换为直接正向声明。
- **三元自动巡航**：每列三项，每形容词三连（"fast, simple, and powerful"）。变化计数：用 2 或 4，用 1。
- **五段式论文骨架**：每页都是 intro → 3 节 → conclusion。打乱。从例子开头。跳 conclusion。让某些节只有一句。
- **统一段落节奏**：插一个 4 词句。插一个一行段。
- **空洞自信**："Powerful" 无数字。换具体事实。
- **堆叠对冲**："It might potentially be useful to consider..."。单个对冲可，堆叠像训练。
- **可互换文案**：把产品名换成竞品名，若没有任何一句变假，文案就是通用的。

## 5. a11y 审计分离原则

a11y 检查只在 audit 命令做，不在设计时做。

### 原因

模型在设计期被提醒无障碍会**过度谨慎**，产出保守、欠设计的方案。设计期专注视觉与体验，审计期专项检查对比度 / 键盘 / 屏幕阅读器 / ARIA。两条通道分离，避免互相拖累。

### 实践

- polish / typeset / layout / colorize 等设计命令：专注视觉与体验标杆，不主动跑 a11y 扫描。
- audit 命令：5 维度之一就是 a11y，0–4 评分，P0–P3 严重度，配修复建议与 suggested command。
- 设计期写语义 HTML 是基本工，不算 a11y 检查（那是实现质量）。a11y 检查指：对比度达标、键盘顺序、屏幕阅读器播报、ARIA 角色 / 标签 / 状态、焦点管理、reduced motion、高对比模式。
- 暗底亮字行高 +0.05–0.1 这类补偿是**设计决策**，写在 typeset 里；不是 a11y 检查项。

### 反模式

设计期就跑对比度扫描 → 模型把每个色阶都拉到 AAA → 设计变成"安全但平庸"；或模型自我审查不敢用品牌色 → 失去个性。审计期再校验，不达标再回头微调，是正确循环。

## 6. DESIGN.md 生产级范例学习要点

从一个真实生产级 DESIGN.md 提炼的关键模式：

### OKLCH 色彩空间

- 比 HSL 感知均匀：50% lightness 的黄和蓝在 HSL 里亮度感差异巨大，OKLCH 里等步进 lightness 视觉也等步进。
- `oklch(lightness chroma hue)`，lightness 0–100%，chroma 约 0–0.4，hue 0–360。
- 建色阶：固定 chroma+hue，变 lightness；**接近纯白或纯黑时降 chroma**，否则高 chroma 在极端 lightness 显得 garish。
- 新颜色一律 OKLCH 声明，hex 只出现在第三方示例或导入资产里。
- 不要默认选 hue 250（蓝）或 hue 60（暖橙），那是 AI 设计的默认反射，不是任何具体品牌的正确答案。

### Brand Anchors 概念

- 2 个品牌锚色 + 暗色底，而非泛用色板。主锚承载品牌信号，次锚标记状态与对比。
- 锚色有 ramp（pale / rich / deep / rule / glint 等多档），但 ramp 服务于锚的角色，不是独立色板。
- 中性色带微量 chroma 倾向品牌色（0.005–0.015），创造潜意识凝聚；不倾向"暖=友好，冷=科技"公式。
- 文化符号调色板（如中国红、日本金）不要 reflex 拿，让文化读感来自字体 / 图像 / 文案，不是调色板。

### Kit Consumption Rule

- 一套全局组件 kit，每页都吃。优先用 kit 原语（`.ks-button` `.ks-bento` `.ks-section`），禁止重复造同类组件类（`.hero-cta-primary` `.footer-cta` 都是 `.ks-button-primary` 的违规重造）。
- 仅当 kit 真不覆盖时才发明，且要 flag —— 真正解决复现需求的新模式属于 kit，不属于页 CSS。
- 页 CSS 用于真正页面特定的景色（hero 插画、独特编辑视觉），不是重造 kit 已有的原语。
- kit 原语消费 token，不硬编码值。需要 kit 外的颜色 / 字号 / 缓动时直接读 token（`var(--brand-accent)` `var(--type-display-size)`），不在页 CSS 里手打 oklch 值或字号。

### Token 引用链

- 组件用 `{colors.brand-accent}` 引用，不写裸值。
- frontmatter 中 token 引用规则：组件可引用 primitive；primitive 不互相引用。
- 组件 sub-token 限 8 prop（`backgroundColor` / `textColor` / `typography` / `rounded` / `padding` / `size` / `height` / `width`）。阴影、动效、focus ring、backdrop-filter 不进 frontmatter，写在 sidecar。
- 两种真相源策略二选一：项目有"OKLCH-only"教条 → frontmatter 直接 OKLCH 接受 Stitch linter warning；项目要 Stitch 严格合规 → frontmatter hex，OKLCH 在 prose 作权威参考。**不无理由分裂真相源**。

### 其他生产级模式

- **权重反转**：hero h1 用 weight 100，section h2 用 weight 300。h1 比 h2 更轻是故意的，让页面呼吸；section 锚点更重以稳住每块。不要把两个权重归一。
- **暗底亮字补偿三轴**：行高 +0.05–0.1、字距 +0.01–0.02em、字重升一档（regular → medium）。感知重量在三轴同时下降，三轴都要补。
- **Hairline First**：1px hairline 优先于阴影。无默认卡片阴影，卡片靠边框与底色差。无 glass（装饰性 blur/glass 面板不属此系统）。
- **Texture Needs Contrast**：文字不直接坐高对比 leaf texture 上，要加 lacquer veil 或把 texture 移到边缘。
- **Asset-Led Material**：品牌承载材料用光栅资产或生成图，不用手画 SVG 近似 leaf / dust / oxidation / clockwork。代码原生几何留给简单 hairline / 布局网格 / 功能 UI 结构。
- **Picker Is Brand**：live mode UI 是产品 chrome 不是宿主页 chrome，永远带 lacquer-deep fill + 雕刻 tile mark + 主色于 mark 与 active 控件，不按宿主页 theme 适配。
- **Named Rules 模式**：用"The [Rule Name] Rule"形式写强制规则（"The Gold Carries Brand Rule"、"The Patina Has Meaning Rule"、"The Texture Budget Rule"、"The OKLCH-Only Rule"）。短、有力、可执行，比段落散文更易被 agent 引用与遵守。
- **6 节固定顺序**：Overview / Colors / Typography / Elevation / Components / Do's and Don'ts。可选 evocative 副标题（`## 2. Colors: The Coastal Palette`），但每节字面词必须出现，不重排，不重命名，不加额外顶节。其他 DESIGN.md-aware 工具按字符匹配解析。
