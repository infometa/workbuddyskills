# wps.shapes.distribute

## 1. wps.shapes.distribute

#### 功能说明

设置在线文字文档形状的分布（distribute_cmd：0=水平/1=纵向；relative_to_page=true 页面等距，false 原占空间内分布；需读回 wps.shapes.info 断言等距，防假成功）。

**幂等性**：是 — safe

> group/align/distribute 需至少 2 个形状；shape_names 必须为当前顶层形状名（形状入组后原名失效）。
> code=0 不代表已等距：须读回 wps.shapes.info 断言两端到页面边界、中间间距相等（±0.75 磅）；relative_to_page=false 时间距可能不变（语义如此，非失败）。
> group/align/distribute 需至少 2 个形状；shape_names 必须是当前顶层形状名（来自 wps.shapes.list）；形状入组后其原名失效，须改用组名，否则报 500002 或静默无效。
> 分布生效口径：执行后用 wps.shapes.info 读回 left/top，两端形状落在页面两端、中间形状间距相等（±0.75 磅栅格偏差）即等距成功；组合（Group）对象参与分布时以组整体计。
> relative_to_page=false 是"在原占空间内分布"，间距可能保持不变，这是语义而非失败；要页面级等距须传 true。
> code=0 仅表示内核接受调用，必须读回位置断言等距，防止假成功。

#### 调用示例

文档设置：

```json
{
  "file_id": "<FILE_ID>",
  "distribute_cmd": 1,
  "relative_to_page": false,
  "shape_names": [
    "Straight Connector 4",
    "TextBox 5"
  ]
}
```

#### 参数说明

- `distribute_cmd` (number, 可选): 分布方向：0=水平分布 / 1=纵向分布（msoDistributeHorizontally/Vertically）
- `file_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 文件 id；与 url、link_id 三选一
- `link_id` (string, 三选一必填: `url` / `link_id` / `file_id`): 分享 id；与 url、file_id 三选一
- `relative_to_page` (boolean, 可选): true=均匀分布于页面整个横向/纵向空间（等距到页面边界）；false=仅在原占空间内分布（形状间距可能不变，并非失败）
- `shape_names` (array, 可选): shape names
- `url` (string, 三选一必填: `url` / `link_id` / `file_id`): 文档 URL；与 link_id、file_id 三选一

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `data` | object | 业务数据 |
| `message` | string | 结果说明 |
