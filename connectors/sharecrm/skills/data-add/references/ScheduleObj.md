# ScheduleObj

## `what_list_type` 赋值逻辑

当目标对象为 `ScheduleObj`，且需要填写或修改“关联业务模块”/`related_object`/`what_list` 类型字段时，不要写入 `related_object`，也不要使用 `{ObjectApiName: ["id"]}` 简写；必须同时写入 `related_object_data` 和 `related_api_names`。

- 先按主流程的关联对象字段规则解析每条关联记录，取得唯一的关联对象 `apiName`、记录 `id` 和记录 `name`。
- `related_object_data` 写数组；每个元素必须包含 `describe_api_name`、`id`、`name`。
- `related_api_names` 写数组；值来自 `related_object_data[].describe_api_name` 去重后的对象 apiName，保留首次出现顺序。
- 多条同对象记录可同时写入 `related_object_data`；`related_api_names` 中该对象 apiName 只保留一次。
- 新建记录时，任何关联记录未唯一确认前，不得构造、校验或保存这两个字段。
- 编辑记录时，若用户表达“追加/补充关联”，在原 `object_data.related_object_data` 基础上追加，并按 `describe_api_name + id` 去重后重算 `related_api_names`。
- 编辑记录时，若用户表达“改为/设为/替换关联”，用新解析出的关联记录替换原 `related_object_data`，并重算 `related_api_names`。
- 编辑记录时，任何关联记录未唯一确认前，不得构造、校验或保存这两个字段。

示例：

```json
{
  "related_object_data": [
    {
      "describe_api_name": "AccountObj",
      "id": "6a0697de42275d000745a6ba",
      "name": "抚州影视文化公司"
    },
    {
      "describe_api_name": "AccountObj",
      "id": "6a057a8844cdb1000740a08d",
      "name": "小鹏"
    }
  ],
  "related_api_names": [
    "AccountObj"
  ]
}
```
