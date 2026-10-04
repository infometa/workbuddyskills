---
name: wscn-mcp
description: 华尔街见闻资讯相关产品工具说明
version: "1.0.0"
author: "华尔街见闻"
---

# 华尔街见闻 MCP使用说明

本 Skill 用于通过华尔街见闻mcp服务查询大涨股异动和见闻全球资讯。所有工具都是只读查询，不会修改用户数据。

## 可用工具

### get_large_stocks - 获取大涨股票信息

查询指定日期的大涨股票、关联板块和异动原因。未指定日期时查询当天数据。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | - | 查询日期，格式 `YYYY-MM-DD`；不填表示当天 |

**返回结构**：

```json
{
  "plates": [
    {
      "date": 20260820,
      "plate_id": 1,
      "plate_name": "板块名称",
      "plate_desc": "板块异动说明",
      "stocks": [
        {
          "stock_name": "个股名称",
          "stock_code": "股票代码",
          "stock_desc": "个股大涨异动原因"
        }
      ]
    }
  ]
}
```

返回结果重点是个股、关联板块和异动描述，不包含个股价格、涨跌幅、流通市值、板数、涨停时间等字段。

### get_wscn_global_articles - 获取全球资讯列表

查询指定日期的华尔街见闻全球资讯列表。未指定日期时查询当天数据。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | - | 查询日期，格式 `YYYY-MM-DD`；不填表示当天 |

**返回结构**：

```json
{
  "articles": [
    {
      "date": "2026-08-20",
      "id": 123,
      "title": "文章标题",
      "summary": "文章摘要",
      "displayTime": 1780000000,
      "updatedAt": 1780000000
    }
  ]
}
```

列表工具不返回文章正文。需要正文时，先从列表中取得文章的 `date` 和 `id`，再调用详情工具。

### get_wscn_global_article_detail - 获取文章详情

根据日期和文章 ID 获取单篇资讯正文。

**参数说明**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| date | string | ✅ | 文章所属日期，格式 `YYYY-MM-DD` |
| id | integer | ✅ | 从资讯列表中获得的文章 ID |

调用流程：

1. 调用 `get_wscn_global_articles` 获取指定日期的文章列表。
2. 从列表中选择文章的 `date` 和 `id`。
3. 调用 `get_wscn_global_article_detail` 获取正文详情。

## 使用限制和注意事项

- 三个工具只能查询最近两个月的数据。
- 日期使用北京时间；不传 `date` 时默认查询当天。
- 需要使用有效的 MCP API Key；支持 `Authorization: Bearer <api-key>`。
- 如果 Token/API Key 过期或无效，应提示用户重新获取有效 Key。
