# 平台、产品与参展服务

## 本企业与产品

- xiaoyuan_get_company_basic_info：本企业基本资料及订购展信息。
- xiaoyuan_list_goods：按产品名称、审核／正常／冻结等 goods_state 和页码查产品。
- xiaoyuan_get_product_tags：按真实税号读取产品标签。
- 需要更新企业画像、主图或产品手册时，转 company-profile.md；读取产品不等于修改产品。

## 展会资料与行动

- xiaoyuan_search_exhibitions：按名称、国家、行业、日期搜索展会库。
- xiaoyuan_search_exhibitors：按公司名查展商。
- xiaoyuan_get_his_exhibition：按税号查询国内／国际会刊参展历史。
- 参展指南、物流、搭建申请三类查询采用 api_references.md 中的 xiaoyuan_get_exhibition_guide / logistics / build_applications 工具组；各工具的实际完整名称以实时清单为准，不凭缩写拼造工具。
- xiaoyuan_get_exhibition_work_orders：按展会、工单号、关键词、order_state 查现场工单；状态包括已提交、解决中、无法解决、已解决、已关闭。
- 上述参展服务共用 page（从 1 开始）、limit（默认 20）、exhibition_id／exhibition_name。操作范围是查询，不能说已提交搭建申请、安排物流或创建工单。

## 站内通知与 RFQ 提醒

xiaoyuan_get_notice_list 读取 data.records，page_num 从 1，page_size 默认 10、最大 50；read_state=0 未读、1 已读，省略查全部。msg_type 支持：

| 值 | 通知类型 |
|---|---|
| 1 | 展会现场 |
| 2 | RFQ 推荐 |
| 3 | 买家到场 |
| 4 | 系统 |
| 5 | 物流 |
| 6 | 工单 |
| 7 | 参展指南 |

查看通知后可继续核对对应展会、买家或工单。通知列表不等于 WhatsApp 或邮件入站消息，RFQ 推荐也不等于已创建 AI 猎客任务。

## 平台与充值

平台控制台、企业 Key、Credit 查询、充值入口和到账后继续任务统一走 account-credit.md。用户问“充值”“平台余额”“点数不够”时直接进入该流程，不遗漏为泛化的连接排障。
