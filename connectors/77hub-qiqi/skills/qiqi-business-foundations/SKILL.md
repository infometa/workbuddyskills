---
name: qiqi-business-foundations
description: 企企服务业ERP业务语义与事实判断指南。需要理解产品能力域、档案、单据、主子表、项目型业财阶段、状态、引用、枚举和时间语义，校准利润、预算、任务或工时口径，或判断记录能否支持某项业务结论时使用。
description_zh: "提供企企服务业ERP的业务语义与事实判断指南，用于理解能力域、档案与单据、业财阶段、状态、引用和分析口径。"
description_en: "Provides business semantics and fact-evaluation guidance for 77Hub ERP, including capability domains, master data, documents, financial stages, statuses, references, and analysis bases."
version: "1.0.0"
author: "77Hub"
---

# 企企服务业ERP业务基础

企企服务业ERP（又称企企管理云）面向生产性服务企业，以项目型经营为重要主线，连接客户与合同、项目执行、收入与成本、收付款、财务核算和经营分析，形成可追溯的业财事实链。

产品能力域用于理解用户意图和寻找业务对象，不证明当前企业已经启用相关模块。当前企业实际可用的对象、字段、动作和权限必须由运行时确认。

## 权威事实原则

1. 先识别业务事实，再定位承载事实的对象和记录。名称相似、金额相同或日期相同都不能证明两条记录代表同一事实。
2. 区分档案、计划或预算、申请、合同或订单、执行、确认或结算、开票、收付款等阶段；不要用前一阶段替代后一阶段，也不要反向推断。
3. 区分主对象、明细、引用和关联集合。稳定 ID 用于证明记录身份，显示名称仅用于理解和候选消歧。
4. 区分记录状态与业务事实。状态说明记录处于什么阶段，不自动证明金额已经确认、开票、收付或结算。
5. 把产品稳定定义作为解释基础；把当前企业的对象、字段、枚举、权限和配置交给运行时元数据及返回事实确认。

## 事实判断框架

回答或行动前依次判断：

1. 用户关心哪个业务主体和业务阶段。
2. 目标是当前档案、计划口径、过程单据，还是已经发生或确认的结果。
3. 所需结论由哪些原始事实支持，哪些内容只是推导或建议。
4. 事实之间是否有可确认的记录引用、项目归属、业务期间或其它稳定关系。
5. 数据范围、权限和完整性是否足以支持结论；不足时明确未知，不把“没有查到”写成“没有发生”。

## 时间语义

业务上的自然日、精确时间点、一天中的时刻、自然月和自然年是不同语义。具体字段语义和外部格式必须由当前运行时元数据确认。

不要用创建时间替代业务日期，不用当天日期补齐用户未表达的业务日期，也不根据字段名称或实现经验猜测时间语义。

## 按需读取

- 需要理解企企的产品定位、主要能力域及跨域业务关系时，读取 [product-capability-map.md](references/product-capability-map.md)。
- 需要理解对象类别、主子表或状态生命周期时，读取 [business-model.md](references/business-model.md)。
- 需要理解项目型业财阶段和统计口径边界时，读取 [core-business-concepts.md](references/core-business-concepts.md)。
- 需要寻找标准对象候选时，读取 [standard-object-catalog.md](references/standard-object-catalog.md)。
- 需要理解公共字段、引用、枚举、空值或时间语义时，读取 [common-data-conventions.md](references/common-data-conventions.md)。

只读取当前任务需要的引用文件。
