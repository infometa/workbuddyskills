# 会员子域 — 反馈/客服/分享链接流程

> 对应契约：`apis/member/feedback-query.md` / `apis/member/feedback-action.md`（反馈）、`apis/member/customer-service-query.md` / `apis/member/customer-service-action.md`（客服开关）、`apis/member/wx-share-action.md`（微信分享三件套）；概念知识：`references/domains/member-concepts.md`，状态与枚举：`references/domains/member-enums.md`；写操作共同纪律（风险档位/超时不重试）见入口 Skill 护栏段。

## 反馈处理

**场景**：处理用户意见反馈。

### 操作步骤

1. **看列表**：`ops.member.feedback.search`（类型/手机号/状态/时间筛选；status=0 待处理）
2. **处理**：`ops.member.feedback.handle`——handleRemark 必填 ≤300 字（处理结论先向用户复述）
3. **核验**：回读 search（status=1）；已处理为终态，不可再变更

## 客服配置

**场景**：小程序在线客服开关。

### 操作步骤

1. `ops.member.customer-service.config`（读）→ `customer-service.config-save`（enabled 布尔）

## 分享链接生成

**场景**：为运营物料生成小程序跳转链接。

### 操作步骤

1. **短链**（仅微信内可用）：`ops.member.wx-share.short-link`——pageUrl（小程序页面路径）+ params（拼接到路径后，如 `channel=xxx`）必填
2. **URL Link**（微信外短信/邮件可用）：`ops.member.wx-share.url-link`——path 必填，query 可选
3. **太阳码**（扫码直达小程序）：⛔ **当前未对 Agent 开放（调用会被确定性拒绝），不要调用；用户要太阳码时，说明请到管理后台「微信分享」生成并下载，或改用短链 / URL Link**。契约参考（重新开放后适用）：`ops.member.wx-share.qrcode`——pageUrl（不能带参数）+ params（≤500 字符）必填；返回 base64 data URL（非 COS 链接），按运行时能力以图片形式交付，不要整段 base64 刷屏
4. envVersion 默认 release（生产投放必须 release）；生成失败多为租户小程序未配置，如实转达错误
