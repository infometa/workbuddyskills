# 会员子域 — 会员权益与成长值任务流程

> 对应契约：`apis/member/member-benefit-query.md` / `apis/member/member-benefit-action.md`（权益与成长加速）、`apis/member/growth-task-query.md` / `apis/member/growth-task-action.md`（成长值任务）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 会员权益管理

**场景**：成长加速/升级礼包两类固定权益的整体启停与成长加速配置；自定义权益的增删改/排序/图标/启停。

### 操作步骤（固定权益）

1. **看现态**：`ops.member.benefit.list`（固定 + 自定义统一返回，`fixed=true` 为固定权益行）+ `benefit.growth-accel-detail`（含 revision 与各等级配置）
2. **整体启停** 🔴：`benefit.status`（benefitType=GROWTH_ACCEL|UPGRADE_GIFT，body.globalEnabled；路径为 `status/{benefitType}`——benefitType 在 status 之后）——只切开关、保留配置。**关闭效果两类不同（按实现核验）**：GROWTH_ACCEL 关闭→成长加速停止计算（重新开启不追溯）；UPGRADE_GIFT 关闭→仅权益行展示口径，礼包发放实际由 `upgrade-gift.config-save` 全局开关 + 各等级 levelEnabled 门禁
3. **成长加速配置** 🔴：`benefit.growth-accel-save`
   - revision 必须来自最近一次 `growth-accel-detail` 的下发值（乐观锁，冲突需重新 detail 再提交）
   - levels 为**全量替换**：包含所有需要配置的等级；**未包含在 levels 中的等级其现有配置会被静默删除**（空 levels = 清除全部配置，危险操作，需用户明确确认）
   - 每等级 ≤5 组配置；倍率 1.0~9.9；SPECIFIED 范围至少一项
   - levelId 来自 `ops.member.level.list` 的等级 id
4. **核验**：回读 `growth-accel-detail`（revision 已 +1）

### 操作步骤（自定义权益）

1. **看列表**：`benefit.list`（`fixed=false` 的行为自定义权益；`levelIds` 为其关联等级）
2. **图标**：需要新图标时先 `benefit.upload-icon`（JPG/PNG ≤2MB）取回 `url`
3. **创建** 🔴：`benefit.create`——benefitName/iconUrl/levelIds 必填；benefitType 不传默认 CUSTOM（传固定类型值被服务端拒绝）
4. **编辑** 🔴：先读 `benefit.detail` 回填，`benefit.update`——levelIds 整体替换；固定权益被服务端拒绝通用编辑
5. **启停**：`benefit.status-by-id`（id + enabled 0/1）——自定义权益专用；固定权益启停走 `benefit.status`
6. **排序** 🔴：`benefit.sort`——应提交全部自定义权益 ID 的有序全集（不存在/重复报错；**漏传不报错但其排序值保持旧值不更新**，仍须提交全集）
7. **删除** 🔴：`benefit.delete`——不可逆；固定权益被服务端拒绝删除
8. **核验**：`benefit.list` / `benefit.detail` 回读

### 参数数据流

```
benefit.list 响应 id（fixed=false）→ detail / update / delete / status-by-id 路径参数
benefit.list 响应 levelIds / benefit.detail 响应 levelIds → update 回填（整体替换）
upload-icon 响应 url → create/update 的 iconUrl
level.list 响应 id → create/update 的 levelIds
```

### 异常处理
- revision 冲突：说明"配置已被他人更新"，重新 detail 后与用户确认再提交
- create/update 传 GROWTH_ACCEL/UPGRADE_GIFT 类型报错：固定权益由系统内置，说明限制并改走对应配置入口

## 成长值任务配置

**场景**：购买商品送成长值的比例配置。

### 操作步骤

1. **读现配置**：`ops.member.growth-task.list`（全量，当前仅 purchase 一条）
2. **保存** 🔴：`growth-task.save`——保存即生效、无审核；growthValue（每单成长值 1~9999）直接决定全租户升级速率与礼包触发，**数值必须用户明确给出**；tasks 为整体提交；已有任务带 taskId（原样保留；⚠️ taskId 无效时服务端静默跳过，保存后必须回读核验），taskConfig 结构 `{taskType:"purchase", perAmt:1, growthValue:100}`；perAmt 固定传 1（**回读的存量配置可能含历史默认值 perAmt=100，保存时必须改传 1，不能原样回传**——@Min(1)@Max(1) 硬校验）
3. **核验**：回读 `growth-task.list`
