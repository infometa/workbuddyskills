# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "site",
    "keyword"
  ],
  "properties": {
    "site": {
      "type": "string",
      "default": "US",
      "examples": [
        {
          "value": "US",
          "summary": "美国站"
        }
      ],
      "maxLength": 1000,
      "description": "亚马逊站点代码，当前仅支持 US"
    },
    "keyword": {
      "type": "string",
      "examples": [
        {
          "value": "iodized salt bulk",
          "summary": "碘盐批发"
        }
      ],
      "maxLength": 1000,
      "description": "要查询洞察报告的搜索关键词"
    }
  }
}
```

</details>

## 原始 Output Schema

<details>
<summary>展开查看完整 Output Schema</summary>

```json
{
  "type": "object",
  "required": [],
  "properties": {
    "msg": {
      "type": "string",
      "description": "提示信息或错误信息"
    },
    "code": {
      "type": "string",
      "description": "响应码"
    },
    "type": {
      "type": "string",
      "description": "响应类型"
    },
    "stdout": {
      "type": "string",
      "description": "综合商业洞察报告内容(Markdown格式)"
    },
    "costTime": {
      "type": "integer",
      "description": "总处理耗时（毫秒）"
    },
    "costToken": {
      "type": "integer",
      "description": "token消耗量"
    }
  }
}
```

</details>
