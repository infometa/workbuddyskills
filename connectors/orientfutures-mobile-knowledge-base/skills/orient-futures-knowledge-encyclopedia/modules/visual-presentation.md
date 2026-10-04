# 百科视觉编排

先执行 [回答与合规边界](answer-and-boundaries.md)。本模块只组织定义、公式变量、一般机制和单一合约静态事实；公共组件中的“联合解读、理论加实盘、趋势/信号示意”不扩大权限。

有视觉需求时先完整读取 [视觉表达](../workbuddy-visual-expression/COMPONENT.md)、[视觉设计](../workbuddy-visual-design/COMPONENT.md)、[视觉渲染](../workbuddy-visual-rendering/COMPONENT.md)，再完成必要知识或静态查询。知识目录不是证据，不画目录图，不为填图额外取数。

提交前逐项检查标题、正文、图注、公式 interpretation、图例和所有可控文本，只保留定义/变量/条件。不能使用实盘指标证据；不能把真实行情与 macd-cross/moving-average-cross 机制拼在一起。纯术语示意只有在本轮审核定义支持、明确 illustrative 且能确认没有信号/操作文案时才可选；不能保证 Provider 自动文字合规则用文字/表格。不得靠免责声明、原生绘图或虚构隐藏参数绕过。

选择项目图时仅调用 knowledge_visual_compose；唯一入参 dashboard_spec，结构为 specVersion=1.0.0、title、blocks（1～8），最多 12 个不同证据引用。数值槽只使用本轮有效 evidenceRef 与摘要已声明 key，知识块必须绑定直接支持其定义的审核知识。不读取内部文件、resolve API、renderPlan 或截图。

全请求一个 Composer 一次，包括参数校验失败；提交、成功或未知不补图，明确失败用同次数据文字/表格。ready 不等于宿主显示，不等待回执。简单问题直接文字；原生例外同样通过内容门，不能恢复被禁的实盘解释。

正文、图表、替代文本、文件和追问统一逐句复核；来源仅“数据来源：东方证券期货”。没有独立市场图形的权限不代表不能解释用户所问字段。固定公司入口按业务链接组件单独展示，不夹入知识图；排除账户业务不展示任何入口。
