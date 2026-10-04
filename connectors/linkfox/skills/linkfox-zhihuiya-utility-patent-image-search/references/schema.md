# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "model",
    "patentType",
    "url"
  ],
  "properties": {
    "loc": {
      "type": "string",
      "maxLength": 1000,
      "description": "LOC分类(洛迦诺分类号)，多个分类号可以用逻辑符AND/OR/NOT连接"
    },
    "url": {
      "type": "string",
      "maxLength": 1000,
      "description": "图像的URL"
    },
    "lang": {
      "type": "string",
      "default": "original",
      "examples": [
        {
          "value": "original",
          "summary": "专利原文标题"
        },
        {
          "value": "cn",
          "summary": "专利中文翻译标题"
        },
        {
          "value": "en",
          "summary": "专利英文翻译标题"
        }
      ],
      "maxLength": 1000,
      "description": "设置标题的语言优先选择，可以选cn、en、original"
    },
    "field": {
      "type": "string",
      "default": "SCORE",
      "examples": [
        {
          "value": "SCORE",
          "summary": "按照最相关排序"
        },
        {
          "value": "APD",
          "summary": "按照申请日排序"
        },
        {
          "value": "PBD",
          "summary": "按照公开日排序"
        },
        {
          "value": "ISD",
          "summary": "按照授权日排序"
        }
      ],
      "maxLength": 1000,
      "description": "返回结果排序field支持SCORE,APD,PBD,ISD"
    },
    "limit": {
      "type": "integer",
      "default": 10,
      "maximum": 100,
      "description": "返回专利条数, 1 <= limit <= 100，默认为10"
    },
    "model": {
      "type": "integer",
      "examples": [
        {
          "value": "1",
          "summary": "外观专利-智能联想【推荐】"
        },
        {
          "value": "2",
          "summary": "外观专利-搜索此图"
        },
        {
          "value": "3",
          "summary": "实用新型专利-匹配形状"
        },
        {
          "value": "4",
          "summary": "实用新型专利-匹配形状/图案/色彩【推荐】"
        }
      ],
      "description": "选择图像检索模型，外观专利：1-智能联想，2-搜索此图；实用新型专利：3-匹配形状，4-匹配形状/图案/色彩"
    },
    "order": {
      "type": "string",
      "default": "desc",
      "examples": [
        {
          "value": "desc",
          "summary": "降序"
        },
        {
          "value": "asc",
          "summary": "升序"
        }
      ],
      "maxLength": 1000,
      "description": "当field选择APD,PBD,ISD时有效，order支持desc,asc"
    },
    "offset": {
      "type": "integer",
      "default": 0,
      "maximum": 1000,
      "minimum": 0,
      "description": "偏移量，0 <= offset <= 1000，默认为0"
    },
    "country": {
      "type": "string",
      "examples": [
        {
          "value": "WO",
          "summary": "世界知识产权组织"
        },
        {
          "value": "EP",
          "summary": "欧洲专利局"
        },
        {
          "value": "CN",
          "summary": "中国"
        },
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "KR",
          "summary": "韩国"
        },
        {
          "value": "DE",
          "summary": "德国"
        },
        {
          "value": "FR",
          "summary": "法国"
        },
        {
          "value": "AU",
          "summary": "澳大利亚"
        },
        {
          "value": "AD",
          "summary": "安道尔"
        },
        {
          "value": "AE",
          "summary": "阿联酋"
        },
        {
          "value": "AG",
          "summary": "安提瓜和巴布达"
        },
        {
          "value": "AI",
          "summary": "安圭拉"
        },
        {
          "value": "AL",
          "summary": "阿尔巴尼亚"
        },
        {
          "value": "AM",
          "summary": "亚美尼亚"
        },
        {
          "value": "AO",
          "summary": "安哥拉"
        },
        {
          "value": "AP",
          "summary": "亚太地区"
        },
        {
          "value": "AR",
          "summary": "阿根廷"
        },
        {
          "value": "AT",
          "summary": "奥地利"
        },
        {
          "value": "AW",
          "summary": "阿鲁巴"
        },
        {
          "value": "AZ",
          "summary": "阿塞拜疆"
        },
        {
          "value": "BA",
          "summary": "波斯尼亚和黑塞哥维那"
        },
        {
          "value": "BB",
          "summary": "巴巴多斯"
        },
        {
          "value": "BD",
          "summary": "孟加拉国"
        },
        {
          "value": "BE",
          "summary": "比利时"
        },
        {
          "value": "BG",
          "summary": "保加利亚"
        },
        {
          "value": "BH",
          "summary": "巴林"
        },
        {
          "value": "BM",
          "summary": "百慕大"
        },
        {
          "value": "BN",
          "summary": "文莱"
        },
        {
          "value": "BO",
          "summary": "玻利维亚"
        },
        {
          "value": "BR",
          "summary": "巴西"
        },
        {
          "value": "BS",
          "summary": "巴哈马"
        },
        {
          "value": "BT",
          "summary": "不丹"
        },
        {
          "value": "BW",
          "summary": "博茨瓦纳"
        },
        {
          "value": "BX",
          "summary": "比荷卢经济联盟"
        },
        {
          "value": "BY",
          "summary": "白俄罗斯"
        },
        {
          "value": "BZ",
          "summary": "伯利兹"
        },
        {
          "value": "CA",
          "summary": "加拿大"
        },
        {
          "value": "CD",
          "summary": "刚果（金）"
        },
        {
          "value": "CG",
          "summary": "刚果（布）"
        },
        {
          "value": "CH",
          "summary": "瑞士"
        },
        {
          "value": "CL",
          "summary": "智利"
        },
        {
          "value": "CO",
          "summary": "哥伦比亚"
        },
        {
          "value": "CR",
          "summary": "哥斯达黎加"
        },
        {
          "value": "CS",
          "summary": "捷克和斯洛伐克共和国"
        },
        {
          "value": "CU",
          "summary": "古巴"
        },
        {
          "value": "CV",
          "summary": "佛得角"
        },
        {
          "value": "CY",
          "summary": "塞浦路斯"
        },
        {
          "value": "CZ",
          "summary": "捷克"
        },
        {
          "value": "DD",
          "summary": "东德"
        },
        {
          "value": "DJ",
          "summary": "吉布提"
        },
        {
          "value": "DM",
          "summary": "多米尼克"
        },
        {
          "value": "DK",
          "summary": "丹麦"
        },
        {
          "value": "DO",
          "summary": "多米尼加"
        },
        {
          "value": "DZ",
          "summary": "阿尔及利亚"
        },
        {
          "value": "EA",
          "summary": "欧亚专利局"
        },
        {
          "value": "EC",
          "summary": "厄瓜多尔"
        },
        {
          "value": "EE",
          "summary": "爱沙尼亚"
        },
        {
          "value": "EG",
          "summary": "埃及"
        },
        {
          "value": "ES",
          "summary": "西班牙"
        },
        {
          "value": "ET",
          "summary": "埃塞俄比亚"
        },
        {
          "value": "EU",
          "summary": "欧盟"
        },
        {
          "value": "FI",
          "summary": "芬兰"
        },
        {
          "value": "FJ",
          "summary": "斐济"
        },
        {
          "value": "GB",
          "summary": "英国"
        },
        {
          "value": "GC",
          "summary": "海湾地区阿拉伯国家合作委员会专利局"
        },
        {
          "value": "GE",
          "summary": "格鲁吉亚"
        },
        {
          "value": "GH",
          "summary": "加纳"
        },
        {
          "value": "GR",
          "summary": "希腊"
        },
        {
          "value": "GT",
          "summary": "危地马拉"
        },
        {
          "value": "GY",
          "summary": "圭亚那"
        },
        {
          "value": "HK",
          "summary": "中国香港"
        },
        {
          "value": "HN",
          "summary": "洪都拉斯"
        },
        {
          "value": "HR",
          "summary": "克罗地亚"
        },
        {
          "value": "HU",
          "summary": "匈牙利"
        },
        {
          "value": "ID",
          "summary": "印度尼西亚"
        },
        {
          "value": "IE",
          "summary": "爱尔兰"
        },
        {
          "value": "IL",
          "summary": "以色列"
        },
        {
          "value": "IN",
          "summary": "印度"
        },
        {
          "value": "IQ",
          "summary": "伊拉克"
        },
        {
          "value": "IR",
          "summary": "伊朗"
        },
        {
          "value": "IS",
          "summary": "冰岛"
        },
        {
          "value": "IT",
          "summary": "意大利"
        },
        {
          "value": "JE",
          "summary": "泽西"
        },
        {
          "value": "JO",
          "summary": "约旦"
        },
        {
          "value": "KE",
          "summary": "肯尼亚"
        },
        {
          "value": "KG",
          "summary": "吉尔吉斯斯坦"
        },
        {
          "value": "KH",
          "summary": "柬埔寨"
        },
        {
          "value": "KY",
          "summary": "开曼群岛"
        },
        {
          "value": "KZ",
          "summary": "哈萨克斯坦"
        },
        {
          "value": "LA",
          "summary": "老挝"
        },
        {
          "value": "LB",
          "summary": "黎巴嫩"
        },
        {
          "value": "LI",
          "summary": "列支敦士登"
        },
        {
          "value": "LK",
          "summary": "斯里兰卡"
        },
        {
          "value": "LT",
          "summary": "立陶宛"
        },
        {
          "value": "LU",
          "summary": "卢森堡"
        },
        {
          "value": "LV",
          "summary": "拉脱维亚"
        },
        {
          "value": "MA",
          "summary": "摩洛哥"
        },
        {
          "value": "MC",
          "summary": "摩纳哥"
        },
        {
          "value": "MD",
          "summary": "摩尔多瓦"
        },
        {
          "value": "ME",
          "summary": "黑山共和国"
        },
        {
          "value": "MG",
          "summary": "马达加斯加"
        },
        {
          "value": "MK",
          "summary": "北马其顿共和国"
        },
        {
          "value": "MM",
          "summary": "缅甸"
        },
        {
          "value": "MN",
          "summary": "蒙古"
        },
        {
          "value": "MO",
          "summary": "中国澳门"
        },
        {
          "value": "MS",
          "summary": "蒙特塞拉特"
        },
        {
          "value": "MT",
          "summary": "马耳他"
        },
        {
          "value": "MU",
          "summary": "毛里求斯"
        },
        {
          "value": "MW",
          "summary": "马拉维"
        },
        {
          "value": "MX",
          "summary": "墨西哥"
        },
        {
          "value": "MY",
          "summary": "马来西亚"
        },
        {
          "value": "MZ",
          "summary": "莫桑比克"
        },
        {
          "value": "NA",
          "summary": "纳米比亚"
        },
        {
          "value": "NG",
          "summary": "尼日利亚"
        },
        {
          "value": "NI",
          "summary": "尼加拉瓜"
        },
        {
          "value": "NL",
          "summary": "荷兰"
        },
        {
          "value": "NO",
          "summary": "挪威"
        },
        {
          "value": "NZ",
          "summary": "新西兰"
        },
        {
          "value": "OA",
          "summary": "非洲知识产权组织"
        },
        {
          "value": "OM",
          "summary": "阿曼"
        },
        {
          "value": "PA",
          "summary": "巴拿马"
        },
        {
          "value": "PE",
          "summary": "秘鲁"
        },
        {
          "value": "PG",
          "summary": "巴布亚新几内亚"
        },
        {
          "value": "PH",
          "summary": "菲律宾"
        },
        {
          "value": "PK",
          "summary": "巴基斯坦"
        },
        {
          "value": "PL",
          "summary": "波兰"
        },
        {
          "value": "PS",
          "summary": "巴勒斯坦"
        },
        {
          "value": "PT",
          "summary": "葡萄牙"
        },
        {
          "value": "PY",
          "summary": "巴拉圭"
        },
        {
          "value": "QA",
          "summary": "卡塔尔"
        },
        {
          "value": "RO",
          "summary": "罗马尼亚"
        },
        {
          "value": "RS",
          "summary": "塞尔维亚共和国"
        },
        {
          "value": "RU",
          "summary": "俄罗斯"
        },
        {
          "value": "RW",
          "summary": "卢旺达"
        },
        {
          "value": "SA",
          "summary": "沙特阿拉伯"
        },
        {
          "value": "SB",
          "summary": "所罗门群岛"
        },
        {
          "value": "SC",
          "summary": "塞舌尔"
        },
        {
          "value": "SD",
          "summary": "苏丹"
        },
        {
          "value": "SE",
          "summary": "瑞典"
        },
        {
          "value": "SG",
          "summary": "新加坡"
        },
        {
          "value": "SI",
          "summary": "斯洛文尼亚"
        },
        {
          "value": "SK",
          "summary": "斯洛伐克"
        },
        {
          "value": "SM",
          "summary": "圣马力诺"
        },
        {
          "value": "ST",
          "summary": "圣多美和普林西比"
        },
        {
          "value": "SU",
          "summary": "前苏联"
        },
        {
          "value": "SV",
          "summary": "萨尔瓦多"
        },
        {
          "value": "SY",
          "summary": "叙利亚"
        },
        {
          "value": "TC",
          "summary": "特克斯和凯科斯群岛"
        },
        {
          "value": "TH",
          "summary": "泰国"
        },
        {
          "value": "TJ",
          "summary": "塔吉克斯坦"
        },
        {
          "value": "TM",
          "summary": "土库曼斯坦"
        },
        {
          "value": "TN",
          "summary": "突尼斯"
        },
        {
          "value": "TO",
          "summary": "汤加"
        },
        {
          "value": "TR",
          "summary": "土耳其"
        },
        {
          "value": "TT",
          "summary": "特立尼达和多巴哥"
        },
        {
          "value": "TW",
          "summary": "中国台湾"
        },
        {
          "value": "TZ",
          "summary": "坦桑尼亚"
        },
        {
          "value": "UA",
          "summary": "乌克兰"
        },
        {
          "value": "UG",
          "summary": "乌干达"
        },
        {
          "value": "UY",
          "summary": "乌拉圭"
        },
        {
          "value": "UZ",
          "summary": "乌兹别克斯坦"
        },
        {
          "value": "VC",
          "summary": "圣文森特和格林纳丁斯"
        },
        {
          "value": "VE",
          "summary": "委内瑞拉"
        },
        {
          "value": "VG",
          "summary": "英属维尔京群岛"
        },
        {
          "value": "VN",
          "summary": "越南"
        },
        {
          "value": "WS",
          "summary": "萨摩亚"
        },
        {
          "value": "XK",
          "summary": "科索沃"
        },
        {
          "value": "YE",
          "summary": "也门"
        },
        {
          "value": "YU",
          "summary": "南斯拉夫"
        },
        {
          "value": "ZA",
          "summary": "南非"
        },
        {
          "value": "ZM",
          "summary": "赞比亚"
        },
        {
          "value": "ZN",
          "summary": "桑给巴尔"
        },
        {
          "value": "ZW",
          "summary": "津巴布韦"
        }
      ],
      "maxLength": 1000,
      "description": "专利受理局（国家/组织/地区代码），多个用英文逗号隔开，不传时代表查询全部专利受理局的数据"
    },
    "isHttps": {
      "type": "integer",
      "default": 0,
      "description": "选择是否返回https域名图片，1：返回https，0：返回http"
    },
    "stemming": {
      "type": "integer",
      "default": 0,
      "examples": [
        {
          "value": "1",
          "summary": "开启"
        },
        {
          "value": "0",
          "summary": "关闭"
        }
      ],
      "description": "是否开启截词功能，1：开启；0：关闭"
    },
    "assignees": {
      "type": "string",
      "maxLength": 1000,
      "description": "申请（专利权）人"
    },
    "mainField": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利主要字段，包括标题、摘要、权利要求、说明书、公开号、申请号、申请人、发明人和IPC/UPC/LOC分类号"
    },
    "preFilter": {
      "type": "integer",
      "default": 1,
      "examples": [
        {
          "value": "1",
          "summary": "开启"
        },
        {
          "value": "0",
          "summary": "关闭"
        }
      ],
      "description": "是否开启前置国家/LOC过滤，1：开启；0：关闭"
    },
    "patentType": {
      "type": "string",
      "default": "D",
      "pattern": "D|U",
      "examples": [
        {
          "value": "D",
          "summary": "外观专利"
        },
        {
          "value": "U",
          "summary": "实用新型专利"
        }
      ],
      "description": "选择检索外观专利或实用新型专利：D-外观专利，U-实用新型专利"
    },
    "legalStatus": {
      "type": "string",
      "examples": [
        {
          "value": "1",
          "summary": "公开"
        },
        {
          "value": "2",
          "summary": "实质审查"
        },
        {
          "value": "3",
          "summary": "授权"
        },
        {
          "value": "8",
          "summary": "避免重复授权"
        },
        {
          "value": "11",
          "summary": "撤回"
        },
        {
          "value": "12",
          "summary": "撤回-未指定类型"
        },
        {
          "value": "17",
          "summary": "撤回-视为撤回"
        },
        {
          "value": "18",
          "summary": "撤回-主动撤回"
        },
        {
          "value": "13",
          "summary": "驳回"
        },
        {
          "value": "14",
          "summary": "全部撤销"
        },
        {
          "value": "15",
          "summary": "期限届满"
        },
        {
          "value": "16",
          "summary": "未缴年费"
        },
        {
          "value": "21",
          "summary": "权利恢复"
        },
        {
          "value": "22",
          "summary": "权利终止"
        },
        {
          "value": "23",
          "summary": "部分无效"
        },
        {
          "value": "24",
          "summary": "申请终止"
        },
        {
          "value": "30",
          "summary": "放弃"
        },
        {
          "value": "19",
          "summary": "放弃-视为放弃"
        },
        {
          "value": "20",
          "summary": "放弃-主动放弃"
        },
        {
          "value": "25",
          "summary": "放弃-未指定类型"
        },
        {
          "value": "222",
          "summary": "PCT未进入指定国（指定期内）"
        },
        {
          "value": "223",
          "summary": "PCT进入指定国（指定期内）"
        },
        {
          "value": "224",
          "summary": "PCT进入指定国（指定期满）"
        },
        {
          "value": "225",
          "summary": "PCT未进入指定国（指定期满）"
        }
      ],
      "maxLength": 1000,
      "description": "专利的法律状态，多个用英文逗号隔开"
    },
    "returnImgId": {
      "type": "boolean",
      "default": false,
      "description": "是否返回img_id"
    },
    "applyEndTime": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利申请截止时间，格式:yyyyMMdd"
    },
    "publicEndTime": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利公开截止时间，格式:yyyyMMdd"
    },
    "applyStartTime": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利申请起始时间，格式:yyyyMMdd"
    },
    "scoreExpansion": {
      "type": "boolean",
      "description": "分数拓展"
    },
    "publicStartTime": {
      "type": "string",
      "maxLength": 1000,
      "description": "专利公开起始时间，格式:yyyyMMdd"
    },
    "simpleLegalStatus": {
      "type": "string",
      "examples": [
        {
          "value": "0",
          "summary": "失效"
        },
        {
          "value": "1",
          "summary": "有效"
        },
        {
          "value": "2",
          "summary": "审中"
        },
        {
          "value": "220",
          "summary": "PCT指定期满"
        },
        {
          "value": "221",
          "summary": "PCT指定期内"
        },
        {
          "value": "999",
          "summary": "未确认"
        }
      ],
      "maxLength": 1000,
      "description": "专利的简单法律状态，多个用英文逗号隔开"
    },
    "includeMachineTranslation": {
      "type": "boolean",
      "description": "搜索包含机器翻译数据"
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
          "loc": {
            "type": "array",
            "items": {},
            "description": "LOC分类"
          },
          "url": {
            "type": "string",
            "description": "相似的专利附图"
          },
          "apdt": {
            "type": "integer",
            "description": "申请日"
          },
          "apno": {
            "type": "string",
            "description": "申请号"
          },
          "pbdt": {
            "type": "integer",
            "description": "公开日"
          },
          "imgId": {
            "type": "string",
            "description": "相似的专利附图img_id"
          },
          "score": {
            "type": "number",
            "description": "相似度分数（仅当按照相似度排序时有效，即请求参数field为SCORE）"
          },
          "title": {
            "type": "string",
            "description": "专利名称"
          },
          "inventor": {
            "type": "string",
            "description": "发明人"
          },
          "locMatch": {
            "type": "integer",
            "description": "是否命中高权重LOC，1为命中，0为未命中（仅当model=1且field=SCORE时有效）"
          },
          "patentId": {
            "type": "string",
            "description": "相似专利ID"
          },
          "patentPn": {
            "type": "string",
            "description": "相似专利号"
          },
          "authority": {
            "type": "string",
            "description": "受理局"
          },
          "currentAssignee": {
            "type": "string",
            "description": "当前申请人"
          },
          "originalAssignee": {
            "type": "string",
            "description": "原始申请人"
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
    },
    "allRecordsCount": {
      "type": "integer",
      "description": "总记录数"
    }
  }
}
```

</details>
