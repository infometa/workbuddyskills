# 东方证券期货业务知识 MCP 接口参考

本 Skill 只使用 `orientfutures_mobile_knowledge_base` 的三个原子检索工具、一个查询级可视化组合工具和独立业务链接展示工具。运行时 Schema 和真实返回是最终依据。

`knowledge_visual_compose` 新入口只传 `dashboard_spec`，字段见 [公共渲染契约](../workbuddy-visual-rendering/references--dashboard-spec.md)。原子结果提供 `presentation.evidenceRef`、`evidenceExpiresAt`、`evidenceBindings` 和可选 `evidenceCharts`；只能用本轮返回的引用与 key，不读共享文件。核心入口独立调用 `business_links_show`，不引用知识行动卡。process 只组织本轮审核步骤，不代表用户进度；没有有效图块时返回 not_applicable，不补取数。

## `knowledge_base_list_books`

- 入参：空对象 `{}`。
- 用途：发现当前知识集合及其内部键和记录数。
- 本 Skill 从真实返回中匹配 `orient-futures-business-guide` / “东证期货业务知识库”，不得假设它始终存在。

## `knowledge_base_get_book_toc`

- 必填 `book_key`：来自发现工具。
- 可选 `root`：目录实际返回的记录键。
- 可选 `depth`：1～6。
- 读取 `sections[]` 中的 `key`、`title`、`selfSizeBytes`、`subtreeSizeBytes` 和 `childCount` 来选择最窄记录。
- `presentation.status` 固定为 `not_applicable`，目录仅用于检索，不生成可视化片段。

目录可能包含期货开户与账户管理、银期签约与资金管理、期货交易规则与费用、特殊品种权限、基金等知识域；可发现不等于可使用。本 Skill 只检索前三类中允许个人普通业务的最窄正文，基金、资管、特殊权限与全部非个人业务在任何检索前按范围门结束。目录以本轮返回为准。

## `knowledge_base_get_section_content`

- 必填 `book_key`、`section`；`section` 必须是目录返回的完整字符串 `key`，必须保留前导零和 `/`。
- `view`：`self` 或 `subtree`，默认 `subtree`；仅在通过范围门的个人业务记录上按需要使用 `self`，不得为整篇方便加载排除知识域。
- `max_bytes`：1000～200000，默认 50000。
- `oversized=true` 时正文被主动省略，应根据 `children` 下钻或改用 `self`，不能解释为没有知识。

## 来源与失败语义

- 原子知识查询与知识图解成功返回包含 `provenance`，内部保留记录键和标题路径。
- 对客户只需自然说明内容来自东方证券期货业务知识，不展示内部书目数量、书名、记录键、接口名或检索过程。
- 工具未注册或连接失败表示知识服务不可用；列表为空表示当前条件未返回记录；正文为空不得用模型记忆补齐。
- 只读调用可按相同参数重试一次，再失败则停止对应分支。

## `business_links_show`

独立业务链接工具，HTTP MCP Apps 在内容流直接展示固定入口。必填 `action_ids`（当前工具 Schema 中的合法 ID，非空且不重复）；可选 `catalog_version`，省略使用当前版本。拒绝额外参数，不接受 URL、文案、HTML 或 evidenceRef。

返回 `protocol_version`、`catalog_version`、`delivery_id`、`action_ids`、`state=prepared`；固定展示数据通过工具结果 `_meta.business_links` 交给 `ui://of/business-links/v1`，模型不读取或复制该 UI 数据。不调用知识后端、不读取官网、不执行业务；prepared 不证明可见或已打开。失败/未知处理与场景位置见业务链接 Component。

## 范围优先

本文件仅说明生产接口，不授予基金、资管、特殊权限或非个人主体业务回答权。先执行 [范围门](../modules/safety-and-fallback.md)；纯排除回复零工具、零图表、零链接、零来源。业务链接 ID 可被 Schema 接受不代表本题适用。
