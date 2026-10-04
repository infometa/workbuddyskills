# 个人业务视觉编排

先完整执行 [范围门](safety-and-fallback.md)。纯排除业务只固定电话回复，不加载视觉组件、不查询、不出图、不展示任何业务入口。混合问题仅图示完全独立的允许个人业务，不能把排除业务画成通用流程。

通过范围门且确需视觉时，先完整读取 [视觉表达](../workbuddy-visual-expression/COMPONENT.md)、[视觉设计](../workbuddy-visual-design/COMPONENT.md)、[视觉渲染](../workbuddy-visual-rendering/COMPONENT.md)。只用本轮实际审核正文组织个人普通流程、材料、定义和费用公式；简单问答直接文字，不为图取无关知识。

一个查询仅 knowledge_visual_compose 一次，唯一 dashboard_spec 参数，specVersion=1.0.0、title、blocks（1～8），最多 12 个不同本轮有效证据引用。知识块须审核知识，数值只绑定已声明 key，不手填个人进度或费用。process 表示一般步骤，不标用户已完成、审核通过或已开通。

图前检查标题、条目、公式 interpretation、图注和 Provider 可见摘要，不得夹带基金/权限/非个人流程，或任何行情/交易判断。资料混有排除内容且无法分离，或图形自动输出不可控判断时，不提交，改用同次可核验个人事实文字/表格。不用虚构 Schema 参数过滤，不从 renderPlan/像素反推事实。

提交、成功或未知不补图，校验失败也不重试 Composer，直接已核验文字/表格完成。ready 不等于显示或办理成功，不等待截图。独立文件同样受范围与内容门约束。

核心入口走 [业务链接组件](../workbuddy-business-links/COMPONENT.md)，不嵌到 Dashboard 的 provider-action，不为入口检索知识。适用云开户放在所有正文、来源、其他入口之后。最终按安全模块逐项检查。
