# Mode D — DataX job.json

> **Terminology**: 数据源类型 = data source type | 连接信息 = connection info | 库表名 = database/table name | 查询条件 = query condition | reader 插件 = reader plugin | columnMapping = column-to-property mapping | push_url = TE receiver URL

## Ask User
1. Data source type (MySQL / Oracle / PostgreSQL / OSS / HDFS / Other)
2. Connection info / database & table names / query conditions (or file path)

## Deliverable
`.ae-cli/output/datax-job.json`:

```json
{
  "job": {
    "content": [{
      "reader": {
        "name": "<mysqlreader|oraclereader|...>",
        "parameter": { "connection": [ { "jdbcUrl": ["<TODO>"], "table": ["<TODO>"] } ], "username": "<TODO>", "password": "<TODO>", "column": ["*"] }
      },
      "writer": {
        "name": "tewriter",
        "parameter": {
          "push_url": "<SERVER_URL>",
          "appid": "<appId>",
          "eventName": "<from plan>",
          "columnMapping": { "<db_col>": "<te_prop>" }
        }
      }
    }],
    "setting": { "speed": { "channel": 2 } }
  }
}
```

`.ae-cli/output/datax-README.md`:
- Launch: `python datax.py datax-job.json`
- Prerequisite: DataX runtime environment
- `<TODO>` checklist

## Generation Steps
1. Determine the reader plugin name
2. Fill `eventName` + `columnMapping` using the first event from plan (or user-specified event)
3. Write both files
