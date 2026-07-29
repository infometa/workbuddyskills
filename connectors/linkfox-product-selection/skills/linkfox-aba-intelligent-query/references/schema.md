# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "analysisDescription"
  ],
  "properties": {
    "uid": {
      "type": "string",
      "maxLength": 1000,
      "description": "用户ID"
    },
    "chatId": {
      "type": "string",
      "maxLength": 1000,
      "description": "对话ID"
    },
    "region": {
      "type": "string",
      "default": "US",
      "pattern": "DE|BR|US|CA|AU|JP|AE|ES|FR|IT|SA|TR|MX|SE|NL",
      "examples": [
        {
          "value": "DE",
          "summary": "亚马逊-德国站"
        },
        {
          "value": "BR",
          "summary": "亚马逊-巴西站"
        },
        {
          "value": "US",
          "summary": "亚马逊-美国站"
        },
        {
          "value": "CA",
          "summary": "亚马逊-加拿大站"
        },
        {
          "value": "AU",
          "summary": "亚马逊-澳大利亚站"
        },
        {
          "value": "JP",
          "summary": "亚马逊-日本站"
        },
        {
          "value": "AE",
          "summary": "亚马逊-阿联酋站"
        },
        {
          "value": "ES",
          "summary": "亚马逊-西班牙站"
        },
        {
          "value": "FR",
          "summary": "亚马逊-法国站"
        },
        {
          "value": "IT",
          "summary": "亚马逊-意大利站"
        },
        {
          "value": "SA",
          "summary": "亚马逊-沙特站"
        },
        {
          "value": "TR",
          "summary": "亚马逊-土耳其站"
        },
        {
          "value": "MX",
          "summary": "亚马逊-墨西哥站"
        },
        {
          "value": "SE",
          "summary": "亚马逊-瑞典站"
        },
        {
          "value": "NL",
          "summary": "亚马逊-荷兰站"
        }
      ],
      "description": "亚马逊市场（站点）"
    },
    "stepId": {
      "type": "string",
      "maxLength": 1000,
      "description": "调用顺序"
    },
    "memberId": {
      "type": "string",
      "maxLength": 1000,
      "description": "成员ID"
    },
    "messageId": {
      "type": "string",
      "maxLength": 1000,
      "description": "消息ID"
    },
    "createDownloadUrl": {
      "type": "boolean",
      "default": false,
      "examples": [
        {
          "value": "true",
          "summary": "生成下载链接，可下载全量的查询结果（但不超过10000条）。"
        },
        {
          "value": "false",
          "summary": "不生成下载链接。"
        }
      ],
      "description": "是否生成下载链接。当用户要求下载、导出、或生成下载链接时，设置为true。"
    },
    "analysisDescription": {
      "type": "string",
      "examples": [
        {
          "value": "筛选美国站，关键词“gift”在过去12周的搜索热度排名。",
          "summary": "搜索词的热度排名趋势分析"
        },
        {
          "value": "筛选美国站，关键词包含“gift”，2025年Q1和全年的平均搜索排名都大于50万，但最新排名冲进5万-10万的搜索词。",
          "summary": "潜力爆款挖掘/黑马词挖掘"
        },
        {
          "value": "筛选美国站，最新排名在20万以内，且4周前的排名比8周前提升30%，本周的排名比4周前提升30%的搜索词。",
          "summary": "持续增长趋势挖掘"
        },
        {
          "value": "筛选美国站，筛选当前搜索排名在20000以内，近三个月点击占比Top 1的Asin的转化率占比低于5%的搜索词。相同搜索词相同Asin值保留最新的一个。",
          "summary": "市场机会挖掘/高搜索量低垄断"
        },
        {
          "value": "筛选美国站，包含“cup”的关键词中，去年（2024年）1-9月份排名未进入50万，10-11月份连续进入20万的词。",
          "summary": "节日/季节性礼物词定位"
        },
        {
          "value": "筛选筛选美国站关键词包含“hat”的，最新搜索排名在5万-20万之间，且近3个月来点击占比大于20%，转化占比小于10%的ASIN。相同搜索词和ASIN仅保留点击占比和转化占比的比例最小数据。",
          "summary": "高点击低转化ASIN挖掘"
        },
        {
          "value": "筛选美国站，关键词包含“charger”的，当前排名在20万开外的，近2个月的平均转化占比大于平均转化占比1.5倍的关键词，以及相应的ASIN。",
          "summary": "高ROAS长尾蓝海词库构建"
        },
        {
          "value": "找到美国站“charger”的长尾词中，近一个月才进入排名榜单，且当前排名在50万以内的所有词。",
          "summary": "市场新词与新需求侦测"
        },
        {
          "value": "筛选美国站中“table”的长尾词中，排名在10万-30万之间，且近4周的搜索排名增长50%以上的搜索词。",
          "summary": "捕捉细分趋势/变体增长"
        }
      ],
      "maxLength": 1000,
      "description": "需要查询或分析的具体内容。应客观反映用户意图，不能曲解用户需求。"
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
      "description": "消息"
    },
    "code": {
      "type": "string",
      "description": "返回码"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "title": {
      "type": "string",
      "description": "标题"
    },
    "total": {
      "type": "integer",
      "description": "结果总数"
    },
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "data": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "查询结果数据列表"
          },
          "name": {
            "type": "string",
            "description": "sheet的名称"
          },
          "columns": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "渲染的列"
          },
          "userExplanation": {
            "type": "string",
            "description": "用户的分析意图"
          },
          "analysisStatement": {
            "type": "string",
            "description": "LLM生成的SLS分析语句"
          }
        }
      },
      "description": "查询结果数据列表数组"
    },
    "success": {
      "type": "boolean",
      "description": "本次数据挖掘是否最终成功执行"
    },
    "costTime": {
      "type": "integer",
      "description": "耗时"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    },
    "downloadUrl": {
      "type": "string",
      "description": "CSV 文件下载 URL，当 createDownloadUrl 为 true 时返回"
    },
    "downloadNote": {
      "type": "string",
      "description": "文件下载提示。提醒用户下载文件，或通过下载文件查看完整数据。"
    }
  }
}
```

</details>
