# 表单对象、模板和字段发现

## Tool 路由

| 目的 | Tool |
| --- | --- |
| 当前用户可见对象 | `ycrm_form_deploy_list` |
| 对象模板 | `ycrm_form_template_list` |
| 快速了解基础字段 | `ycrm_form_simple_field_list` |
| 查询可读字段、字典、关联和约束 | `ycrm_form_field_list` |
| 新增允许字段 | `ycrm_form_add_field_list` |
| 更新允许字段 | `ycrm_form_upd_field_list` |
| 解释详情或核验子表 | `ycrm_form_detail_field_list` |

## 发现顺序

1. 需要发现或消歧对象时，调用无业务参数的 `ycrm_form_deploy_list`，结合[对象索引](forms/index.md)、用户上下文和返回的业务名称唯一确认对象。当前任务已有可信且唯一的对象结果时可复用；需要判断是否命中特有 Profile 时仍读取索引。索引以外对象按通用流程发现，不编造别名或标识。
2. 查询和详情不依赖模板；新增先确认模板。需要时调用 `ycrm_form_template_list`，使用支持的 `templateName` 缩小候选；仍有多个适用模板才请求选择，无匹配则停止新增。
3. 选择当前操作的字段 Tool。`simple_field_list` 不按字段权限过滤，不能作为可读或可写依据。
4. 主表场景对 `field_list`、`add_field_list`、`upd_field_list` 显式传 `needChildField=false`；确需子表才展开。`detail_field_list` 默认不展开，解释详情子表时传 `needChildField=true`。

复用与刷新统一按[共享规则](shared-rules.md)的证据表执行。

## 完整性与字段匹配

- `ycrm_form_deploy_list` 返回的 `nameField` 是对象主显示字段线索。按名称定位记录时可优先核对它；用于 `filterGroupList` 前仍须在当前可读字段结果中确认同一 `fieldName`、类型和可用比较方式。未返回或无法确认时按其他字段证据判断，不猜字段名。
- 以返回的 `fieldName`、`fieldTitle`、`fieldDomType`、`isRequired`、`multiValueField`、`dateFormat`、`dicDataList`、`referSelectItemList`、`referRule` 识别字段。标题、描述和类型共同确定唯一含义，不能猜字段名或把同名子表字段当主表字段。
- 字段类型、必填、字典、关联与关系 key 以当前场景元数据为准；可读字段不背书可写性。
- 元数据被截断时，用当前 Tool 支持的参数缩小范围后重查，例如只请求主表或在模板查询时按名称过滤。不能给字段 Tool 添加未声明的筛选参数。跨工具对照只帮助识别遗漏，仍须取得对应新增/更新字段证据才能写入。
- 无法取得完整所需证据时说明“未确认”；不能据残片断言字段不存在、不可写或对象不可见。完整可写清单未返回的字段不提交。
- 字典和关联使用当前返回允许的自然值，不将展示名称改成未返回的编码。普通多值自然值按契约用英文逗号分隔；图片、附件、子表等结构型字段按各自契约处理。
- 日期优先使用字段 `dateFormat`，其次使用 Tool 声明格式；均未提供且当前 Tool 已确认支持通用日期文本时才以 `yyyy-MM-dd HH:mm:ss` 兜底。不得覆盖明确格式。

涉及子表读取时读[子表读取规则](subform-read-rules.md)；仅在增删改子表行时读[子表写入规则](subform-write-rules.md)。
