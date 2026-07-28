# 实体、来源与主张审计

## 为什么必须拆开对象

主体名字、网页、主张和任务验收不能塞进一张自由文本卡。按任务适用性分别维护：

- `EntityRecord`：涉及需消歧主体时，说明是谁；
- `SourceRecord`：来源是什么、实际读到了什么；
- `ClaimEvidenceLink`：哪条来源支持或反驳哪条主张；
- `KnowledgeRecord`：政策、案例、趋势或一般事实的可复用记录；
- `TaskAssessment`：哪些结构化交付要求已经满足。

非企业材料任务不要求 `EntityRecord`，也不创建虚假 `entityId`。

## 实体消歧

### 稳定键

先分别核实每个候选的法定主体与登记法域，再用已经验证、辖区适用且稳定的法人键去重。统一社会信用代码是中国境内主体的强键之一；其他法域使用当地适用的登记标识。缺少可验证登记标识时，可使用由独立公开证据共同绑定的规范法定全称与登记法域/注册地区组合。官网域名只作已验证归属后的辅助消歧，不是集团内法人合并键。

### 常见混淆

| 混淆 | 处理 |
|---|---|
| 品牌与法定主体 | 品牌作别名，找品牌权利/运营主体 |
| 集团与子公司 | 保留父子关系，按实际项目和用房主体计数 |
| 总部与基地 | 基地作为 operating base，不自动算新企业 |
| 项目公司与运营主体 | 分别建实体，记录关系和职责 |
| 同名公司 | 用注册地、信用代码、官网域名和业务交叉消歧 |
| 简称/旧称 | 记录 alias 和有效期 |

`resolved` 必须有至少一个可回读的身份来源。无法判断时使用 `ambiguous`，不要猜。

## 来源记录

每个来源必须记录：

```text
sourceId
url
title
publisher
sourceType
originSourceType（仅来路提示）
publisherResponsibility
publishedAt
retrievedAt
contentHash
locator
excerpt
readbackStatus
accessLimitation
freshnessStatus
```

`sourceType`、`originSourceType` 和兼容字段 `trustTier` 只用于记录来路或展示，不能决定证据是否充分。每条主张必须为每个 `evidenceRef` 记录一条 `sourceUsageAssessment`，按发布责任、司法辖区适用性、内容直接性、主体绑定和回读状态判断用途。发布责任、回读正文、最终 URL 和用途判断必须与受信工具或宿主回执闭合；业务 payload 只能提供待核输入，不能靠自填标签晋级。只有 `usageEligibility=standalone` 的关系记录可以单独过门；`corroborative` 只能补充，不得被任意固定成“必须两条来源”的全国统一规则。摘要、索引或不可回读内容因内容直接性和回读状态不足而只能作线索，与来源类别标签无关。

## 主张记录

把复合判断拆成可证伪主张。例如：

```text
不写：企业很适合园区

拆成：
- 企业主营某类产品
- 企业在某链节承担某角色
- 企业在本任务相关时间窗内出现某扩张信号
- 企业公开披露某研发/制造/载体需求
- 园区某资源可能解决其已知任务
```

每条主张绑定：

```text
taskContextRef
subjectRef / entityId（有真实主体时）
predicate
value / normalizedValue / valueType / unit
claimText
criticalityAssessment（从冻结规则引用派生）
validFrom / validTo
evidenceRefs[]
sourceUsageAssessments[]
entailment（由本次主张与回读内容的绑定判断）
freshnessStatus
conflictGroupId
alternativeExplanation
```

数值、集合、日期和定性规则只能按冻结判断规则的类型、操作符、单位与基准时点比较。字符串包含不等于集合成员，未知单位不能隐式换算，解析失败时返回 `unknown`。只有包含 `normalizedValue + normalization + criticalityAssessment` 且通过正式 Schema 的 Claim 才能参与机器判断；仅有旧 `value / typedValue / critical` 形状的记录最多作为迁移线索留档，不取得资格、排序、完成或行动判断权。兼容字段 `critical` 只可展示，不能决定资格；`criticalityAssessment.authorityRefs` 必须回连 `TaskGoal / ParkBrief`、身份或交付规则。

## 支持状态

| 状态 | 含义 | 可否过关键证据门 |
|---|---|---|
| `supports` | 来源直接支持主张 | 是，且来源可回读 |
| `partially_supports` | 只支持部分或间接支持 | 否，进入待核验 |
| `contradicts` | 来源明确反驳 | 否，并披露反证 |
| `unknown` | 无法判断 | 否 |

## 冲突

冲突不能“多数票”自动消失。记录：

- 哪些主张冲突；
- 来源时间、主体和权威性；
- 可能的口径/时点差异；
- 当前采用哪一解释及理由；
- 什么新证据会改变结论。

## 致命错误

以下任一出现即不能进入合格池：

- 错误法定主体；
- 同一法定主体重复计数；
- 注销/终止状态未披露；
- 关键主张引用无关主体；
- 关键来源不存在、不可回读或不支持主张；
- 把集团新闻直接归给未参与的子公司；
- 把历史项目写成当前扩张；
- 把公开联系方式写成确认决策人。

## 证据最小化

- 只摘录核验所需短句；
- 不聚合私人手机号、私人邮箱或敏感画像；
- 证据页面与行动入口分开；使用公开商务入口时绑定同一主体、建议渠道和具体用途，并标注“公开渠道，未核验是否适合触达”；
- 当前会话偏好和记忆不是企业事实证据。
