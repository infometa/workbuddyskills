# 办事入口 - 菜单命令参考

## menuSearch menuSearch — 搜索菜单

```bash
beisen-cli staffservice employeeWork menuSearch --data '{"query":"<用户问题>","minScore":0.3}'
```

### 参数（通过 --data 传入 JSON）

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `query` | string | 是 | 用户原始问题，用于匹配菜单ID、菜单名称和菜单描述（可参考同义词表改写，提升命中率） |
| `minScore` | number | 是 | 最低匹配分数，取值范围 0 到 1，仅返回匹配分数严格大于该值的菜单。**固定传 `0.3`** |

### 同义词参考

仅作检索改写的辅助手段，不承担路由职责；未列入的表达直接用原文检索：

| 用户表达 | 改写为 |
|---------|--------|
| "打卡" / "签到" | "考勤" |
| "工资" / "薪水" | "薪资" |
| "请假" / "休假" | "假期"（仅非请假操作意图场景） |
| "打开日程菜单" | "日程" |

### 返回结构

```json
{
  "code": "200",
  "message": "",
  "data": {
    "itemsCount": 3,
    "items": [
      {
        "menuId": "菜单ID",
        "menuName": "菜单名称",
        "menuDescription": "菜单描述"
      }
    ]
  }
}
```

- `code` 为状态码（`"200"` 表示成功）；`message` 为失败原因；`data` 为菜单结果
- `itemsCount` 为有效菜单数量；`items` 为菜单集合，按匹配分数降序排列
- 实际字段名以 CLI 返回为准

### 字段说明

| 字段 | 说明 |
|------|------|
| `itemsCount` | 有效菜单数量（整数） |
| `items` | 菜单集合（数组） |
| `items[].menuId` | 菜单唯一标识 |
| `items[].menuName` | 菜单名称 |
| `items[].menuDescription` | 菜单描述 |

### 菜单唤起按钮输出

匹配到菜单后，按 [../../beisen-data-query/SKILL.md](../../beisen-data-query/SKILL.md) 步骤六的规范输出可点击按钮：

````markdown
```senclaw-ui-json name=@senclaw-cmp/menu-group-button
{"menus": [{"menuId": "<id1>"}, {"menuId": "<id2>"}]}
```
````

### 判断逻辑

- `code == "200"` 且 `itemsCount > 0` → 进入步骤二判断意图是否命中
- `code == "200"` 但 `itemsCount == 0` 或 `items` 为空 → 按入场方式处理无命中分支
- `code != "200"` → 业务失败，原因在 `message`，按步骤四异常处理

### 注意事项

- `menuId` 必须从 CLI 返回中提取，严禁编造
- `minScore` 固定传 `0.3`，不需要根据场景调整
- `query` 传用户原始问题，可参考同义词表改写以提升命中率
- 代码块格式必须严格一致，否则前端无法渲染
- 菜单项根据当前用户角色（员工 / 管理者）不同而有差异，返回结果均已由后端完成权限过滤
