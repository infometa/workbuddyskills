# 站点对照

Amazon 与 TikTok 的站点参数不要混用。

## Amazon（表 1.1）

未指定站点时，Amazon 工具默认美国站 `webSiteId=1`。`marketplace` 与 `webSiteId` 取值相同。

| # | marketplace | webSiteId | 区域代码 | fromSite | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | us | com | 美国；amazon.com |
| 2 | 2 | 2 | gb | co.uk | 英国；amazon.co.uk |
| 3 | 3 | 3 | de | de | 德国；amazon.de |
| 4 | 4 | 4 | fr | fr | 法国；amazon.fr |
| 5 | 5 | 5 | jp | co.jp | 日本；amazon.co.jp |
| 6 | 6 | 6 | ca | ca | 加拿大；amazon.ca |
| 7 | 8 | 8 | it | it | 意大利；amazon.it |
| 8 | 9 | 9 | es | es | 西班牙；amazon.es |
| 9 | 10 | 10 | in | in | 印度；amazon.in |
| 10 | 11 | 11 | mx | com.mx | 墨西哥；amazon.com.mx |

## TikTok

`countryRegion` 传参时取「取值」列的中文名称（如 `"countryRegion": "美国"`）。`region` 传参时取「region」列区域代码（如 `region=us`）。

| # | 取值（countryRegion 用中文） | region | 站点 |
| --- | --- | --- | --- |
| 1 | 美国 | us | 美国站 |
| 2 | 日本 | jp | 日本站 |
| 3 | 越南 | vn | 越南站 |
| 4 | 菲律宾 | ph | 菲律宾站 |
| 5 | 马来西亚 | my | 马来西亚站 |
| 6 | 印度尼西亚 | id | 印度尼西亚站 |
| 7 | 泰国 | th | 泰国站 |
| 8 | 新加坡 | sg | 新加坡站 |
| 9 | 墨西哥 | mx | 墨西哥站 |
| 10 | 西班牙 | es | 西班牙站 |
| 11 | 英国 | gb | 英国站 |
| 12 | 德国 | de | 德国站 |
| 13 | 意大利 | it | 意大利站 |
| 14 | 法国 | fr | 法国站 |
| 15 | 巴西 | br | 巴西站 |
