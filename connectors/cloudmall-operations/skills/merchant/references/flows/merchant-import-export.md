# 商户域 — Excel 导入导出流程（门店/组织/供应商/分类导航）

> 对应契约：`apis/merchant/store-query.md`（store.export）与 `store-action.md`（store.import）、`apis/merchant/org-action.md`（org.import）、`apis/merchant/supplier-query.md`（supplier.export）与 `supplier-action.md`（supplier.import）、`apis/merchant/category-nav-query.md`（category-nav.export）、`apis/merchant/channel-trace-query.md` / `channel-trace-action.md`（渠道追踪导入导出）；写操作共同纪律见 `merchant-core.md`。

**场景**：批量导出数据留存；批量导入建店/建组织/建供应商。

---

## 导出（返回预签名下载 URL）

1. 与用户确认导出范围（筛选条件）→
2. 调用对应导出能力：`ops.merchant.store.export`（条件同门店 search）、`ops.merchant.supplier.export`（条件同 supplier.search）、`ops.merchant.category-nav.export`（模板 ID）→
3. 响应 `downloadUrl` 为 **COS 预签名 URL（分钟级时效）**——立即完整转告用户让其尽快下载，不持久化、不当稳定链接。
4. ⚠️ 组织导出与自提点导出为**文件流响应**（当前执行链不支持），引导用户在管理后台操作。

## 导入（multipart 文件型）

1. 用户提出导入诉求 → 告知**模板获取路径**（管理后台对应模块「导入-下载模板」），或参考导出文件列结构 →
2. 用户把填好的 Excel **上传到对话/工作区**（Agent 通过文件型 capability 的 multipart file part 读取，本地路径不进结构化 input）→
3. 执行前复述：文件名、行数量级、目标模块与影响（导入是批量写）→
4. 调用导入能力：`ops.merchant.store.import`（≤500 行，服务端并发锁）、`ops.merchant.org.import`（≤10MB 同步）、`ops.merchant.supplier.import`（≤200 行）→
5. **结果处理（部分成功语义）**：
   - 供应商导入：响应含逐行明细 `failList[]`（rowIndex/name/errorMsg）——逐条报告失败原因；支持 .xlsx/.xls（.csv 会被后端拒绝，如实转述错误）；同租户并发导入有服务端锁（进行中会拒绝，稍后再试）；
   - 门店/组织导入：`successCount`/`failureCount` + `hasFailureDetail`——门店有失败明细时把 `failureDetailUrl`（预签名）转告用户下载修正；**组织导入的失败明细文件后端暂未生成（failureDetailUrl 恒为 null），失败数以 failureCount 为准**；
   - 门店/组织导入均为**同步执行**，`status` 通常为 null——**不要把 null 当「处理中」**，结果以计数为准，不引导用户去后台等待。
6. 导入失败修正后重导属**新文件新操作**，正常执行（每行独立事务，已成功行不会重复导入——以响应计数为准）。
