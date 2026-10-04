# WorkBuddy 视觉设计

内部公共 Component，不单独注册或发布为 Skill。负责颜色、文字层次、留白、圆角、边框、阴影和视觉状态；不决定取哪些数据、用什么解释结构或调用哪个工具。

唯一视觉设计权威是 `contracts/financial-visualization/v2/` 的设计系统、tokens 和 profiles，以及对应服务端解析和 Widget 实现。发布时由套件绑定该设计契约；不要在 Skill、Expert 或本 Component 内复制一套色值。主题由服务端写入 `renderPlan.design`，LLM 的 `dashboard_spec` 不接收主题参数。

纯视觉规则维护在 specifications/VISUAL-SPECIFICATION.md；金融场景与信息结构维护在 specifications/FINANCIAL-SCENE-SPECIFICATION.md。新增视觉值只登记到 tokens/profiles；只有新增语义槽或结构字段时才同步修改协议 Schema、解析器和验证，不把文档章节当作工具参数。

## 可替换的构建绑定

本目录 `theme-binding.json` 是固定换肤入口。只需替换该文件的 `defaultDesignProfileRef` 为 FVDS 已注册、相同市场涨跌约定与密度的主题，再正常重建两个 MCP；无需修改业务 Skill、选图逻辑、Composer 或 Widget。默认仍是现有浅色主题，允许切换到已注册的中国市场暗色主题。未知主题、额外内联色值、第二套 token 文件或改变红涨绿跌语义的绑定会在构建时失败。

构建器 `publication/lib/visual-design-binding.mjs` 从唯一 canonical FVDS package 生成 `dist/node_modules/@orientfutures/financial-visualization-contracts`，仅固化默认 profile 选择；这是发布产物，不是第二份维护源。服务端 `dist` 入口和 Widget 构建共用该产物，因此返回的 `renderPlan.design`、FVAS 主题与实际图形一致。`dist/visual-design-binding.json` 记录 profile、版本与摘要供验收。运行时不热改主题，也不在浏览器偷偷覆盖计划。

新增从未注册过的色板时，仍先在唯一 FVDS tokens/profiles 中登记，再替换本组件绑定并重建；本组件不接受任意颜色覆盖，不复制第二套设计系统。业务逻辑和图形结构在这个过程中保持不变。

## 不随主题变化的表达约束

- 产业链 `COMMODITY` 用矩形卡片，`PROCESS` 用小椭圆；节点形状、关系方向、字段含义和交互行为属于表达/渲染语义，不是可随配色替换的装饰。
- 涨跌、风险、选中、普通序列各有独立语义，不能因统一品牌色丢失金融方向。配色升级只能替换对应语义 token，不重写事实或图形结构。
- Dashboard 保持整体背景、清晰层次和克制边框；避免多层大底色、重阴影、重复标题和空泛副标题。
- 单个 Dashboard 只保留一个来源标识：`数据来源：东方证券期货`。内部服务、目录和章节留在审计数据，不铺在每个图区下。
- 不加“全屏查看”按钮。保留图表已经支持的悬浮提示、高亮、图例开关、节点上下游高亮、重置、键盘焦点及必要的平移缩放。

替换本 Component 的视觉指导及其关联主题文件，应只影响样式。发布验收须在相同证据和相同 DashboardSpec 下检查：区块类型/顺序、绑定值、节点拓扑和交互不变。若确实要改变结构，单独修改视觉表达或渲染 Component 并做相应验收，不夹在主题升级里。


## 对外来源与紧凑单位

所有 MCP 支持的正文、表格、图表、脚注和交付文件，对外来源只输出“数据来源：东方证券期货”。不得追加括号、竖线或分号后的内部服务、采购供应商、原始来源、研究机构、知识集合或章节归属。`provenance.sources`、上游来源字段仅供内部核验，不作为正文来源展开。指标对象、统计范围、实际日期、频率和影响解释的口径差异仍须保留。

产业链节点紧凑区分行展示名称、合约代码和价格；省略 CNY 等重复单位标签，完整单位留在悬停详情和原始证据。其他图中可省略重复单位标签；不同量纲仍分图/分组，并在组标题或详情保留识别所需的单位，不因省略标签混合计算或更改原值。
