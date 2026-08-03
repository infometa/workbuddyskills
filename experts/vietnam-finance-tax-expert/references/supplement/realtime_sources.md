# 越南财税金融 · 实时数据源注册表

> 用途：当用户问"当前汇率 / 最新税率 / 某 HS 编码关税 / 最新法规"时，按本表用 WebFetch 直连权威源实时查询，弥补静态语料无实时行情的短板。
> 创建：2026-07-24 ｜ 维护：vietnam-finance-tax-expert

## 使用原则
1. **实时数据必须标注来源 URL 与抓取日期**，不得与静态语料混淆。
2. 优先用**官方源**（SBV / GDT / 海关 / vbpl.vn）；中文用户优先"税路通"中文编译。
3. 外汇以 **Vietcombank** 为最易抓取基准，SBV 为官方参照。
4. 关税以 **tariff.customs.gov.vn** 为唯一官方 HS 查询平台（2022 起 10 位制）。

## 数据源清单

| ID | 名称 | URL | 类别 | 查什么 | 更新频率 | 可信度 |
|---|---|---|---|---|---|---|
| sbv_fx | 国家银行参考汇率 | https://www.sbv.gov.vn/vi/t%E1%BB%B7-gi%C3%A1 | 外汇/实时 | USD/EUR/CNY 买卖中间价 | 每日 | 官方 |
| vcb_fx | Vietcombank 牌价 | https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia | 外汇/实时 | 多币种现钞/转账买卖价(含CNY) | 每日多次 | 商业银行基准 |
| gdt_news | 税务总局门户 | https://gdt.gov.vn | 税务/半实时 | 税务新政、电子发票、跨境税 | 持续 | 官方 |
| chinatax_vn | 税路通·越南税讯(中文) | https://www.chinatax.gov.cn/chinatax/c102745/c5242838/content.html | 税务/半实时 | 越南税改中文编译 | 持续 | 高(中资首选) |
| tariff_customs | 海关税则系统 | https://tariff.customs.gov.vn | 关税/实时 | HS 编码查进口关税/VAT/SCT | 随法令 | 官方 |
| vtip | 越南贸易门户 | https://www.vietnamtradeportal.gov.vn/ | 贸易/半实时 | 进出口流程、HS、FTA、SPS | 持续 | 海关主办 |
| vbpl | 国家法理库 | https://vbpl.vn/ | 法规/半实时 | 法律/法令全文(2026升级版) | 持续 | 司法部官方 |
| lawnet | Lawnet 法律库 | https://lawnet.vn/ | 法规/半实时 | 英文法律摘要、效力状态 | 持续 | 高 |
| luatvietnam | LuatVietnam | https://luatvietnam.vn/ | 法规/半实时 | 法律解读、模板、实务 | 持续 | 高 |
| fia_vn | 外资局 FIA | https://dautunuocngoai.gov.vn/ | 投资/半实时 | FDI 政策、流程、统计 | 持续 | 官方 |
| mof_vn | 财政部 MoF | https://www.mof.gov.vn/ | 财税/会计/保险 | VAS、保险、证券法令 | 持续 | 官方 |
| ssc_vn | 证券委员会 SSC | https://www.ssc.gov.vn/ | 证券/半实时 | 证券发行/上市/披露 | 持续 | 官方 |
| wtocenter | VCCI 世贸中心 | https://www.wtocenter.vn/german-market/24176-import-tax-searching-tools | 关税/FTA | FTA 优惠税率检索指引 | 随法令 | 高 |

### 非税金融实时源（本轮新增，补足静态语料短板）

| ID | 名称 | URL | 类别 | 查什么 | 更新频率 | 可信度 |
|---|---|---|---|---|---|---|
| sbv_policy_rate | 国家银行政策利率 | https://www.sbv.gov.vn/webcenter/portal/vi/menu/trang-chu/hoat-dong-nh/tra-soat-lai-suat | 银行/实时 | 再融资/再贴现利率、平均放贷利率 | 货币政策会议 | 官方 |
| vcb_rates | Vietcombank 存贷款 | https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Lai-suat | 银行/实时 | 企业本外币存贷款基准利率 | 随行就价 | 商业银行基准 |
| vss_portal | 社保局 VSS | https://baohiemxahoi.gov.vn/ | 社保/半实时 | 社保费率、外籍员工参保 | 随《社保法》 | 官方 |
| hose_hnx | 胡志明/河内证交所 | https://www.hsx.vn/Modules/Listing/Web/Stock | 证券/实时 | VN-Index、个股市价、成交量 | 交易时段 | 交易所 |
| mof_insurance | 财政部保险监管 | https://www.mof.gov.vn/webcenter/portal/vi/pages_tt/ttcq/bh | 保险/半实时 | 强制险费率、保险许可 | 随保险法令 | 官方 |

## 实时查询示例（WebFetch prompt 模板）
- **汇率**：`WebFetch https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia` → "提取 USD、CNY、EUR 的买入价与卖出价(越南盾)及更新时间"
- **关税**：`WebFetch https://tariff.customs.gov.vn` → "查询 HS编码 [编码] 的进口关税、VAT、特别消费税与监管条件"
- **最新法规**：`WebFetch https://vbpl.vn/` → "查找 [编号如 67/2025/QH15] 的全文与生效日期"
- **税改中文**：`WebSearch site:chinatax.gov.cn 越南 税收 [关键词]`

详见 `realtime_sources.json`（机器可读版，含每条 query_method）。
