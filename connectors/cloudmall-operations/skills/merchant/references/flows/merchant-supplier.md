# 商户域 — 供应商审核与资料复核流程

> 对应契约：`apis/merchant/supplier-query.md`（分页/详情/草稿/字段配置）、`apis/merchant/supplier-action.md`（审核/分区保存/复核/OCR/字段配置/导入）；概念知识：`references/domains/merchant-concepts.md`，状态机见 `references/domains/merchant-enums.md`；写操作共同纪律与字段来源见 `merchant-core.md`。

**场景**：新供应商提交入驻申请后审核；已入驻供应商提交资料变更后复核；运营代供应商修正档案。

---

## 入驻审核

1. `ops.merchant.supplier.search`（auditStatus=pending）拿到待审核清单 →
2. `ops.merchant.supplier.detail`（id）看三分区完整档案（企个人资质、结算、OCR、bizSummary）→
3. 向用户复述审核结论（通过 / 驳回+原因）并确认 →
4. `ops.merchant.supplier.audit`（approve/reject；reject 必填 rejectReason；**idempotencyKey 幂等键必填**——16~128 位建议 UUID，同一审核操作的确认重提**复用同值**，用户改变决定后的新审核操作重新生成）→
5. 回读 detail 确认 `auditStatus` 已流转（**单向状态机，不可回退**）。

## 资料变更复核

1. `ops.merchant.supplier.search`（profileReviewOnly=true）或 detail 的 `profileReviews[]` 找到 `status=reviewing` 的变更单 →
2. 向用户展示 `diffFields[]`（改了什么：fieldName/before/after）→
3. 确认后 `ops.merchant.supplier.profile-review`（approve/reject + sectionKey；**enterprise 与 settlement 可能并行各一张**，多张时必须显式指定审哪张）→
4. 回读 detail 的 `profileReviews[]` 核验。

## 运营代改档案（分区保存）

1. `ops.merchant.supplier.draft.get`（id）确认无他人未提交草稿（有草稿先与用户确认是否覆盖/丢弃）→
2. `ops.merchant.supplier.update`（sectionKey + content 明文 + expectedVersion——version 来自 detail；contactRebindStatus=provisioning 时禁止编辑手机号）→
3. 回读 detail 核验；乐观锁冲突时重读 version 再来，不盲目重试。

营业执照识别：素材先上传素材库（material.upload）→ detail 确认 `licenseMaterialId` → `ops.merchant.supplier.license-ocr`（结果仅是编辑建议，未识别字段为 null 不得编造）。
