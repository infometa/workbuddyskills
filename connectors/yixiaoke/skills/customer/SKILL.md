---
name: customer
description: 翼小客操作技能 - 客户全生命周期管理与 CRM 业务操作
version: "1.0.0"
author: "DMing"
---

# 翼小客 customer Skill

本 Skill 提供翼小客 CRM 的完整操作能力，覆盖客户管理、商机/订单/合同、审批/汇报、通话/微信/设备、组织架构等全链路场景。

## 工具一览

### 一、通用业务工具（meta 系列，覆盖 9 大业务模块）

#### 业务数据列表
查询各模块的数据列表。模板类模块（enterprise/customer/contract）留空 catId 时只返回模板列表供用户选择，选定后再带 catId 查询。
- **module 可选值**: approval(审批), business(商机), contract(合同), customer(联系人), enterprise(客户), order(订单), product(商品), product_file(商品档案), report(工作汇报)
- **参数**: module, catId, type, page, limit, keyword, body

#### 业务数据详情
查询单条业务数据详情。
- **module 可选值**: approval, business, contract, customer, enterprise, order, product, product_file, report
- **参数**: module, id

#### 业务数据保存
新增/编辑业务数据。模板类模块留空 catId 返回模板列表；带 catId 且 fields 留空返回字段预览；固定表单模块(business/order/product/product_file)用 body 透传。
- **module 可选值**: approval, business, contract, customer, enterprise, order, product, product_file, report
- **参数**: module, catId, id, fields, body

#### 业务筛选条件
获取模块支持的 conditions 字段和格式，用于构造复杂筛选。
- **module 可选值**: enterprise, customer, contract, order, product, product_file
- **参数**: module, catId

#### 业务数据导入（三步流程）
step=1 解析模板 → step=2 下载导入模板 → step=3 上传文件执行导入。
- **module 可选值**: customer(联系人), enterprise(客户), order(订单), product(商品)
- **参数**: module, step, catId, body

#### 业务数据导出
参数与业务数据列表对齐，支持复杂筛选。模板类模块需传 catId。
- **module 可选值**: approval, business, contract, customer, enterprise, order, product, report
- **参数**: module, catId, type, keyword, conditions, body

---

### 二、客户专属工具（customer 系列）

#### 客户查重
按客户名称/电话+模板查询是否已存在同名或同电话客户，新增客户前调用。catId 留空时先返回模板列表让用户选择。
- **参数**: catId, customerName, contactPhone, page, limit

#### 客户详情统计信息
查询某客户详情页各模块数量汇总（跟进记录数、商机数、订单数等）。
- **参数**: id

#### 客户详情操作
对客户执行操作：分配(allot)、公海领取(getsea)、退回公海(backsea)、转移公海(transfersea)。
- **参数**: action, cusIds, csIds, chsId, type, allotType, headSid, body

#### 客户设置标签
新增/移除/重置/清空客户标签，支持一次操作多个客户。catId 留空返回模板列表；labelIds 留空且非清空时返回可用标签列表。
- **参数**: catId, cusIds, batchType(1新增/2移除/3重置/4清空), labelIds, type, body

#### 修改客户跟进阶段
修改某客户的跟进阶段。cnId 留空时先返回可用阶段列表让用户选择。
- **参数**: id, cnId

#### 客户联系人信息
查看某客户下的联系人列表，支持按名称/电话/微信搜索。
- **参数**: id, keyword, page, limit

#### 客户社交信息
查看客户的微信/企微/WhatsApp/WaBusiness 好友信息。
- **参数**: id, csId, sourceType(2微信/3企微/4whatsapp/5WABusiness), page, limit

#### 客户跟进记录
action=list 查看跟进记录，action=add 新增跟进记录（需传 content、cusId）。
- **参数**: action, cusId, cusIdType, content, type, fType, cnId, linkmanId, bizId, nextTime, page, limit, body

#### 客户跟进计划
action=list 查看跟进计划，action=add 新增跟进计划（需传 title、content、followTime、cusIds）。
- **参数**: action, cusId, cusIds, cusIdType, title, content, followTime, pType, id, eType, type, page, limit, body

#### 客户AI信息
action=num 沟通总结数字，action=history 历史分析记录，action=detail 分析详情，action=execute 发起分析（需 followId）。
- **参数**: action, cusId, cusTypeId, followId, analysisId, categoryId, showTxt, page, limit

#### 客户crm信息
查看客户关联的商机(biz)、订单(order)、回款(repay)、成交商品(product)、流程(approval)、附件(file)。
- **参数**: type, id, bizId, keyword, from, ww_user_id, page, limit, body

---

### 三、渠道数据工具（channel 系列）

#### 网销数据查询
微信/企微/WhatsApp/WaBusiness 的好友/申请/重复/群/语音/员工查询。
- **channel**: wechat(微信/微聊), wework(企业微信), whatsapp(WhatsApp), wabusiness(WA商业版)
- **action**: staff(员工), friend(好友), repeat(重复好友), call(语音通话), group(群), apply(好友申请，仅wechat)
- **参数**: channel, action, body

#### 电销面销数据查询
通话记录、工牌录音、短信、通讯录查询。
- **channel**: call(通话记录), workcard(工牌录音), sms(短信), addrbook(通讯录)
- **action**: cussave(关联客户，仅call/workcard), query(我的查询), view(可查看查询，仅call/workcard), detail(详情，仅call)
- **参数**: channel, action, body

#### 设备信息查询
工作手机/工牌/分机查询与操作（绑定/锁定/重启/解绑等）。
- **channel**: phone(工作手机), workcard(工牌), call(分机)
- **action**: query(信息查询), change(设备绑定/换绑/分配), lock(锁定/解锁), logout(强制退出), restart(重启，仅phone), unbind(解绑，仅phone)
- **参数**: channel, action, body

#### 风控信息查询
财务统计、敏感操作统计、敏感词统计查询。
- **action**: moneyQuery(财务统计-查询), moneyInfo(财务统计-汇总), moneyType(财务统计-类型), moneyDetail(财务统计-明细), operateQuery(敏感操作统计), wordType(敏感词分类), wordQuery(敏感词查询)
- **参数**: action, body, page, limit

---

### 四、系统待办工具

#### 待办列表
查询当前登录人的系统待办列表（审批、跟进计划、抄送、通知等）。
- **sendType**: 空全部, 1需处理, 2需查看
- **sendSubType**: 1订单待审核, 2回款待审核, 3退款待审核, 4办公流程, 5跟进计划, 6抄送, 7通知
- **参数**: sendType, sendSubType, maxId, minId

#### 待办详情
查看某条待办审批的详情。id 从待办列表返回中获取。
- **参数**: id

#### 待办跟进计划
查看某条待办跟进计划的详情。id 从待办列表返回中获取。
- **参数**: id

---

### 五、组织架构工具

#### 通讯录
获取公司通讯录，部门员工列表（组织架构树）。isStaff=1 时返回员工；sourceType 可按业务线过滤（1客户 2crm 3电销 4微信 5工作汇报）。
- **参数**: isStaff, disabledType, sourceType

#### 员工名片
查看某个员工的个人信息/名片详情。id 为员工id，可从通讯录获取。
- **参数**: id

#### 员工工作信息
查看某个员工的工作数据（工作量、跟进、通话等）。id 为员工id，可从通讯录获取。
- **参数**: id

---

### 六、登录信息工具

#### 当前登录公司信息
获取当前登录的企业/商户/公司信息（公司名称、行业、版本、配置等）。
- **参数**: 无

#### 当前登录账号信息
获取当前登录人/账号/员工信息（姓名、员工id、部门、角色权限等）。
- **参数**: 无

## 注意事项

- 需要用户先完成 OAuth 授权后方可使用
- 如果 Token 过期，提示用户前往设置页重新授权
- 客户的列表/详情/保存统一走 `业务数据列表` / `业务数据详情` / `业务数据保存`(module=enterprise)，不使用独立的客户工具
- 模板类模块（enterprise/customer/contract）查询前需先让用户选择模板（catId 留空时只返回模板列表）
- 删除工具(meta_delete)暂未启用，各模块删除契约不同，待逐个验证后再放开