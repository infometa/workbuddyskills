---
name: xinhua-industry-data
description: 中经社产业数据服务。当用户需要查询中国境内的企业工商信息、股东与董监高、司法与经营风险、知识产权、公告研报、舆情、招投标、创投融资与产业基金、产业链评价、政策文件、人物任职持股等数据时使用。
version: 1.0.0
---

# 中经社产业数据（MCP）

以标准 MCP 协议，将企业、产业、人物、投融资等数据能力封装为 AI 可直接调用的数据工具。

## 接入配置

- 服务地址（聚合入口，一个地址访问全部工具）：`https://openapi-xhzjds.cnfic.com.cn/mcp-gateway/mcp`
- 鉴权方式：Bearer Token
- 获取凭证：用户在中经社行业洞察AI数据开放平台注册后，于「API Key」页生成 Key，粘贴到本连接器配置中
- Key 分两类：试用Key（消耗积分，注册即送额度）/ 正式Key（消耗合同次数配额）。两类 Key 的使用方法完全一致，仅计费轨道不同

## 能力边界（能查什么 / 暂不能查什么）

**能查**：企业工商与全维信息（股东/董监高/融资/风险/知产/公告/研报/舆情/招投标）、企业关系网络图谱、人物任职持股与商业伙伴、产业链节点检索与区域评价、创投融资事件与产业基金（含LP与退出）、国家及地方政策文件。

**暂不能查**（用户问到时如实说明能力未开放，不要硬调工具）：
- 产业园区维度数据（园区内企业名单等）
- 产业链上下游关系明细（链路径可经 `get_industry_detail` 获取，但上下游企业级关系暂无）
- 境外企业数据
- 实时股价/行情类数据

## 调用策略（重要）

### 名称模糊时：先识别，再查询
用户给的名称不标准（简称、错别字、旧名）时，**先调主体识别工具做标准化**，拿到标准名称/编号后再调详情类工具：

| 用户给的模糊对象 | 先调 | 再调 |
| --- | --- | --- |
| 企业（简称/别称） | `search_enterprise_by_name`（返回工商全称+信用代码+候选列表） | 企业类工具（入参 `company_name` 用工商全称） |
| 人物（重名常见） | `search_person_by_name`（返回人物编号+角色分布） | 人物类工具（入参 `person_no`） |
| 产业（口语说法） | `get_industry_tree`（返回产业节点代码+所属路径） | 产业类工具（入参 `industry_code`） |
| 地区（口语说法） | `get_region_tree`（返回行政区划编码） | 区域类工具（入参 `region_code`） |

注意：人物重名多，识别后**优先选关联角色最多的那位**；拿不准时在回答中说明识别结果并请用户确认。

### 常见组合场景
- **企业全景画像**：主体识别 → 工商信息（`get_enterprise_basic`）+ 股东（`get_enterprise_shareholders`）+ 董监高（`get_enterprise_management`）+ 标签（`get_enterprise_tags`），按需加风险（`get_enterprise_business_risk` / `get_enterprise_judicial_risk`）
- **企业关系网络**：`get_company_graphy` 一次拉取对外投资/供应商/客户/股东/高管等关系；融资关系网络用 `get_businessFinance_graphy`
- **产业链分析**：先 `get_industry_tree` 定位节点 → `get_industry_detail`（简介与链路径）→ `get_industry_evaluation`（区域评价）/ `get_industry_company_portrait`（企业画像）/ `get_industry_financial`（财务）/ `get_industry_innovation`（创新）
- **投融资调研**：`search_financing_companies` 扫近期早期获投事件 → `get_enterprise_VCPE_financing` 等企业融资明细 → 基金侧用 `get_industryFund_list` / `get_fund_detail_basic` / `get_fund_detail_investment_list` / `get_fund_detail_exit_list`；竞品融资对比用 `get_query_competitive_Finance`
- **人物背景**：`search_person_by_name` 识别 → `get_talent_basic`（简介）+ `get_person_legal` / `get_person_office` / `get_person_controller` / `get_person_holder` / `get_person_union` / `get_person_partner`

### 出参说明
- 出参为中文字段名、扁平结构，可直接组织为回答
- 列表类出参含「总数」与「列表」字段；部分工具直接返回关键字段（如主体识别返回「企业名称」「企业统一社会信用代码」）
- 出参外层可能带"提示"字段（如积分余额不足20%的提醒）——**如存在提示，请原样转达给用户，不要改写**

## 错误处理

| 状态码 | 含义 | 处理方式 |
| --- | --- | --- |
| 401 | Key无效或已失效 | 引导用户到平台「API Key」页检查或重新生成 |
| 402 | 试用积分不足 | 引导用户回平台账户页查看（中性提示，不含销售联系方式） |
| 403 | 该工具不在已购范围内 | 说明当前账号未购买此工具，可调整查询范围 |
| 429 | 并发或周期配额超限 | 稍后重试；提示用户配额刷新时间（24h配额每日0点、每周配额每周一00:00刷新） |
| 500 | 服务内部异常 | 稍后重试；持续失败时引导用户到平台查看服务健康状态 |

## 注意

- 不要在回答中编造本平台未返回的数据；数据缺失时如实说明
- 不要主动向用户推销或引导付费；涉及额度不足时使用平台返回的中性提示口径
