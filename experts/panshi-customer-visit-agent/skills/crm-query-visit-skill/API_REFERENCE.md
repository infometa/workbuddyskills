# API 接口参考（API_REFERENCE）

> 本文件包含查询跟进记录 Skill 所需的接口参数规范、角色鉴权逻辑。
> 所有接口均通过 MCP Server `omp-service`（地址：`https://omp-service.mcp.it.woa.com`）的 `request_api` 工具转发调用。

## MCP 服务映射

> ⛔ **统一调用方式**：所有接口均通过 `omp-service` 的 `request_api` 工具转发调用。下表「MCP Tool」统一为 `request_api`，原接口名作为 `request_api` 的 `apiPath` 参数传入（不是 toolName）。

| 接口 | MCP Server | MCP Tool | 接口路径（apiPath） |
|------|-----------|----------|--------------------|
| GetCustomerListForVisitForMcp | `omp-service` | `request_api` | `csm/GetCustomerListForVisitForMcp` |
| GetVisitListForMcp | `omp-service` | `request_api` | `csm/GetVisitListForMcp` |
| list（商机搜索） | `omp-service` | `request_api` | `ltc.project/list` |
| get_lead_list（线索搜索） | `omp-service` | `request_api` | `opportunity_node/get_lead_list` |

**统一调用模板：**

```
use_mcp_tool(
  serverName="omp-service",
  toolName="request_api",
  arguments={
    "apiPath": "<上表接口路径>",
    "data": { ...业务参数（即下方各接口的 JSON 请求体）... }
  }
)
```

## 目录

- [客户搜索接口](#客户搜索接口)
- [商机搜索接口](#商机搜索接口)
- [线索搜索接口](#线索搜索接口)
- [跟进记录查询接口](#跟进记录查询接口)

---

## 客户搜索接口

### GetCustomerListForVisitForMcp（通过 `omp-service` 的 `request_api` 转发调用，apiPath=`csm/GetCustomerListForVisitForMcp`）

以下 JSON 作为 `data` 业务参数传入：

```json
{
  "type": [1],
  "customer_name": "模糊搜索关键词",
  "page": 1,
  "page_size": 100,
  "sales_mode": "all",
  "select_type": "only_mine",
  "get_all_area_data": 1
}
```

> `type` 字段为数组：`[1]` 表示「我相关」，`[2]` 表示「长尾客户」。
> `select_type`：`only_mine` 表示我相关，`all` 表示长尾客户。

**搜索策略：**
1. 先用 `select_type=only_mine` 搜索
2. 返回0个 → 改用 `select_type=all` 再搜索一次
3. 仍为0个 → 提示「未找到您名下的「{客户名}」，请确认客户归属」，cid 置空继续查询
4. 返回多个 → 列出候选让用户选择

> ⚠️ **严禁调用 GetAssociationCustomerList**，该接口无权限过滤。

---

## 商机搜索接口

**调用方式：** 通过 `omp-service` 的 `request_api` 转发调用（apiPath=`ltc.project/list`）

**请求参数（以下 JSON 作为 `data` 业务参数传入）：**
```json
{
  "page": 1,
  "size": 100,
  "type": 12,
  "switchPanshiBase": 1,
  "projectArea": [0, 1],
  "name": "商机名称关键词"
}
```

> ⚠️ `projectArea: [0, 1]` 仅国内版传，海外版不传此字段。
> ⚠️ 必须从用户输入提取关键词传入 `name` 参数，禁止不传 `name` 搜索全量列表。

**返回字段：** `list[].code`（商机编码，即 `project_code`）、`list[].name`（商机名称，即 `project_name`）

**搜索策略：**
- 返回0个 → 提示「未找到名下商机「{商机名}」，请确认商机归属或换个关键词重试」
- 返回1个 → 向用户确认：「找到商机「{name}」（编码：{code}），是否以此查询跟进记录？」，确认后选中
- 返回多个（≥2）→ 列出全部候选让用户选择，**禁止自动选中**
- 选中后：传入 `project_codes: [project_code]`，并传 `from_type: [2]`

---

## 线索搜索接口

**调用方式：** 通过 `omp-service` 的 `request_api` 转发调用（apiPath=`opportunity_node/get_lead_list`）


### 第一步：搜索客户

```json
{
  "headers": { "x-staffname": "用户RTX" },
  "page": 1,
  "page_size": 50,
  "only_follow": 2,
  "company": "客户名关键词（可选）"
}
```

**返回字段：** `list[].cid`（客户CID）、`list[].customer`（客户名称）
→ 展示客户列表，让用户选择目标客户

### 第二步：搜索线索

用户选定客户后，传入 `cid` 查询该客户下的线索：

```json
{
  "headers": { "x-staffname": "用户RTX" },
  "page": 1,
  "page_size": 100,
  "only_follow": 2,
  "cid": "用户选定的客户CID"
}
```

**返回字段：** `list[].id`（线索ID）、`list[].company`（公司名）、`list[].follow`（线索销售）
- 选中后：传入 `lead_ids: [lead_id]`，并传 `from_type: [12]`

---

## 跟进记录查询接口

**调用方式：** 通过 `omp-service` 的 `request_api` 转发调用（apiPath=`csm/GetVisitListForMcp`）

### 必传参数（OA 鉴权）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| switch_panshi_base | number | ✱ | 固定传 `1`，OA鉴权标识 |
| tab_type | number | ✱ | 固定传 `3` |
| source_list | array | ✱ |source_list固定= `[1,2,3,4,5,6,7,9,10,11]`。任何查询都应带上此参数，不得省略|

### 完整请求参数

> 以下表格包含全部参数；其中 `switch_panshi_base`、`tab_type`、`source_list` 为必传（见上方必传参数表），其余为选填。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| switch_panshi_base | number | ✱ | 固定传 `1`，OA鉴权标识 |
| tab_type | number | ✱ | 数据范围：`1`=我创建的，`2`=我协同的，`3`=我创建+我协同，`4`=全部；固定传 `3` |
| source_list | array | ✱ | 固定= `[1,2,3,4,5,6,7,9,10,11]`，任何查询都应带上此参数，不得省略 |
| page | integer | — | 页码，从 1 开始，默认 1 |
| page_size | integer | — | 每页条数，范围 [1, 2000]，默认 20 |
| visit_id | integer | — | 单条跟进记录ID，精确查询单条时使用 |
| from_type | integer[] | — | 跟进对象类型：`1`=客户，`2`=项目/商机，`10`=产研商机，`11`=私有云POC，`12`=线索，`13`=分包经理 |
| type | integer[] | — | 跟进方式：`10000`=线下拜访，`10001`=线上沟通，`10002`=跟进进展 |
| cid | string | — | 客户CID，精确过滤 |
| customer_name | string | — | 客户名称模糊搜索 |
| project_codes | string[] | — | 商机编码列表，最多100个 |
| project_name | string | — | 商机名称模糊搜索 |
| lead_ids | number[] | — | 线索ID列表，最多100个 |
| product_opp_ids | string[] | — | 产研商机ID列表，最多100个 |
| product_opp_name | string | — | 产研商机名称搜索 |
| private_poc_ids | string[] | — | 私有云POC ID列表，最多100个 |
| private_poc_name | string | — | 私有云POC名称搜索 |
| pnids | string[] | — | 合作伙伴ID列表，最多100个 |
| creator | string | — | 创建人RTX（精确匹配） |
| search_rtx | string | — | 跟进人或创建人（二合一模糊搜索） |
| keyword | string | — | 内容模糊搜索（跟进内容/下一步计划/项目进展） |
| visit_time_start | string | — | 拜访时间起，格式：`YYYY-MM-DD HH:mm:ss` |
| visit_time_end | string | — | 拜访时间止，格式：`YYYY-MM-DD HH:mm:ss` |
| create_time_start | string | — | 创建时间起，格式：`YYYY-MM-DD HH:mm:ss` |
| create_time_end | string | — | 创建时间止，格式：`YYYY-MM-DD HH:mm:ss` |
| sort | string | — | 排序字段，目前仅支持 `update_time` |
| sort_type | string | — | 排序方向：`ASC`=升序，`DESC`=降序 |
| source | integer | — | 来源：`2`=磐石，`4`=小O智能跟进，`9`=用户输入会议code，`11`=AI助手 |


> ⚠️ `tab_type=3` 为常规查询默认值（我创建+我协同）；`switch_panshi_base=1` 启用磐石鉴权，正常查询时必须传入。
> 
>⚠️ `source_list` 为来源白名单过滤，source_list固定= `[1,2,3,4,5,6,7,9,10,11]`。任何查询都应带上此参数，不得省略。

**请求示例：**
```json
{
  "switch_panshi_base": 1,
  "tab_type": 3,
  "page": 1,
  "page_size": 10,
  "cid": "C123456",
  "type": [10000],
  "visit_time_start": "2026-04-01 00:00:00",
  "visit_time_end": "2026-04-13 23:59:59"
}
```

### 响应

**成功：**
```json
{
  "total": 100,
  "list": [
    {
      "base_info_visit_id": 12345,
      "customer_name": "腾讯科技（深圳）有限公司",
      "cid": "C123456",
      "from_type": 1,
      "type": 10000,
      "visit_time": "2026-04-10 14:30:00",
      "create_time": "2026-04-10 14:35:00",
      "update_time": "2026-04-10 14:35:00",
      "conclusion": "沟通内容摘要...",
      "plan": "下一步计划...",
      "current_progress": "项目进展...",
      "login_name": "jacklian",
      "source": 11
    }
  ]
}
```

**失败：**
```json
{
  "code": 400,
  "message": "错误原因"
}
```

### 返回字段说明

| 字段 | 必选(是/否) | 类型 | 描述 |
| list | 否 | object[] | 跟进记录列表 |
| list[i].ft | 否 | string | 创建人所属中心 |
| list[i].id | 否 | number | 跟进记录自增ID（customer_visit.id） |
| list[i].cid | 否 | string | 客户CID |
| list[i].pid | 否 | string | 项目ID（逐步废弃，建议使用project_code） |
| list[i].uin | 否 | string | UIN |
| list[i].pnid | 否 | string | 合作伙伴ID |
| list[i].q_id | 否 | string | 架构师潜在机会ID |
| list[i].type | 否 | number | 业务类型：1=现场拜访，2=电话微信，3=架构师拜访纪要，4=行业五部拜访纪要，5=行业五部风险问题及重要信息，6=跟进记录，7=架构师项目进展，10000=线下拜访，10001=线上沟通，10002=跟进记录，10003=其他 |
| list[i].source | 否 | number | 来源系统：1=销售易，2=磐石，3=合作伙伴，4=小O智能跟进，5=CEM，6=小程序人工填写，7=线索，8=商业授权，9=用户输入会议code，10=会议结束后自动生成 |
| list[i].creator | 否 | string | 创建人RTX |
| list[i].visitor | 否 | string | 拜访人RTX |
| list[i].location | 否 | string | 拜访位置 |
| list[i].visit_id | 否 | number | 外部系统跟进记录ID（如销售易自定义ID） |
| list[i].clientUin | 否 | string | 代客UIN |
| list[i].from_type | 否 | number | 拜访来源类型：0=其他，1=客户，2=项目，3=渠道经理-合作伙伴，4=合作伙伴-立项，5=合作伙伴-客户，6=渠道续费，7=渠道-伙伴打卡，8=渠道-商情跟进，9=潜在机会，10=产研商机，11=私有云POC，12=线索，13=分包经理 |
| list[i].goal_info | 否 | string[] | 拜访目标信息列表 |
| list[i].conclusion | 否 | string | 拜访结论/会议纪要 |
| list[i].group_name | 否 | string | 创建人所属组名称 |
| list[i].visit_time | 否 | string | 拜访时间，格式：Y-m-d H:i:s |
| list[i].visit_type | 否 | string | 拜访类型：partner=合作伙伴，customer=客户 |
| list[i].create_time | 否 | string | 记录创建时间，格式：Y-m-d H:i:s |
| list[i].product_tag | 否 | string | 产品标签 |
| list[i].update_time | 否 | string | 记录最后更新时间，格式：Y-m-d H:i:s |
| list[i].contact_info | 否 | string[] | 联系人信息列表 |
| list[i].project_code | 否 | string | 项目编码 |
| list[i].summary_type | 否 | string | 纪要类型 |
| list[i].time_section | 否 | string | 拜访时间段：morning=早上，noon=中午，afternoon=下午，night=晚上 |
| list[i].bus_result_id | 否 | string | 商情ID |
| list[i].business_info | 否 | object[] | 商情信息列表 |
| list[i].business_info[i].id | 否 | number | 商情信息自增ID |
| list[i].business_info[i].plan | 否 | string | 目前进展及下一步计划 |
| list[i].business_info[i].amount | 否 | string | 商机总金额预估 |
| list[i].business_info[i].income | 否 | string | 应收影响预估 |
| list[i].business_info[i].numbers | 否 | number | 商机数量 |
| list[i].business_info[i].visit_id | 否 | number | 关联的跟进记录ID |
| list[i].business_info[i].main_risk | 否 | string | 项目主要风险点 |
| list[i].business_info[i].pain_problem | 否 | string | 痛点问题 |
| list[i].business_info[i].bevisited_role | 否 | string | 被拜访人角色 |
| list[i].business_info[i].meeting_address | 否 | string | 会议地址 |
| list[i].business_info[i].current_progress | 否 | string | 项目当前进展 |
| list[i].business_info[i].cooperate_progress | 否 | string | 合作进展 |
| list[i].business_info[i].product_difficult_point | 否 | string | 产品卡点 |
| list[i].collaborators | 否 | object[] | 协同跟进人列表 |
| list[i].collaborators[i].rtx | 否 | string | 协同人RTX账号 |
| list[i].collaborators[i].rtx_role | 否 | string | 协同人角色 |
| list[i].channel_manager | 否 | string | 渠道经理RTX |
| list[i].department_name | 否 | string | 创建人所属部门名称 |
| list[i].tx_participants | 否 | string | 腾讯参与人 |
| list[i].visit_check_ins_id | 否 | number | 关联签到记录ID，对应 customer_visit_check_ins.id |
| list[i].customer_participants | 否 | string | 客户参与人 |
| list[i].visit_check_ins_detail | 否 | object | 关联签到记录详情 |
| list[i].visit_check_ins_detail.id | 否 | number | 签到记录自增ID |
| list[i].visit_check_ins_detail.list | 否 | object[] | 签到附件列表 |
| list[i].visit_check_ins_detail.list[i].url | 否 | string | 附件URL |
| list[i].visit_check_ins_detail.list[i].name | 否 | string | 附件文件名 |
| list[i].visit_check_ins_detail.address | 否 | string | 签到详细地址 |
| list[i].visit_check_ins_detail.creator | 否 | string | 签到人RTX |
| list[i].visit_check_ins_detail.latitude | 否 | number | 签到纬度坐标 |
| list[i].visit_check_ins_detail.longitude | 否 | number | 签到经度坐标 |
| list[i].visit_check_ins_detail.create_time | 否 | string | 签到创建时间，格式：Y-m-d H:i:s |
| list[i].visit_check_ins_detail.update_time | 否 | string | 签到更新时间，格式：Y-m-d H:i:s |
| total | 否 | number | 符合条件的总记录数 |