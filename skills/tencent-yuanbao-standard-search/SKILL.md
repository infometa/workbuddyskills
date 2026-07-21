---
name: tencent-yuanbao-standard-search
display_name: "元宝搜索标准版"
description: Search the web using TencentCloud Web Search API (WSA). Prioritize using it when you need to retrieve network information.
description_zh: 基于腾讯元宝搜索API实时检索互联网信息，支持关键词、站点、时间范围搜索
description_en: Real-time web search via TencentCloud WSA API with keyword, site & time filters
version: 1.0.1
homepage: https://cloud.tencent.com/product/wsa
metadata:
  clawdbot:
    emoji: 🔍
    requires:
      bins:
      - python3
      env:
      - TENCENTCLOUD_WSA_APIKEY
---

# 元宝搜索标准版skill

元宝搜索标准版skill以互联网全网公开资源为基础，叠加腾讯优质内容生态，结合元宝APP联网搜索应用实践，从数据收录到智能检索召回，全链路构建AI友好搜索引擎。

针对用户对话中的关键问题（query）实时搜索互联网内容，返回最新相关的、高质量网页的内容信息，包括文章标题、摘要、url地址、发布时间、发布站点等，为大模型提供关键有效的决策信息，为用户提供更精准、更高质量的回答。

## 使用场景
通过接入元宝搜索标准版skill，为大模型拓展互联网信息实时检索能力，突破大模型知识困局，帮助大模型准确理解并快速回应用户的多样化问题。
- **信息查询**：搜索特定主题的互联网信息
- **热点追踪**：获取最新的新闻、资讯
- **知识检索**：查找百科、教程等知识类内容

## 工具特性
- **信息自动去噪，token消耗更友好**
- **毫秒级响应结果**
- **百亿索引内容库**
- **支持指定网址检索**
- **支持指定时间范围检索**
- **支持混合模式检索独家插件内容来源，如天气、股价、汇率等**

## 快速开始

### 开通服务并获取API KEY
使用元宝搜索标准版skill前，您需要在腾讯云联网搜索API控制台上完成准备工作：

- **[开通服务](https://console.cloud.tencent.com/wsapi/index?tab=apikey)**：登陆腾讯云联网搜索API控制台，开通标准版服务。
- **[创建服务API KEY](https://console.cloud.tencent.com/wsapi/index?tab=apikey)**：登陆腾讯云联网搜索API控制台，创建服务API KEY并保存。
- **[领取免费额度](https://console.cloud.tencent.com/wsapi/activity)**：登陆腾讯云联网搜索API活动专区页面，领取每日免费调用额度，活动限时，具体规则以页面信息为准。


### 配置API KEY环境变量
安装skill后，您需要将服务API KEY以环境变量的方式配置。

变量名称：
TENCENTCLOUD_WSA_APIKEY

在终端中设置环境变量：
```bash
export TENCENTCLOUD_WSA_APIKEY="your-api-key-here"
```


## 使用方法

** 注意：需要切换到该 skill 同目录下执行**

### 基于关键词搜索
```bash
python3 scripts/websearch.py --query="搜索关键词"
```

### 指定时间范围搜索相关信息
```bash
python3 scripts/websearch.py --query="搜索关键词" --freshness='year'
```
freshness包含以下选项:

|选项|解释|
|-----|----|
| ''| 空或者不带freshness不强调时间范围|
| day | 搜索最近一天的内容|
| week| 搜索最近一周的内容|
| month| 搜索最近一个月的内容|
| year| 搜索最近一年的内容|

### 搜索天气、金价、股价、医疗、汇率、油价、贵金属相关高时效高精度的垂类信息，混合搜索独家插件内容来源。
```bash
python3 scripts/websearch.py --query="搜索关键词" --mode=2
```

### 指定网页站点搜索
```bash
python3 scripts/websearch.py --query="搜索关键词" --site="sogou.com"
```

## 输入参数说明

| 参数    | 必填 | 说明                     | 示例                                                                |
|-------| ---- |------------------------|-------------------------------------------------------------------|
| query | 是   | 搜索关键词                 | python3 scripts/websearch.py --query="搜索关键词"                      |
| site | 否 | 用于约束搜索内网的站点,要求是严格的站点格式 | python3 scripts/websearch.py --query="搜索关键词" --site="sogou.com"   |
| mode | 否| 0-自然检索结果(默认)，1-多模态VR结果（包括天气、金价、股价、医疗、汇率、油价、贵金属等相关信息），2-混合结果（多模态VR结果+自然检索结果)| python3 scripts/websearch.py --query="搜索关键词" --mode=2             |
| freshness| 否| 'day': 表示最近一天,'week': 表示最近一周,'month': 表示最近一个月,'year': 表示最近一年|python3 scripts/websearch.py --query="搜索关键词" --freshness='year'|
## 输出示例

输出结果为markdown格式
```
## 查询词:腾讯股价, 搜索结果:8条
1. [腾讯版“小龙虾”爆火,股价涨超7%、市值重回5万亿__财经头条__新浪财经](https://cj.sina.cn/articles/view/2587691232/9a3d08e002001mr1o%3Ffroms%3Dggmp%26vt%3D4)
 - 摘要：同日,腾讯股价大涨｡截至当日收盘,报553.5港元,涨7.27%,市值重回5万亿元｡
 - 内容发布时间：2026-04-22 00:56:18
 - 网站：新浪财经
 - 相关图片：https://k.sinaimg.cn/n/sinakd20260311s/475/w909h366/20260311/e169-cee03761e128389727727e2ea2a8766c.png/w700d1q75cms.jpg
2. [港股收盘  恒指收跌1.22% 联想集团领跑蓝筹 光通信概念股逆市大涨](http://stock.10jqka.com.cn/hks/20260422/c676189781.shtml)
 - 摘要：股普遍承压,阿里(BABA)跌3.52%,腾讯(K80700)跌2.89%｡光通信板块午后涨幅扩大,长飞光纤光缆(HK6869)､剑桥科技(HK6166)均大幅上涨,得益于光模块行业景气度提升及光纤市场量价齐升;AI次新股表现亮眼,极视角(HK6636)､爱芯元智(HK0600)､澜起科技(HK6809)､智谱(HK2513)等个股均有明显上涨｡
 - 内容发布时间：2026-04-22 00:00:00
 - 网站：同花顺财经
3. [腾讯概念相关股票、成分股、图表和最新新闻 - 富途牛牛](https://www.futunn.com/sectors/Tencent-Ecosystem-BK1190)
 - 摘要：腾讯概念 添加自选 2106.612 -45.690-2.12%已收盘 04/22 16:00 (北京) 2133.563最高价2097.097最低价2132.145今开2152.302昨收2.96亿股成交量6上涨15.86市盈率(静)140.48亿成交额3平盘0.18%换手率5.72万亿总市值11下跌5.32万亿流通值概览资讯评论腾讯概念板块 分时 5日日K 周K 月K 季K 年K 
 - 内容发布时间：2026-04-22 17:17:16
 - 网站：
4. [港股收评:科指大跌1.93%!阿里腾讯跌近3%,长飞光纤逆势飙升17%创新高_财富号_东方财富网](https://caifuhao.eastmoney.com/news/20260422161755282718080)
 - 摘要：今天港股大跌,主要是地缘风险､外部情绪和权重股表现这三大因素叠加的结果｡截止收盘,恒生科技指数大幅下跌1.93%表现最弱,盘中曾跌至2.4%,恒生指数､国企指数分别下跌1.22%及1.59%｡具体盘面上,作为市场风向标的权重科技股集体下挫拖累大市下行,阿里巴巴跌3.5%,腾讯､百度跌近3%,美团､京东跌超2%;昨日多只创新高的内银股集体低迷,中国银行､建设银行跌超2%;
 - 内容发布时间：2026-04-22 16:23:38
 - 网站：财富号东方财富网
 - 相关图片：https://gbres.dfcfw.com/Files/iimage/20260422/73DECEA77DF5284865ACEDF050527BA4_w484h246.png
5. [腾讯控股](https://quote.eastmoney.com/us/TCTZF.html)
 - 摘要：腾讯控股TCTZF(2026-04-22 03:52:48)交易币种:美元1美元约折合人民币6.8163元+加自选全球指数美股行情美股吧国际期货我的自选更多名称最新价涨跌幅三友医疗17.14-2.06%ST九州--科士达48.30-1.09%华谊兄弟1.91-3.05%爱尔眼科9.690.21%广电网络3.44-1.71%诚迈科技36.71-3.27%武商集团8.39-0.
 - 内容发布时间：2026-04-22 03:52:48
 - 网站：东方财富网
6. [笑看红绿的微博_微博](http://weibo.com/u/1334095513)
 - 摘要：%｡ 看我有些惊异,太太说:“腾讯今年的涨幅高些,45%左右”｡ 腾讯2025年原来涨了这么多,我已经很久没看腾讯的股价了,应该全年没看一眼,不记得上次是 ...展开全文c 笑看红绿  2025年总结:收益平淡,生活平淡,知足常乐 2025年在股市的收益率是15.16% 有女生玩棉花娃娃,应该也是随着社会发展,年轻人情感消费提升的体现｡ 🔻就图1这事儿,老刘和吧友分享了一些截图｡ 
 - 内容发布时间：2026-04-22 19:35:54
 - 网站：微博
7. [腾讯市值比阿里巴巴高1.4万亿,阿里“差”在哪里?-ZOL问答](https://ask.zol.com.cn/x/33980977.html)
 - 摘要：已采纳 阿里差在增长预期､核心电商承压､云业务分拆遇阻､国际化进展慢,以及市场对消费复苏信心不足;而腾讯游戏､视频号､金融科技及AI布局更受青睐,估值溢价更高｡ 取消 评论 这样的现象在阿里巴巴这样的巨无霸企业身上是并不常见的,而且这样将会是最大的跌幅现象,会使阿里巴巴的股价降低,而且还会增加减持阿里的持仓 ｡ 坊间传闻,美团王兴一直不喜欢马云｡ 
 - 内容发布时间：2026-04-22 09:27:29
 - 网站：中关村在线
8. [野村下调腾讯音乐目标价至12.5美元](https://so.html5.qq.com/page/real/search_news?docid=70000021_69269e84da443152)
 - 摘要：<p>野村将腾讯音乐美股的目标价从26美元下调至12.5美元｡
 - 内容发布时间：2026-04-22 12:26:38
 - 网站：企鹅号
```

## 错误处理

使用本skill的常见报错况及处理方式如下：
- **服务不可用**：请登陆[腾讯云费用中心](https://console.cloud.tencent.com/expense/overview)检查账号是否欠费，并及时冲正。
- **服务未开通**：请登陆腾讯云[联网搜索API控制台](https://console.cloud.tencent.com/wsapi/index?tab=apikey)，开通标准版服务。
- **未授权操作**：请登陆[联网搜索API控制台](https://console.cloud.tencent.com/wsapi/index?tab=apikey)创建服务API KEY并配置到环境变量(TENCENTCLOUD_WSA_APIKEY)中。若已配置，请检查填入的变量值是否正确。