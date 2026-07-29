# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "imageUrl",
    "topNumber",
    "queryMode"
  ],
  "properties": {
    "topLoc": {
      "type": "string",
      "pattern": "^(0[1-9]|1[0-9]|2[0-9]|3[0-2]|ALL)(,(0[1-9]|1[0-9]|2[0-9]|3[0-2]|ALL))*$",
      "examples": [
        {
          "value": "01",
          "summary": "食品"
        },
        {
          "value": "02",
          "summary": "服装、服饰用品和缝纫用品"
        },
        {
          "value": "03",
          "summary": "其他类未列入的旅行用品、箱包、阳伞和个人用品"
        },
        {
          "value": "04",
          "summary": "刷子"
        },
        {
          "value": "05",
          "summary": "纺织品，人造或天然材料片材 "
        },
        {
          "value": "06",
          "summary": "家具和家居用品"
        },
        {
          "value": "07",
          "summary": "其他类未列入的家用物品"
        },
        {
          "value": "08",
          "summary": "工具和五金器具"
        },
        {
          "value": "09",
          "summary": "用于商品运输或装卸的包装和容器"
        },
        {
          "value": "10",
          "summary": "钟、表及其他测量仪器，检测仪器，信号仪器"
        },
        {
          "value": "11",
          "summary": "装饰品"
        },
        {
          "value": "12",
          "summary": "运输或提升工具"
        },
        {
          "value": "13",
          "summary": "发电、配电或变电设备"
        },
        {
          "value": "14",
          "summary": "记录、电信或数据处理设备"
        },
        {
          "value": "15",
          "summary": "其他类未列入的机械"
        },
        {
          "value": "16",
          "summary": "照相设备、电影摄影设备和光学设备"
        },
        {
          "value": "17",
          "summary": "乐器"
        },
        {
          "value": "18",
          "summary": "印刷和办公机械"
        },
        {
          "value": "19",
          "summary": "文具、办公用品、美术用品和教学用品"
        },
        {
          "value": "20",
          "summary": "销售设备、广告设备和标志物"
        },
        {
          "value": "21",
          "summary": "游戏器具、玩具、帐篷和体育用品"
        },
        {
          "value": "22",
          "summary": "武器，烟火用品，用于狩猎、捕鱼及捕杀有害动物的用具"
        },
        {
          "value": "23",
          "summary": "流体分配设备、卫生设备、加热设备、通风和空气调节设备、固体燃料"
        },
        {
          "value": "24",
          "summary": "医疗设备和实验室设备"
        },
        {
          "value": "25",
          "summary": "建筑构件和施工元件"
        },
        {
          "value": "26",
          "summary": "照明设备"
        },
        {
          "value": "27",
          "summary": "烟草和吸烟用具"
        },
        {
          "value": "28",
          "summary": "药品，化妆品，梳妆用品和设备"
        },
        {
          "value": "29",
          "summary": "防火灾、防事故、救援用的装置及设备"
        },
        {
          "value": "30",
          "summary": "动物照管与驯养用品"
        },
        {
          "value": "31",
          "summary": "其他类未列入的食品或饮料制备机械和设备"
        },
        {
          "value": "32",
          "summary": "图形符号、标识、表面图案、纹饰、内部和外部布置"
        },
        {
          "value": "ALL",
          "summary": "全部"
        }
      ],
      "description": "指定检索的一级LOC范围, 不指定时代表使用模型LOC预测服务的结果, 可多选, 多选时多个编码用逗号隔开，如 01,02"
    },
    "regions": {
      "type": "string",
      "default": "US",
      "pattern": "^(SE|EU|CH|IE|BR|MX|US|WO|GB|IL|JP|IN|DK|DE|AU|IT|NZ|AT|CA|BX|FI|FR|CN|KR|TH)(,(SE|EU|CH|IE|BR|MX|US|WO|GB|IL|JP|IN|DK|DE|AU|IT|NZ|AT|CA|BX|FI|FR|CN|KR|TH))*$",
      "examples": [
        {
          "value": "SE",
          "summary": "瑞典"
        },
        {
          "value": "EU",
          "summary": "欧盟"
        },
        {
          "value": "CH",
          "summary": "瑞士"
        },
        {
          "value": "IE",
          "summary": "爱尔兰"
        },
        {
          "value": "BR",
          "summary": "巴西"
        },
        {
          "value": "MX",
          "summary": "墨西哥"
        },
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "WO",
          "summary": "世界知识产权"
        },
        {
          "value": "GB",
          "summary": "英国"
        },
        {
          "value": "IL",
          "summary": "以色列"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "IN",
          "summary": "印度"
        },
        {
          "value": "DK",
          "summary": "丹麦"
        },
        {
          "value": "DE",
          "summary": "德国"
        },
        {
          "value": "AU",
          "summary": "澳大利亚"
        },
        {
          "value": "IT",
          "summary": "意大利"
        },
        {
          "value": "NZ",
          "summary": "新西兰"
        },
        {
          "value": "AT",
          "summary": "奥地利"
        },
        {
          "value": "CA",
          "summary": "加拿大"
        },
        {
          "value": "BX",
          "summary": "玻利维亚"
        },
        {
          "value": "FI",
          "summary": "芬兰"
        },
        {
          "value": "FR",
          "summary": "法国"
        },
        {
          "value": "CN",
          "summary": "中国"
        },
        {
          "value": "KR",
          "summary": "韩国"
        },
        {
          "value": "TH",
          "summary": "泰国"
        }
      ],
      "description": "商品所售卖国家/地区代码, 可多选, 多选时多个编码用逗号隔开，如： US,CH,IE"
    },
    "imageUrl": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品图片文件URL"
    },
    "queryMode": {
      "type": "string",
      "default": "hybrid",
      "pattern": "physical|line|hybrid",
      "examples": [
        {
          "value": "physical",
          "summary": "实物图检索模式"
        },
        {
          "value": "line",
          "summary": "线条图检索模式"
        },
        {
          "value": "hybrid",
          "summary": "混合检索模式"
        }
      ],
      "description": "检索模式"
    },
    "topNumber": {
      "type": "integer",
      "default": 100,
      "maximum": 100,
      "description": "召回专利数量"
    },
    "enableRadar": {
      "type": "boolean",
      "default": true,
      "description": "是否启用雷达图"
    },
    "patentStatus": {
      "type": "string",
      "default": "1",
      "examples": [
        {
          "value": "1",
          "summary": "检索有效专利"
        },
        {
          "value": "0",
          "summary": "检索失效专利"
        }
      ],
      "maxLength": 1000,
      "description": "专利有效性, 可多选, 多选时多个状态用逗号隔开，如 1,0"
    },
    "productTitle": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品标题"
    },
    "sourceLanguage": {
      "type": "string",
      "maxLength": 1000,
      "description": "原语言，需要标记，以便统一翻译成英文，文本为英语时传空即可.例如：zh-CN"
    },
    "productDescription": {
      "type": "string",
      "maxLength": 1000,
      "description": "产品描述"
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
    "data": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [],
        "properties": {
          "images": {
            "type": "array",
            "items": {},
            "description": "专利图片列表"
          },
          "troCase": {
            "type": "boolean",
            "description": "是否有TRO维权史"
          },
          "abstracts": {
            "type": "string",
            "description": "专利摘要"
          },
          "grantDate": {
            "type": "string",
            "description": "专利授权日"
          },
          "inventors": {
            "type": "array",
            "items": {},
            "description": "发明人"
          },
          "patentLoc": {
            "type": "string",
            "description": "该专利的loc分类，多个loc英文逗号隔开"
          },
          "troHolder": {
            "type": "boolean",
            "description": "是否是TRO权利人的专利"
          },
          "applicants": {
            "type": "array",
            "items": {},
            "description": "申请人"
          },
          "locOneInfo": {
            "type": "string",
            "description": "loc一级详情"
          },
          "locTwoInfo": {
            "type": "string",
            "description": "loc二级详情"
          },
          "patentProd": {
            "type": "string",
            "description": "专利标题"
          },
          "similarity": {
            "type": "string",
            "description": "专利与产品相似度"
          },
          "radarResult": {
            "type": "object",
            "required": [],
            "properties": {
              "exp": {
                "type": "string",
                "description": "预期描述"
              },
              "same": {
                "type": "boolean",
                "description": "是否疑似侵权"
              }
            }
          },
          "isSketchText": {
            "type": "string",
            "description": "是否线稿图"
          },
          "patentFamily": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "同族专利"
          },
          "patentProdCn": {
            "type": "string",
            "description": "专利标题中文"
          },
          "globalImageId": {
            "type": "string",
            "description": "专利图片的ID"
          },
          "specification": {
            "type": "string",
            "description": "专利说明书"
          },
          "globalPatentId": {
            "type": "string",
            "description": "全球专利ID"
          },
          "patentImageUrl": {
            "type": "string",
            "description": "与产品图片相似度最高的专利附图"
          },
          "patentValidity": {
            "type": "string",
            "description": "专利有效性"
          },
          "applicationDate": {
            "type": "string",
            "description": "专利申请日"
          },
          "publicationDate": {
            "type": "string",
            "description": "专利公开日"
          },
          "estimatedDueDate": {
            "type": "string",
            "description": "预估到期日"
          },
          "applicationNumber": {
            "type": "string",
            "description": "专利申请号"
          },
          "publicationNumber": {
            "type": "string",
            "description": "专利公开号"
          },
          "applicantAddresses": {
            "type": "array",
            "items": {},
            "description": "申请人地址"
          },
          "registrationOfficeCode": {
            "type": "string",
            "description": "专利注册受理局"
          }
        }
      },
      "description": "专利列表"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "total": {
      "type": "integer",
      "description": "记录数"
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
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
