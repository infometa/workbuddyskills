---
name: "lingmao-scm-cloud-tools-reference"
description: "领猫 SCM Cloud Connector 全部工具参考 —— 按开放平台模块列出每个工具的用途与入参"
version: "1.0.1"
author: "领猫科技"
display_name: "领猫 SCM Cloud · 全部工具参考"
display_name_en: "Lingmao SCM Cloud · Tools Reference"
description_zh: "按开放平台模块列出全部工具的用途与入参，供查证工具名与参数形态时对照。"
description_en: "Reference of all tools grouped by open-platform module, with purpose and inputs."
---

# 领猫 SCM Cloud · 全部工具参考

本 Connector 共注册 **227 个开放平台端点工具**（分属 58 个模块）和 3 个不计配额的通用工具。**一个工具 = 一个开放平台接口**，工具名以 `op_` 开头。

> 实际会话里 `tools/list` 只返回**该授权勾选的模块**下的工具：未勾选的模块，其工具既不出现也调不动。本文件是全量参考；具体调哪个，以会话里 `tools/list` 实际返回的为准。

入参列：`*` 必填，`[]` 数组，`{}` 对象；字段级结构以 `tools/list` 返回的 `inputSchema` 为准。用途列末尾【读】为只读查询，【写】会创建或修改业务数据，调用前应向用户确认。

## 通用工具（任何授权都可用，不计配额）

| 工具 | 用途 | 入参 |
|---|---|---|
| `health` | 自描述诊断(不计配额)。 | 无 |
| `list_capabilities` | 返回**这把 Key 实际可用**的能力清单:已开通的开放平台模块与其下工具、未开通的模块(想用就拿这个名字去控制台勾)、以及按 17 阶段鞋服 SCM 业务链路聚合的覆盖情况。 | 无 |
| `ask_knowledge` | 查询领猫 SCM 业务功能知识库,回答系统里各业务菜单的业务规则问题:采购订单、生产分配、订单跟进、订单需求、成品/二次加工退货、销售通知,以及款式、物料、样品、客户、供应商、仓库等档案。 | question* |

## 个人认证接口（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_personal_certification_get_detail` | 获取个人认证详情【读】 | id, name, phone, certificateNumber, code, unionId |
| `op_personal_certification_get_list` | 分页查询个人认证【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 19 个 |
| `op_personal_certification_set_certification_status` | 设置个人认证的认证状态【写】 | ids[], certificationStatus, code, unionId, authFlowId, certificationThirdParty |

## 事件汇报（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_event_report_order_void` | 事件汇报--作废【写】 | ids[], codes[] |
| `op_event_report_order_get_event_report_detail` | 获取事件汇报详情【读】 | id, code, thirdCode, thirdSystem |
| `op_event_report_order_get_event_report_paged_list` | 获取事件汇报列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |
| `op_save_event_report_order_for_ai` | 保存事件汇报（简约入参）【写】 | status, eventReasonIds[], eventReasonNames[], remark, orderDate, attachmentUrls[], productInfo[], tagNames[], originOrderId, originOrderCode，…共 14 个 |

## 仓库（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_warehouse_archives_detail_by_id` | 根据Id获取仓库档案详情【读】 | id |
| `op_create_warehouse_archives` | 新增仓库列表【写】 | thirdCode, thirdSystem, code, name, status, warehouseAttribute, qualityType, isEnabledLocation, warehouseContacts, contactInformation，…共 13 个 |
| `op_page_query_warehouse_archives` | 分页查询仓库列表【读】 | pageIndex, pageSize, totalCount, searchKey, hasInvalidData |

## 付款单（5 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_payable_payment_detail` | 付款单-详情【读】 | id, code, thirdCode, thirdSystem |
| `op_payable_payment_update_status` | 付款单-批量更新状态【写】 | items*[] |
| `op_payable_payment_verification` | 付款单-核销【写】 | items*[] |
| `op_query_payable_payment` | 付款单-列表查询【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 18 个 |
| `op_payable_payment_set_external_order_num` | 设置外部单号【写】 | id, paymentNum, externalOrderNum |

## 企业认证（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_enterprise_certification_get_detail` | 获取企业认证详情【读】 | principalCompanyId, principalCompanyCode, principalCompanyName, certificationCode, unionId, authFlowId |
| `op_enterprise_certification_get_list` | 分页获取企业认证列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 17 个 |
| `op_enterprise_certification_set_certification_status` | 设置企业认证的认证状态【写】 | principalCompanyIds[], certificationCode, certificationStatus, unionId, authFlowId, sealManagementUrl, certificationThirdParty |

## 供应商（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_supplier_detail` | 获取供应商详情【读】 | id, code, thirdCode, thirdSystem |
| `op_supplier_page_list_query` | 供应商列表查询【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |
| `op_supplier_update_status` | 供应商状态批量更新接口【写】 | items*[] |

## 其他应收付（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_create_other_payable` | 其他应收付-创建【写】 | items*[] |
| `op_get_other_payable_detail` | 其他应收付-详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_other_payable_list_paged` | 其他应收付-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |
| `op_other_payable_update_status` | 其他应收付-批量更新状态【写】 | items*[] |

## 合同接口（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_contract_get_detail` | 获取合同详情【读】 | id, code, thirdPartyApprovalFlowCode, isGetNotSignedFile |
| `op_contract_get_list` | 分页合同列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |
| `op_set_contract_signing_status` | 设置合同的签署状态 只适合线上签署【写】 | operationType, contractSigningStatus, personalCertificationPhone, signatoryPartnerUnionId, signatoryDate, thirdPartyApprovalFlowId, thirdPartyApprovalFlowCode, thirdPartyApprovalFlowName, signedCompl… |

## 吊牌信息（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_product_tag_get_tag_detail_by_id` | 获取吊牌信息详情【读】 | tagId, productCode |
| `op_platfore_product_tag_pagination_query` | 吊牌信息——列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |

## 品类企划（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_inform_category_planning_category_planning_detail` | 获取品类企划详情【读】 | id, code, thirdCode, thirdSystem |
| `op_inform_category_planning_category_planning_page_query` | 获取品类企划列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 16 个 |

## 唯一码（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_paged_unique_code_from_batch` | 唯一码分页（根据批次号）【读】 | pageIndex, pageSize, totalCount, batchId, batchCode |

## 外部系统（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_add_external_system_data_log` | 添加外部系统数据对接日志【写】 | requestId, dataSnapshotId, isSuccess, invokeSystem, thirdPartySystem, requestUrl, requestBody, responseBody, extendedParameter, elapsedMilliseconds，…共 14 个 |

## 客户档案（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_batch_create_customer` | 批量新增客户信息【写】 | customers[] |
| `op_change_customer_status` | 变更客户信息状态【写】 | items*[] |
| `op_page_query_customers` | 分页查询客户信息【读】 | pageIndex, pageSize, totalCount |

## 对账单（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_payable_bill_detail` | 对账单-详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_payable_bill_list_paged` | 对账单-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |
| `op_payable_bill_update_status` | 对账单-批量更新状态【写】 | items*[] |
| `op_update_supplier_payable_bill_status` | 修改应付对账供应商对账状态并保存异常信息【写】 | billNum, supplierPayableBillStatusEnum, exceptionTypeName, exceptionDescription, attachmentUrls[] |

## 应付账单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_payable_list_paged` | 应付账单-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |
| `op_payable_detail` | 应付账单-详情【读】 | id, code, thirdCode, thirdSystem |

## 成品二次加工单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_secondary_processing_order_detail` | 获取成品二次加工单详情【读】 | id, code |
| `op_secondary_processing_order_list` | 获取成品二次加工单分页列表【读】 | pageIndex, pageSize, totalCount, ids[], codes[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, status[] |

## 成品二次加工退货单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_secondary_processing_return_order_detail` | 获取成品二次加工退货单详情【读】 | id, code |
| `op_secondary_processing_return_order_list` | 获取成品二次加工退货单分页列表【读】 | pageIndex, pageSize, totalCount, ids[], codes[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, status[] |

## 成品入库单（7 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_warehouse_in_order_detail_by_code` | 根据Code获取成品入库单详情【读】 | code |
| `op_get_warehouse_in_order_detail_by_id` | 根据Id获取成品入库单详情【读】 | id |
| `op_get_warehouse_in_order_detail_by_third_code` | 根据ThirdCode获取成品入库单详情【读】 | thirdCode, thirdSystem |
| `op_warehouse_in_batch_audit` | 批量审核/反审核【写】 | auditOption, auditName, ids[], codes[], apiCodes[], sysType |
| `op_warehouse_in_batch_cancel` | 批量作废【写】 | ids[], codes[], apiCodes[], sysType |
| `op_warehouse_in_batch_delete` | 批量删除【写】 | ids[], codes[], apiCodes[], sysType |
| `op_page_query_warehouse_in_order` | 分页查询成品入库单 列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |

## 成品出库单（5 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_warehouse_out_detail` | 获取出库单详情【读】 | apiCode, apiSystem, id, code |
| `op_warehouse_out_batch_audit` | 批量审核/反审核【写】 | auditOption, auditName, ids[], codes[], apiCodes[], sysType |
| `op_page_query_warehouse_out_order` | 分页查询成品出库单 列表【读】 | pageIndex, pageSize, totalCount, searchKey, lastModificationTimeStart, lastModificationTimeEnd |
| `op_warehouse_out_update_warehouse_order_return_status` | 更新出库单退货状态【写】 | codes[], ids[], sysType, warehouseOutReturnStatusEnum, quantity, exceptionType, reason, filePaths[] |
| `op_warehouse_out_order_by_jst_no_source` | 拉取聚水潭无来源出库单【写】 | id, code, creatorName, warehouseId, warehouseCode, warehouseName, supplierId, supplierName, supplierFullName, supplierCode，…共 34 个 |

## 成品质检单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_product_qc_detail` | 查询成品质检单明细【读】 | id, code, thirdCode, thirdSystem |
| `op_get_product_qc_list` | 查询成品质检单列表【读】 | pageIndex, pageSize, totalCount, ids[], codes[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, status[]，…共 15 个 |

## 成品退货单（7 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_warehouse_refund_batch_audit` | 批量审核/反审核【写】 | auditOption, auditName, ids[], codes[], apiCodes[], sysType |
| `op_warehouse_refund_batch_cancel` | 批量作废【写】 | ids[], codes[], apiCodes[], sysType |
| `op_warehouse_refund_batch_delete` | 批量删除【写】 | ids[], codes[], apiCodes[], sysType |
| `op_get_warehouse_refund_detail` | 查询退货单详情【读】 | apiCode, apiSystem, id, code |
| `op_warehouse_refund_list` | 分页查询成品退货单【读】 | pageIndex, pageSize, totalCount, businessOrderNums[], orginOrderNums[] |
| `op_warehouse_refund_warehouse_return_order_by_jst_no_source` | 拉取聚水潭无来源退货单【写】 | id, code, creatorName, accountingDate, orginOrderType, supplierId, supplierName, supplierFullName, supplierCode, supplierApiCode，…共 26 个 |
| `op_warehouse_refund_product_return_order_to_scm` | 变更供应商退货状态【写】 | refundOrderNo, status, quantity, exceptionType, reason, filePaths[] |

## 成品销售退货单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_sales_return_order_detail` | 查询成品销售退货单详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_sales_return_order_list_paged` | 查询成品销售退货单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 18 个 |

## 打样需求（8 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_proofing_order_detail` | 获取打样需求详情【读】 | id, code, thirdCode, thirdSystem |
| `op_proofing_order_page_query` | 获取打样需求列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 19 个 |
| `op_proofing_order_simple_detail` | 获取打样需求详情（简易版）【读】 | id, code, thirdCode, thirdSystem |
| `op_get_proofing_order_bom_share_link_by_sample_code` | 根据样衣编码获取打样需求 BOM 分享链接【读】 | sampleCode |
| `op_get_proofing_order_bom_data` | 获取打样需求-详情Bom数据【读】 | id, code, thirdCode, thirdSystem |
| `op_proofing_order_node_report` | 打样需求节点汇报【写】 | id, code, thirdCode, thirdSystem, poNodeId, nodeId, nodeName, nodeProgress, reportInfos[] |
| `op_proofing_order_save_pattern_attachment` | 保存打样需求-图样附件【写】 | thirdCode, thirdSystem, syncMsg, id, proofingCode, patternAttachmentRemark, fileUrls[] |
| `op_update_proofing_order_oms_status` | 更新打样单打样状态【写】 | thirdCode, thirdSystem, syncMsg, id, proofingCode, linkOMSProofingStatus, filePaths[] |

## 批量打标（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_common_save_document_mark` | 批量打标【写】 | items*[] |

## 数据字典（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_plateform_basic_data_tree` | 获取树结构的数据字典【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |
| `op_basic_data_create_size_group` | 批量新增尺码组【写】 | batchAddTrees[] |
| `op_basic_data_page_list` | 列表查询【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 16 个 |

## 样衣（7 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_page_query_research_archive` | 获取样衣列表【读】 | pageIndex, pageSize, totalCount, searchType, searchKey, isProof, isEnable, internalAuditProductCount, researchArchiveCode, researchArchiveCodes[]，…共 14 个 |
| `op_page_query_research_archive_inquiry` | 获取款式询价单列表【读】 | pageIndex, pageSize, totalCount, inquiryIds[], inquiryCodes[], inquiryStatus[], quotationStatus[] |
| `op_page_query_research_archive_quotation` | 获取款式报价单列表【读】 | pageIndex, pageSize, totalCount, quotationIds[], quotationCodes[], quotationStatus[] |
| `op_research_archive_detail` | 获取样衣详情【读】 | id, code, thirdCode, thirdSystem |
| `op_research_archive_inquiry_detail` | 获取款式询价单详情【读】 | id, code, thirdCode, thirdSystem |
| `op_research_archive_quotation_detail` | 获取款式报价单详情【读】 | id, code, thirdCode, thirdSystem |
| `op_research_archive_sample_turn_to_big_goods` | 样衣转大货【写】 | items*[] |

## 样衣出入库（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_sample_warehouse_in_out_order_detail` | 样衣出入库-详情查询【读】 | id, code, thirdCode, thirdSystem |
| `op_sample_warehouse_in_out_order_batch_audit` | 样衣出入库-批量审核/反审核【写】 | auditOption, auditName, ids[], codes[], apiCodes[], sysType |
| `op_sample_warehouse_in_out_order` | 样衣出入库-列表查询【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |

## 样衣图库（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_sample_library_detail` | 获取样衣图库详情【读】 | id, code, thirdCode, thirdSystem |
| `op_sample_library_page_query` | 获取样衣图库列表【读】 | pageIndex, pageSize, totalCount, categoryPlanningIds[], status, lastModificationTimeStart, lastModificationTimeEnd |

## 款式档案（6 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_product_detail` | 获取款式详情【读】 | id, code, thirdCode, thirdSystem |
| `op_product_get_standard_info_package_print_link` | 根据款号获取标准资料包打印链接【读】 | productCode |
| `op_product_third_attributes_page_query` | 获取款式第三方关联信息【读】 | pageIndex, pageSize, totalCount, productCode, productCodes[], skuCode, skuCodes[], storeName, storeNames[], fnskuCode，…共 16 个 |
| `op_save_product_info` | 保存商品信息(新增、编辑)【写】 | id, productCode, productName, imgId, imgUrl, imgIds[], imgUrls[], relevanceArchives, archivesSuffix, archivesSuffixCode，…共 115 个 |
| `op_page_query_products` | 款式档案分页查询【读】 | pageIndex, pageSize, totalCount, sorting, isQueryList, standardPackageId, productId, productCode, productCodes[], skuCode，…共 17 个 |
| `op_set_product_sku_sync_status` | 批量设置款式SKU同步状态【写】 | items*[] |

## 正品调拨单（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_warehouse_certified_change_detail` | 获取正品调拨单详情【读】 | apiCode, apiSystem, id |
| `op_change_warehouse_certified_change_status` | 修改正品调拨单状态【写】 | code, thirdCode, thirdSystem, status, accountStatus, accountDate, operator |
| `op_page_query_warehouse_certified_change` | 分页查询正品调拨单列表【读】 | pageIndex, pageSize, totalCount, searchKey |

## 物料入库单（8 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_material_warehouse_in_order_batch_approval` | 批量审核物料入库单【写】 | ids[], codes[], apiCodes[], sysType |
| `op_material_warehouse_in_order_batch_cancel` | 批量作废物料入库单【写】 | ids[], codes[], apiCodes[], sysType |
| `op_material_warehouse_in_order_batch_de_approval` | 批量反审核物料入库单【写】 | ids[], codes[], apiCodes[], sysType |
| `op_get_material_warehouse_in_order_detail_by_code` | 根据Code获取物料入库单详情【读】 | code |
| `op_get_material_warehouse_in_order_detail_by_id` | 根据Id获取物料入库单详情【读】 | id |
| `op_get_material_warehouse_in_order_detail_by_third_code` | 根据ThirdCode获取物料入库单详情【读】 | thirdCode, thirdSystem |
| `op_page_query_material_warehouse_in_order` | 物料入库单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |
| `op_save_material_warehouse_in_order_with_patch` | 保存物料入库单【写】 | id, code, thirdCode, thirdSystem, warehouseInOrderTypeId, warehouseInOrderTypeCode, warehouseInOrderTypeName, warehouseId, warehouseCode, warehouseName，…共 27 个 |

## 物料出库单（8 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_material_warehouse_out_order_batch_approval` | 批量审核物料出库单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_material_warehouse_out_order_batch_cancel` | 批量作废物料出库单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_material_warehouse_out_order_batch_de_approval` | 批量反审核物料出库单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_get_material_warehouse_out_order_detail_by_code` | 根据Code获取物料出库单详情【读】 | code |
| `op_get_material_warehouse_out_order_detail_by_id` | 根据Id获取物料出库单详情【读】 | id |
| `op_get_material_warehouse_out_order_detail_by_third_code` | 根据ThirdCode获取物料出库单详情【读】 | thirdCode, thirdSystem |
| `op_page_query_material_warehouse_out_order` | 物料出库单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |
| `op_save_material_warehouse_out_order_with_patch` | 保存物料出库单 以补丁方式保存物料出库单；已有明细未传来源字段时保留历史来源链， 新增或变更来源时可省略来源明细 Id，由服务按物料/SKU 等业务编码唯一匹配，并支持主单标签累…【写】 | code, thirdCode, thirdSystem, id, isAudit, warehouseOutOrderTypeId, warehouseOutOrderTypeCode, warehouseOutOrderTypeName, accountingDate, supplierId，…共 26 个 |

## 物料库存（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_warehouse_inventory_paged` | 分页查询物料库存【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 29 个 |

## 物料收货单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_receive_detail` | 物料收货单-详情【读】 | apiCode, apiSystem, id, code |
| `op_page_query_material_receive` | 物料收货单-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |

## 物料档案（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_other_material_detail_material_archive` | 明细查询【读】 | id, code, thirdCode, thirdSystem |
| `op_other_material_list_material_archive` | 列表查询【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |

## 物料直发单（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_delivery_detail` | 获取物料直发单详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_material_delivery_list` | 获取物料直发单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |
| `op_material_delivery_receive` | 物料直发收货【写】 | datas[] |

## 物料码单（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_save_material_code_list` | 创建物料码单-新增(增量更新)【写】 | sourceOrderType, sourceOrderId, sourceOrderCode, items[] |

## 物料采购单（6 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_purchase_order_detail` | 获取物料采购单信息【读】 | Id, Code, ThirdCocde, ThirdName, ParameterCheck, IsThird |
| `op_ai_save_material_purchase_order` | AI保存物料采购单（简约入参）【写】 | originOrderType, originOrderIds[], originOrderCodes[], isCopied, isDeductOriginalOrder, originalOrderCode, status, purchaseTypeId, purchaseTypeCode, purchaseTypeName，…共 60 个 |
| `op_batch_audit_material_purchase_order` | 批量审核/反审核物料采购单【写】 | materialPurchaseOrderIds[], apiCodes[], codes[], sysType, operate |
| `op_batch_case_closed_material_purchase_order` | 批量结案/反结案物料采购单【写】 | materialPurchaseOrderIds[], apiCodes[], codes[], sysType, materialPurchaseOrderSkuIds[], operate |
| `op_batch_void_material_purchase_order` | 批量作废物料采购单【写】 | materialPurchaseOrderIds[], apiCodes[], codes[], sysType |
| `op_get_material_purchase_order_list_paged` | 第三方-获取物料采购单列表-分页【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 19 个 |

## 物料采购计划（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_material_purchase_plan_page_list_query` | 获取物料采购计划列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |

## 物料采购退货单（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_batch_void_material_purchase_refund` | 批量作废物料采购退货单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_get_material_purchase_refund_detail` | 获取物料采购退货单详情【读】 | Id, Code, ThirdCode, ThirdSystem |
| `op_get_material_purchase_refund_list_paged` | 获取物料采购退货单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 16 个 |

## 物料销售单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_sales_order_detail` | 查询物料销售单详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_material_sales_order_list_paged` | 查询物料销售单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 17 个 |

## 物料销售退货单（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_sales_return_order_detail` | 查询物料销售退货单详情【读】 | Id, Code, ThirdCode, ThirdSystem |
| `op_get_material_sales_return_order_list_paged` | 查询物料销售退货单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 18 个 |

## 物料领料单（8 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_material_requisition_order_detail_by_code` | 根据Code获取物料领料单详情【读】 | code |
| `op_get_material_requisition_order_detail_by_id` | 根据Id获取物料领料单详情【读】 | id |
| `op_get_material_requisition_order_detail_by_third_code` | 根据ThirdCode获取物料领料单详情【读】 | thirdCode, thirdSystem |
| `op_material_requisition_batch_approval` | 批量审核物料领料单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_material_requisition_batch_cancel` | 批量作废物料领料单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_material_requisition_batch_de_approval` | 批量反审核物料领料单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_material_requisition_page_query_material_requsition_order` | 物料领料单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |
| `op_patch_save_material_requisition` | 保存物料领料单【写】 | businessType, originOrderId, originOrderCode, purchaseOrderId, purchaseOrderCode, calculationMethod, nodeId, requisitionDate, followerTeamId, followerTeamCode，…共 37 个 |

## 理化检测（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_physical_qc_package_list_sync` | 同步检测套餐【写】 | supplierCode, data[] |
| `op_physical_qc_standard_item_sync` | 同步检测项目【写】 | supplierCode, data[], sId, levelId |
| `op_physical_qc_standard_levels_sync` | 同步检测等级【写】 | supplierCode, data[] |
| `op_physical_qc_standard_list_sync` | 同步检测标准【写】 | supplierCode, data[] |

## 理化质检（2 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_physical_qc_get_physical_detail` | 获取理化质检单明细数据【读】 | id, code |
| `op_update_physical_qc_item_result` | 更新理化质检单明细结果和判定状态【写】 | apiCode, apiSystem, id, code, productCodes[], physicalQcProjectItem[], filePaths[], fileName, detectingComponents |

## 生产跟进（11 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_order_follow_up_detail` | 查询单个订单跟进详情【读】 | id |
| `op_get_party_order_follow_up_detail` | 第三方-查询订单跟进详情【读】 | ids[], apiSystem |
| `op_order_follow_up_create_report_exception` | 新增异常记录【写】 | apiCode, apiSystem, purchaseOrderCode, productCode, nodeName, nodeCode, exceptionType, exceptionReason, filePaths[], creatorName |
| `op_order_follow_up_delete_report_exception` | 第三方-删除异常【写】 | apiCode, apiSystem, orderFollowUpId, id |
| `op_order_follow_up_delete_reporting_record` | 第三方-删除汇报记录【写】 | apiCode, apiSystem, orderFollowUpId, id |
| `op_get_order_follow_up_exception_record` | 第三方-查询生成节点异常汇报信息【读】 | exceptionRecordId, apiCode, apiSystem |
| `op_order_follow_up_get_production_plans` | 获取生产计划信息【读】 | apiCode, apiSystem, id, purchaseOrderCode, productCode |
| `op_order_follow_up_report_progress` | 第三方-进度汇报【写】 | apiCode, apiSystem, purchaseOrderCode, nodeId, nodeName, nodeCode, productCode, reportTime, totalQuantity, isFinish，…共 14 个 |
| `op_order_follow_up_report_progress_save_ext_sys_key_map` | 第三方-生产订单跟进节点保存外部单号【写】 | orderId, orderCode, productCode, nodes[] |
| `op_order_follow_up_solve_exception` | 第三方-解决异常【写】 | apiCode, apiSystem, orderFollowUpId, id, solverName |
| `op_thrid_party_page_query_order_follow_ups` | 第三方-订单跟进列表查询【读】 | pageIndex, pageSize, totalCount, isContainDelayNodeOrder, delayNodeId, planCompleteStatus[], nodeIds[], isShowClosedOrder, hasException, isLinkOMS，…共 14 个 |

## 用户接口（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_user_query_list` | 分页查询用户信息【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |

## 表单（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_platformform_get_by_form_key` | 获取表单信息【读】 | formKey |

## 装箱计划单（11 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_packing_plan_order_appservice_batch_completed_packing` | 扫码装箱-完成装箱【写】 | cartonBarCodes[] |
| `op_packing_plan_order_appservice_batch_fast_completed_packing` | 扫码装箱-快速装箱【写】 | cartonBarCodes[] |
| `op_packing_plan_order_appservice_batch_void_packing` | 扫码装箱-作废【写】 | cartonBarCodes[] |
| `op_packing_plan_order_appservice_get_carton_segment_paged` | 获取装箱计划详情 总表-箱段【读】 | id |
| `op_packing_plan_order_appservice_get_carton_segment_to_cartion` | 根据箱段获取箱子的信息 获取扫码装箱详情 箱段-箱子【读】 | cartonSegmentId |
| `op_packing_plan_order_appservice_get_packing_plan_itemby_cartion` | 获取单个计划单下的所有箱段和箱子信息【读】 | packingPlanOrderId |
| `op_packing_plan_order_appservice_get_packing_sku_by_carton` | 获取单箱的装箱明细 扫码装箱获取详情 箱子-小箱子-sku【读】 | cartonId |
| `op_packing_plan_order_appservice_get_paged` | 分页获取装箱计划单【读】 | search, codes[] |
| `op_packing_plan_order_appservice_get_scan_packing_paged` | 分页获取扫码装箱(装箱计划的箱段维度)【读】 | pageIndex, pageSize, totalCount, globalQuery{}, filterQuery{}, groupQuery{}, tableQuery{}, fuzzyQuery{}, sorting, conditionGroups[]，…共 11 个 |
| `op_packing_plan_order_appservice_save` | 新增装箱计划【写】 | code, originOrderType, productType, orderDate, packingStatus, externalOrderCode, deliveryAddress, logisticsCompany, logisticsCode, contact，…共 12 个 |
| `op_packing_plan_order_appservice_void` | 作废装箱计划单【写】 | codes[], externalOrderCodes[] |

## 订单需求（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_order_demand_info` | 获取订单需求信息【读】 | id, code, thirdCocde, thirdName, parameterCheck, isThird |
| `op_batch_audit_order_demand` | 批量审核/反审核订单需求【写】 | orderIds[], apiCodes[], codes[], sysType, operate |
| `op_create_order_demand` | 新增订单需求【写】 | id, code, thirdCode, thirdSystem, followMans[], productionType, customerId, customerCode, customerName, warehouseId，…共 23 个 |
| `op_order_demand_pagination_query` | 订单需求列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 14 个 |

## 设计任务（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_design_task_paged` | 获取设计任务列表【读】 | categoryPlanningCodes[], categoryPlanningNames[], pageIndex, pageSize, totalCount |

## 调价单（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_ai_save_payable_adjust` | 调价单保存（简约入参）【写】 | items*[] |
| `op_get_payable_adjust_detail` | 调价单-详情【读】 | id, code, thirdCode, thirdSystem |
| `op_get_payable_adjust_list_paged` | 调价单-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 15 个 |

## 资料包（10 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_information_package_package_info` | 获取资料包数据(旧)【读】 | id, purchaseOrderCode, productCode, productId, supplierId, extSysKeyMap{} |
| `op_information_package_get_standard_package_bom_data` | 获取标准资料包Bom数据（物料清单）【读】 | productCode |
| `op_information_package_batch_standard_package_audit` | 批量审核/反审核标准资料包【写】 | items*[] |
| `op_information_package_batch_standard_package_lock` | 批量锁定/解锁标准资料包对应的页签数据【写】 | items*[] |
| `op_information_package_get_info_package_bom_data` | 获取标准资料包-详情Bom数据【读】 | id, code, nuclearPriceListId |
| `op_information_package_get_info_package_nuclear_price_list_data` | 获取标准资料包-核价清单数据【读】 | id, code, nuclearPriceListId |
| `op_information_package_get_nuclear_price_list_id_and_name` | 获取标准资料包-核价清单Id和名称【读】 | linkId, productId, productCode |
| `op_information_package_info_package_list_paged` | 获取标准资料包数据-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 18 个 |
| `op_information_package_production_package_list_paged` | 获取生产资料包数据-列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 20 个 |
| `op_information_package_get_production_package_bom_data` | 获取生产资料包-详情Bom数据【读】 | id, code, nuclearPriceListId |

## 采购单（12 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_purchase_order_detail_by_code` | 通过code获取采购单详情【读】 | purchaseOrderCode |
| `op_purchase_order_get_product_sku_inventory` | 款式使用情况查询【读】 | productCodes[], skuCodes[], nodeName |
| `op_get_purchase_order_warehouse_info_data` | 获取采购单交期和首次入库比例获取采购单信息【读】 | day, proportion, isCut |
| `op_ai_save_purchase_order` | AI保存成品采购单（简约入参）【写】 | status, currencyId, currencyCode, currencyName, exchangeRate, productionType, depotId, depotCode, depotName, purchaseManList[]，…共 54 个 |
| `op_get_purchase_order_material_progress` | 获取采购单物料进度【读】 | PurchaseOrderId, PurchaseOrderCode, ThirdCode, ThirdSystem, ProductId, ProductCode |
| `op_purchase_order_batch_audit` | 批量审核/反审核【写】 | orderIds[], operate, apiCodes[], codes[], sysType, approvalManId, approvalMan |
| `op_purchase_order_batch_case_closed` | 批量结案/反结案【写】 | purchaseOrderIds[], apiCodes[], codes[], sysType, operate |
| `op_purchase_order_batch_void` | 批量作废【写】 | purchaseOrderIds[], apiCodes[], codes[], sysType |
| `op_get_purchase_order_list_detail_by_product_list` | 通过款式id集合，批量获取已协同采购单列表的详情-到款（按供应商分组）【读】 | items*[] |
| `op_get_purchase_order_list_paged` | 第三方-获取采购单列表-分页【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 18 个 |
| `op_purchase_order_get_share_bom_url` | 第三方-获取第三方分享的BOM链接请求【读】 | purchaseOrderId, isInCludeDeleted, productId, shareToken, siteOrigin |
| `op_update_receive_purchase_order_status` | 第三方-修改接单状态【写】 | apiCode, apiSystem, purchaseOrderCode, receiveOrderStatus, receiveDate, refusedReason |

## 销售订单（4 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_audit_sales_order` | 审核/反审核销售订单【写】 | orderIds[], operate, apiCodes[], codes[], sysType, approvalManId, approvalMan |
| `op_create_sales_order` | 新增销售订单【写】 | id, code, thirdCode, thirdSystem, createTime, warehouseId, warehouseCode, warehouseName, customId, customName，…共 30 个 |
| `op_get_sales_order_detail` | 查询销售订单详情【读】 | id, code, thirdCocde, thirdName, parameterCheck, isThird |
| `op_get_sales_order_list_paged` | 查询销售订单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 17 个 |

## 销售通知单（3 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_sales_notification_batch_anti_audit` | 批量反审核销售通知单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_sales_notification_batch_audit` | 批量审核销售通知单【写】 | ids[], codes[], thirdCodes[], thirdSystem |
| `op_sales_notification_batch_delete` | 批量删除销售通知单【写】 | ids[], codes[], thirdCodes[], thirdSystem |

## 预约单（9 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_get_warehouse_schedule_order` | 查询预约单详情（包含预约单各种状态信息和审批驳回信息）【读】 | apiCode, apiSystem, id, code |
| `op_get_warehouse_schedule_order_in_storage_sku_received_quantity` | 查询预约单入库sku入库数量【读】 | apiCode, apiSystem, inOrderId, originOrderType |
| `op_get_warehouse_schedule_order_list` | 查询预约单列表【读】 | pageIndex, pageSize, codes[], names[], createTimeBegin, createTimeEnd, modifyTimeBegin, modifyTimeEnd, trackTimeBegin, trackTimeEnd，…共 13 个 |
| `op_get_warehouse_schedule_order_packed_detail` | 查询预约单装箱明细【读】 | apiCode, apiSystem, id, code |
| `op_get_warehouse_schedule_order_to_product` | 查询预约单详情（包含预约单各种状态信息和审批驳回信息及款维度信息）【读】 | apiCode, apiSystem, id, code |
| `op_warehouse_schedule_batch_audit` | 批量审核/反审核【写】 | ids[], operate, apiCodes[], codes[], sysType |
| `op_save_warehouse_schedule_order_with_patch` | 保存预约单【写】 | id, code, thirdCode, thirdSystem, distinguishOrderType, scheduleOrderType, reservationMethod, purchaseOrderCodes[], allocationRule, scheduleTime，…共 32 个 |
| `op_share_create_warehouse_schedule_order` | 按sku采购数量分摊逻辑创建预约单(支持多采购单，仅创建)【写】 | apiCode, apiSystem, creatorName, receiveWarehouseCode, allocationRule, scheduledType, reservationMethod, remark, items[] |
| `op_warehouse_schedule_void` | 作废预约单【写】 | apiCode, sysType, orderId, orderCode |

## 颜色（1 个）

| 工具 | 用途 | 入参 |
|---|---|---|
| `op_page_query_color` | 分页查询颜色信息【读】 | codes[], names[], status |

