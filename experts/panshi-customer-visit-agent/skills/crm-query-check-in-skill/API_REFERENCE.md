# API 接口参考（API_REFERENCE）

> 本文件包含签到打卡记录查询 Skill 所需的接口参数规范、角色鉴权逻辑。
> 所有接口均通过 MCP Server `omp-service`（地址：`https://omp-service.mcp.it.woa.com`）的 `request_api` 工具转发调用。

## MCP 服务映射

> ⛔ **统一调用方式**：所有接口均通过 `omp-service` 的 `request_api` 工具转发调用。下表「MCP Tool」统一为 `request_api`，原接口名作为 `request_api` 的 `apiPath` 参数传入（不是 toolName）。

| 接口 | MCP Server | MCP Tool | 接口路径（apiPath） |
|------|-----------|----------|--------------------|
| GetCustomerListForVisitForMcp | `omp-service` | `request_api` | `csm/GetCustomerListForVisitForMcp` |
| GetVisitCheckInsListForMcp | `omp-service` | `request_api` | `csm/GetVisitCheckInsListForMcp` |

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
- [签到记录查询接口](#签到记录查询接口)

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

> `select_type`：`only_mine` 表示我相关，`all` 表示长尾客户。

**搜索策略：**
1. 先用 `select_type=only_mine` 搜索
2. 返回0个 → 改用 `select_type=all` 再搜索一次
3. 仍为0个 → 提示「未找到您名下的「{客户名}」，请确认客户归属」，cid 置空继续查询
4. 返回多个 → 列出候选让用户选择

> ⚠️ **严禁调用 GetAssociationCustomerList**，该接口无权限过滤。

---

## 签到记录查询接口

**调用方式：** 通过 `omp-service` 的 `request_api` 转发调用（apiPath=`csm/GetVisitCheckInsListForMcp`）

> 签到记录列表接口（小程序）

### 必传参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | ✱ | 查询类型：`1`=近15天未被关联的签到记录，`2`=我的全部签到记录 |

### 完整请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | ✱ | `1`=近期15天且未被关联的数据；`2`=我的签到记录（含所有数据） |
| id | int | — | 按ID查询单条详情 |
| page | int | — | 页码，默认 1 |
| page_size | int | — | 每页条数，默认 10 |
| address | string | — | 地址关键词 |
| creator | string | — | 创建人RTX |
| create_time_start | string | — | 开始时间，格式 `YYYY-MM-DD HH:mm:ss` |
| create_time_end | string | — | 结束时间，格式 `YYYY-MM-DD HH:mm:ss` |
| customer_name | string | — | 客户名称关键词 |
| keyword | string | — | 模糊搜索（同时匹配客户名称和地址），传了则不传 `address`/`customer_name` |
| cid | string | — | 客户CID，精确过滤 |
| source | int | — | 传 `id` 时必填：来源类型，`1`=列表点击查详情，`2`=分享 |
| sort | string | — | 排序字段，默认 id 倒序，支持 `update_time` |
| sort_type | string | — | 升降序：`asc` 或 `desc` |

**请求示例：**
```json
{
  "type": 2,
  "page": 1,
  "page_size": 10,
  "create_time_start": "2026-04-01 00:00:00",
  "create_time_end": "2026-04-13 23:59:59"
}
```

### 响应

**成功：**
```json
{
  "list": [
    {
      "id": 3,
      "longitude": 108.887646,
      "latitude": 34.214495,
      "address": "雁塔区新长安广场2期(沣惠南路西)",
      "attachment": [
        {
          "url": "https://panshi-file-1258344699.cos.accelerate.myqcloud.com/followRecord/20255/tmp_xxx.png",
          "name": "tmp_xxx.png"
        }
      ],
      "creator": "jack",
      "cid": "C123456",
      "customer_name": "测试客户",
      "create_time": "2025-05-22 19:40:04",
      "update_time": "2025-05-22 19:40:04",
      "is_bind_visit": 1,
      "base_info_visit_id": 772
    }
  ],
  "total": 1
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

| 字段 | 说明 |
|------|------|
| total | 符合条件的总记录数 |
| list | 当前页记录列表 |
| id | 签到记录唯一ID |
| longitude | 经度 |
| latitude | 纬度 |
| address | 签到详细地址 |
| attachment | 现场照片列表，每项含 `url`（图片地址）和 `name`（文件名） |
| creator | 创建人RTX |
| cid | 关联客户CID |
| customer_name | 关联客户名称 |
| create_time | 签到时间 |
| update_time | 最后更新时间 |
| is_bind_visit | 是否已绑定跟进记录：`1`=已绑定，`0`=未绑定 |
| base_info_visit_id | 已绑定的跟进记录ID（`is_bind_visit=1` 时有值） |

### type 说明

| type 值 | 含义 | 使用场景 |
|---------|------|---------|
| 1 | 近期15天且未被关联的签到记录 | 创建跟进记录时选择关联的签到 |
| 2 | 我的全部签到记录（含已关联） | 查看历史所有签到 |
