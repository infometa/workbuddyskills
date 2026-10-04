# 原始 Schema

## 原始 Input Schema

<details>
<summary>展开查看完整 Input Schema</summary>

```json
{
  "type": "object",
  "required": [
    "asin"
  ],
  "properties": {
    "asin": {
      "type": "string",
      "maxLength": 1000,
      "description": "种子 ASIN（必填，用于查询与该 ASIN 相关的商品列表）"
    },
    "page": {
      "type": "integer",
      "default": 1,
      "description": "页码"
    },
    "pageSize": {
      "type": "integer",
      "default": 50,
      "maximum": 100,
      "minimum": 10,
      "description": "每页数量"
    },
    "priceMax": {
      "type": "number",
      "description": "最高商品价格"
    },
    "priceMin": {
      "type": "number",
      "description": "最低商品价格"
    },
    "sortType": {
      "type": "string",
      "default": "desc",
      "pattern": "^(desc|asc)$",
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
      "description": "排序方式"
    },
    "fbaFeeMax": {
      "type": "number",
      "description": "最高fba佣金"
    },
    "fbaFeeMin": {
      "type": "number",
      "description": "最低fba佣金"
    },
    "sortField": {
      "type": "string",
      "default": "purchasedClicksT360",
      "pattern": "^(totalReviews|price|launchDate|clickCountT30|clickCountT90|clickCountT7|clickConversionRate|clickConversionRateComposite|customerRating|purchasedClicksT360|clickCountGrowthT7|clickCountGrowthT30|currentPrice|fbaFee|shippingFee|gpm)$",
      "examples": [
        {
          "value": "totalReviews",
          "summary": "总评论数"
        },
        {
          "value": "price",
          "summary": "价格"
        },
        {
          "value": "launchDate",
          "summary": "上架时间"
        },
        {
          "value": "clickCountT30",
          "summary": "30天点击量"
        },
        {
          "value": "clickCountT90",
          "summary": "90天点击量"
        },
        {
          "value": "clickCountT7",
          "summary": "7天点击量"
        },
        {
          "value": "clickConversionRate",
          "summary": "点击购买转化率(原7天点击转化率)"
        },
        {
          "value": "clickConversionRateComposite",
          "summary": "综合点击购买转化率"
        },
        {
          "value": "customerRating",
          "summary": "评分"
        },
        {
          "value": "purchasedClicksT360",
          "summary": "360天购买量"
        },
        {
          "value": "clickCountGrowthT7",
          "summary": "周点击增长率"
        },
        {
          "value": "clickCountGrowthT30",
          "summary": "月点击增长率"
        },
        {
          "value": "currentPrice",
          "summary": "当前价格"
        },
        {
          "value": "fbaFee",
          "summary": "fba佣金"
        },
        {
          "value": "shippingFee",
          "summary": "Fba运费"
        },
        {
          "value": "gpm",
          "summary": "毛利率"
        }
      ],
      "description": "排序字段"
    },
    "countryCode": {
      "type": "string",
      "default": "US",
      "pattern": "^(US|JP|DE)$",
      "examples": [
        {
          "value": "US",
          "summary": "美国"
        },
        {
          "value": "JP",
          "summary": "日本"
        },
        {
          "value": "DE",
          "summary": "德国"
        }
      ],
      "description": "国家,使用国家简称"
    },
    "launchDateMax": {
      "type": "string",
      "maxLength": 1000,
      "description": "最大上架时间, 格式为：yyyyMMdd000000"
    },
    "launchDateMin": {
      "type": "string",
      "maxLength": 1000,
      "description": "最小上架时间, 格式为：yyyyMMdd000000"
    },
    "nicheCountMax": {
      "type": "integer",
      "description": "最高细分市场数量"
    },
    "nicheCountMin": {
      "type": "integer",
      "description": "最低细分市场数量"
    },
    "sellerCountry": {
      "type": "string",
      "pattern": "^(AD|AE|AF|AL|AM|AR|AS|AT|AU|AX|AZ|BA|BB|BD|BE|BF|BG|BH|BJ|BN|BO|BR|BS|BT|BY|BZ|CA|CD|CF|CG|CH|CL|CM|CN|CO|CR|CV|CY|CZ|DE|DJ|DK|DO|DZ|EC|EE|EG|ES|ET|FI|FJ|FR|GA|GB|GD|GE|GG|GH|GI|GL|GR|GT|GU|GY|HK|HN|HR|HT|HU|ID|IE|IL|IN|IQ|IS|IT|JE|JM|JO|JP|KE|KG|KH|KI|KP|KR|KW|KZ|LB|LC|LI|LK|LT|LU|LV|LY|MA|MD|ME|MG|MK|MM|MN|MO|MP|MR|MT|MU|MV|MW|MX|MY|MZ|NA|NC|NG|NI|NL|NO|NP|NZ|OM|PA|PE|PF|PH|PK|PL|PR|PT|PY|QA|RO|RS|RU|RW|SA|SE|SG|SH|SI|SK|SL|SN|SR|SV|TH|TJ|TN|TR|TT|TW|TZ|UA|UG|UM|US|UY|UZ|VE|VG|VI|VN|VU|WS|YE|ZA|ZM)(,(AD|AE|AF|AL|AM|AR|AS|AT|AU|AX|AZ|BA|BB|BD|BE|BF|BG|BH|BJ|BN|BO|BR|BS|BT|BY|BZ|CA|CD|CF|CG|CH|CL|CM|CN|CO|CR|CV|CY|CZ|DE|DJ|DK|DO|DZ|EC|EE|EG|ES|ET|FI|FJ|FR|GA|GB|GD|GE|GG|GH|GI|GL|GR|GT|GU|GY|HK|HN|HR|HT|HU|ID|IE|IL|IN|IQ|IS|IT|JE|JM|JO|JP|KE|KG|KH|KI|KP|KR|KW|KZ|LB|LC|LI|LK|LT|LU|LV|LY|MA|MD|ME|MG|MK|MM|MN|MO|MP|MR|MT|MU|MV|MW|MX|MY|MZ|NA|NC|NG|NI|NL|NO|NP|NZ|OM|PA|PE|PF|PH|PK|PL|PR|PT|PY|QA|RO|RS|RU|RW|SA|SE|SG|SH|SI|SK|SL|SN|SR|SV|TH|TJ|TN|TR|TT|TW|TZ|UA|UG|UM|US|UY|UZ|VE|VG|VI|VN|VU|WS|YE|ZA|ZM))*$",
      "examples": [
        {
          "value": "AD",
          "summary": "安道尔"
        },
        {
          "value": "AE",
          "summary": "阿联酋"
        },
        {
          "value": "AF",
          "summary": "阿富汗"
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
          "value": "AR",
          "summary": "阿根廷"
        },
        {
          "value": "AS",
          "summary": "美属萨摩亚"
        },
        {
          "value": "AT",
          "summary": "奥地利"
        },
        {
          "value": "AU",
          "summary": "澳大利亚"
        },
        {
          "value": "AX",
          "summary": "奥兰"
        },
        {
          "value": "AZ",
          "summary": "阿塞拜疆"
        },
        {
          "value": "BA",
          "summary": "波黑"
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
          "value": "BF",
          "summary": "布基纳法索"
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
          "value": "BJ",
          "summary": "贝宁"
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
          "summary": "刚果民主共和国"
        },
        {
          "value": "CF",
          "summary": "中非"
        },
        {
          "value": "CG",
          "summary": "刚果共和国"
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
          "value": "CM",
          "summary": "喀麦隆"
        },
        {
          "value": "CN",
          "summary": "中国"
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
          "value": "DE",
          "summary": "德国"
        },
        {
          "value": "DJ",
          "summary": "吉布提"
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
          "value": "FI",
          "summary": "芬兰"
        },
        {
          "value": "FJ",
          "summary": "斐济"
        },
        {
          "value": "FR",
          "summary": "法国"
        },
        {
          "value": "GA",
          "summary": "加蓬"
        },
        {
          "value": "GB",
          "summary": "英国"
        },
        {
          "value": "GD",
          "summary": "格林纳达"
        },
        {
          "value": "GE",
          "summary": "格鲁吉亚"
        },
        {
          "value": "GG",
          "summary": "根西"
        },
        {
          "value": "GH",
          "summary": "加纳"
        },
        {
          "value": "GI",
          "summary": "直布罗陀"
        },
        {
          "value": "GL",
          "summary": "格陵兰"
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
          "value": "GU",
          "summary": "关岛"
        },
        {
          "value": "GY",
          "summary": "圭亚那"
        },
        {
          "value": "HK",
          "summary": "香港"
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
          "value": "HT",
          "summary": "海地"
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
          "value": "JM",
          "summary": "牙买加"
        },
        {
          "value": "JO",
          "summary": "约旦"
        },
        {
          "value": "JP",
          "summary": "日本"
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
          "value": "KI",
          "summary": "圣基茨和尼维斯"
        },
        {
          "value": "KP",
          "summary": "朝鲜"
        },
        {
          "value": "KR",
          "summary": "韩国"
        },
        {
          "value": "KW",
          "summary": "科威特"
        },
        {
          "value": "KZ",
          "summary": "哈萨克斯坦"
        },
        {
          "value": "LB",
          "summary": "黎巴嫩"
        },
        {
          "value": "LC",
          "summary": "圣卢西亚"
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
          "value": "LY",
          "summary": "利比亚"
        },
        {
          "value": "MA",
          "summary": "摩洛哥"
        },
        {
          "value": "MD",
          "summary": "摩尔多瓦"
        },
        {
          "value": "ME",
          "summary": "黑山"
        },
        {
          "value": "MG",
          "summary": "马达加斯加"
        },
        {
          "value": "MK",
          "summary": "北马其顿"
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
          "summary": "澳门"
        },
        {
          "value": "MP",
          "summary": "北马里亚纳群岛"
        },
        {
          "value": "MR",
          "summary": "毛里塔尼亚"
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
          "value": "MV",
          "summary": "马尔代夫"
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
          "value": "NC",
          "summary": "新喀里多尼亚"
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
          "value": "NP",
          "summary": "尼泊尔"
        },
        {
          "value": "NZ",
          "summary": "新西兰"
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
          "value": "PF",
          "summary": "法属波利尼西亚"
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
          "value": "PR",
          "summary": "波多黎各"
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
          "summary": "塞尔维亚"
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
          "value": "SE",
          "summary": "瑞典"
        },
        {
          "value": "SG",
          "summary": "新加坡"
        },
        {
          "value": "SH",
          "summary": "圣赫勒拿、阿森松和特里斯坦-达库尼亚"
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
          "value": "SL",
          "summary": "塞拉利昂"
        },
        {
          "value": "SN",
          "summary": "塞内加尔"
        },
        {
          "value": "SR",
          "summary": "苏里南"
        },
        {
          "value": "SV",
          "summary": "萨尔瓦多"
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
          "value": "TN",
          "summary": "突尼斯"
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
          "summary": "中华民国中国台湾省"
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
          "value": "UM",
          "summary": "美国本土外小岛屿"
        },
        {
          "value": "US",
          "summary": "美国"
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
          "value": "VE",
          "summary": "委内瑞拉"
        },
        {
          "value": "VG",
          "summary": "英属维尔京群岛"
        },
        {
          "value": "VI",
          "summary": "美属维尔京群岛"
        },
        {
          "value": "VN",
          "summary": "越南"
        },
        {
          "value": "VU",
          "summary": "瓦努阿图"
        },
        {
          "value": "WS",
          "summary": "萨摩亚"
        },
        {
          "value": "YE",
          "summary": "也门"
        },
        {
          "value": "ZA",
          "summary": "南非"
        },
        {
          "value": "ZM",
          "summary": "赞比亚"
        }
      ],
      "description": "卖家国家地区编码，选择多个的情况下用逗号隔开,如：CN,US"
    },
    "clickCountT7Max": {
      "type": "integer",
      "description": "最高周点击量"
    },
    "clickCountT7Min": {
      "type": "integer",
      "description": "最低周点击量"
    },
    "totalReviewsMax": {
      "type": "integer",
      "description": "最高评论数"
    },
    "totalReviewsMin": {
      "type": "integer",
      "description": "最低评论数"
    },
    "clickCountT30Max": {
      "type": "integer",
      "description": "最高月点击量"
    },
    "clickCountT30Min": {
      "type": "integer",
      "description": "最低月点击量"
    },
    "customerRatingMax": {
      "type": "number",
      "description": "最高评分，取值范围 0.0-5.0"
    },
    "customerRatingMin": {
      "type": "number",
      "description": "最低评分，取值范围 0.0-5.0"
    },
    "salesVolumeT360Max": {
      "type": "integer",
      "description": "最高年销售量"
    },
    "salesVolumeT360Min": {
      "type": "integer",
      "description": "最低年销售量"
    },
    "grossProfitMarginMax": {
      "type": "number",
      "description": "最高毛利率"
    },
    "grossProfitMarginMin": {
      "type": "number",
      "description": "最低毛利率"
    },
    "clickCountGrowthT7Max": {
      "type": "number",
      "description": "最高周点击增长率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickCountGrowthT7Min": {
      "type": "number",
      "description": "最低周点击增长率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickConversionRateMax": {
      "type": "number",
      "description": "最高点击购买转化率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickConversionRateMin": {
      "type": "number",
      "description": "最低点击购买转化率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickCountGrowthT30Max": {
      "type": "number",
      "description": "最高月点击增长率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickCountGrowthT30Min": {
      "type": "number",
      "description": "最低月点击增长率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickConversionRateCompositeMax": {
      "type": "number",
      "description": "最高综合转化率,取值范围 0-1，输入 0.1 表示 10%"
    },
    "clickConversionRateCompositeMin": {
      "type": "number",
      "description": "最低综合转化率,取值范围 0-1，输入 0.1 表示 10%"
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
          "gpm": {
            "type": "number",
            "description": "毛利率"
          },
          "asin": {
            "type": "string",
            "description": "亚马逊商品asin"
          },
          "link": {
            "type": "string",
            "description": "asin链接"
          },
          "brand": {
            "type": "string",
            "description": "品牌"
          },
          "price": {
            "type": "number",
            "description": "价格"
          },
          "title": {
            "type": "string",
            "description": "产品标题"
          },
          "fbaFee": {
            "type": "number",
            "description": "fba佣金"
          },
          "images": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {}
            },
            "description": "产品图(大图+小图),json格式"
          },
          "niches": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "image": {
                  "type": "string",
                  "description": "图片地址"
                },
                "demand": {
                  "type": "integer",
                  "description": "市场需求"
                },
                "nicheId": {
                  "type": "string",
                  "description": "细分市场id"
                },
                "nicheTitle": {
                  "type": "string",
                  "description": "细分市场标题"
                },
                "marketplaceId": {
                  "type": "string",
                  "description": "asin市场"
                }
              }
            },
            "description": "top3利基市场"
          },
          "trends": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "day": {
                  "type": "integer",
                  "description": "日期"
                },
                "reviewCount": {
                  "type": "integer",
                  "description": "评论数"
                },
                "clickCountT7": {
                  "type": "integer",
                  "description": "周点击量"
                },
                "reviewRating": {
                  "type": "number",
                  "description": "评分"
                },
                "averagePriceT7": {
                  "type": "number",
                  "description": "周平均价格"
                },
                "bestSellerRanking": {
                  "type": "integer",
                  "description": "BestSeller排名"
                },
                "totalOfferDepthT7": {
                  "type": "integer",
                  "description": "7天下单数"
                }
              }
            },
            "description": "90天点击量趋势"
          },
          "currency": {
            "type": "string",
            "description": "货币"
          },
          "sellerId": {
            "type": "string",
            "description": "卖家ID"
          },
          "hasMetric": {
            "type": "boolean",
            "description": "标识是否有指标"
          },
          "imagesUrl": {
            "type": "string",
            "description": "产品主图"
          },
          "nichesIds": {
            "type": "array",
            "items": {},
            "description": "市场标识列表"
          },
          "launchDate": {
            "type": "string",
            "description": "上架时间"
          },
          "nicheCount": {
            "type": "integer",
            "description": "利基市场数"
          },
          "parentAsin": {
            "type": "string",
            "description": "亚马逊商品父Asin"
          },
          "sellerName": {
            "type": "string",
            "description": "卖家名称"
          },
          "involvedNum": {
            "type": "integer",
            "description": "覆盖的关键词数量"
          },
          "shippingFee": {
            "type": "number",
            "description": "Fba运费"
          },
          "clickCountT7": {
            "type": "integer",
            "description": "7天点击量"
          },
          "currentPrice": {
            "type": "number",
            "description": "当前价格"
          },
          "totalReviews": {
            "type": "integer",
            "description": "评论数"
          },
          "categoryNames": {
            "type": "array",
            "items": {},
            "description": "类目信息"
          },
          "clickCountT30": {
            "type": "integer",
            "description": "30天点击量"
          },
          "clickCountT90": {
            "type": "integer",
            "description": "90天点击量"
          },
          "marketplaceId": {
            "type": "string",
            "description": "市场标识"
          },
          "customerRating": {
            "type": "number",
            "description": "评分"
          },
          "lastUpdateTime": {
            "type": "string",
            "description": "最后更新时间"
          },
          "sameNicheTitle": {
            "type": "string",
            "description": "同利基市场名称"
          },
          "searchValueType": {
            "type": "string",
            "description": "搜索类型[Enum values: exact(精准匹配) sameNiche(同利基市场) category(类目)]"
          },
          "involvedFrequency": {
            "type": "integer",
            "description": "覆盖的关键词频"
          },
          "bestSellersRanking": {
            "type": "array",
            "items": {
              "type": "object",
              "required": [],
              "properties": {
                "rank": {
                  "type": "integer",
                  "description": "排名"
                },
                "category": {
                  "type": "string",
                  "description": "类目名称"
                }
              }
            },
            "description": "利基市场排名"
          },
          "clickCountGrowthT7": {
            "type": "number",
            "description": "周点击增长率"
          },
          "clickConversionRate": {
            "type": "number",
            "description": "点击购买转化率(原7天点击转化率)"
          },
          "clickCountGrowthT30": {
            "type": "number",
            "description": "月点击增长率"
          },
          "purchasedClicksT360": {
            "type": "integer",
            "description": "360天购买量"
          },
          "clickConversionRateType": {
            "type": "string",
            "description": "点击转化率计算类型"
          },
          "clickConversionRateComposite": {
            "type": "number",
            "description": "综合点击购买转化率"
          },
          "clickConversionRateCompositeType": {
            "type": "string",
            "description": "点击转化率计算类型"
          }
        }
      },
      "description": "ASIN 商品列表"
    },
    "page": {
      "type": "integer",
      "description": "当前页"
    },
    "type": {
      "type": "string",
      "description": "渲染的样式"
    },
    "pages": {
      "type": "integer",
      "description": "总页数"
    },
    "total": {
      "type": "integer",
      "description": "总记录数"
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
    "pageSize": {
      "type": "integer",
      "description": "每页大小"
    },
    "costToken": {
      "type": "integer",
      "description": "消耗token"
    }
  }
}
```

</details>
