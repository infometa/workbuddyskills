# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "prompts"
  ],
  "properties": {
    "url": {
      "type": "string",
      "examples": [
        {
          "value": "https://www.amazon.com/",
          "summary": "亚马逊首页上下文"
        }
      ],
      "maxLength": 1000,
      "description": "联动页面 URL.用于补充 Alexa 当前答复的页面上下文"
    },
    "format": {
      "type": "string",
      "default": "markdown",
      "examples": [
        {
          "value": "markdown",
          "summary": "Markdown 展示"
        },
        {
          "value": "json",
          "summary": "JSON列表"
        }
      ],
      "maxLength": 1000,
      "description": "响应格式.可选 markdown 或 json；默认 markdown。"
    },
    "prompts": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": ""
      },
      "examples": [
        {
          "value": "[\"best wireless earbuds for running\"]",
          "summary": "单轮问题"
        },
        {
          "value": "[\"best electric kettle\",\"Compare with similar products\"]",
          "summary": "两轮对话"
        }
      ],
      "maxItems": 1000,
      "description": "对话提示词数组.用于发起一次 Alexa 多轮问答，至少 1 条，建议不超过 5 条。多个元素表示同一次调用中的连续追问，会按数组顺序依次发送：先发送 prompts[0]，等待 Alexa 回答后再发送 prompts[1]，再继续发送后续问题。若需要基于上一次工具调用结果继续追问，下一次调用是新的问答上下文，agent 需要根据历史回答和推荐商品自行总结上下文，并组织成新的 prompts 再发起调用。"
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
      "description": "返回消息.成功为 ok"
    },
    "code": {
      "type": "string",
      "description": "返回码.成功为 \"200\""
    },
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "prompt": {
            "type": "string",
            "description": "用户提示词.对应的问题或者追问"
          },
          "content": {
            "type": "string",
            "description": "Alexa回答内容"
          },
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "items": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": [],
                    "properties": {
                      "url": {
                        "type": "string",
                        "description": "商品详情页 URL"
                      },
                      "asin": {
                        "type": "string",
                        "description": "商品 ASIN"
                      },
                      "cover": {
                        "type": "string",
                        "description": "商品封面图 URL"
                      },
                      "price": {
                        "type": "string",
                        "description": "现价"
                      },
                      "score": {
                        "type": "string",
                        "description": "评分"
                      },
                      "title": {
                        "type": "string",
                        "description": "商品标题"
                      },
                      "describe": {
                        "type": "string",
                        "description": "商品简介"
                      },
                      "ratingsCount": {
                        "type": "string",
                        "description": "评价数量"
                      },
                      "originalPrice": {
                        "type": "string",
                        "description": "原价或划线价"
                      }
                    }
                  },
                  "description": "推荐商品列表"
                },
                "title": {
                  "type": "string",
                  "description": "推荐商品分组标题"
                }
              }
            },
            "description": "推荐商品分组列表.商品列表"
          },
          "screenshot": {
            "type": "string",
            "description": "本轮对话截图链接"
          },
          "followUpQuestions": {
            "type": "array",
            "items": {},
            "description": "可继续追问的问题列表"
          }
        }
      },
      "description": "Alexa 查询结果列表.仅当 format=json 时返回结构化结果"
    },
    "type": {
      "type": "string",
      "description": "渲染类型.markdown 为 stdoutWorkbenches，json 为 json"
    },
    "stdout": {
      "type": "string",
      "description": "Alexa 查询结果.Markdown 格式，包含用户问题、Alexa回答、推荐商品和可继续追问的问题"
    },
    "taskId": {
      "type": "string",
      "description": "任务ID.用于排查和追踪本次查询"
    },
    "costTime": {
      "type": "integer",
      "description": "接口耗时.单位毫秒"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗 Token 数.按上游成功对话轮次计费"
    },
    "resultsNum": {
      "type": "integer",
      "description": "对话结果数量.工具统计字段"
    }
  }
}
```

</details>
