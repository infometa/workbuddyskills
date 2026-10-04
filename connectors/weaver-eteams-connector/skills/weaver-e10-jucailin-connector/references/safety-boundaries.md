# 能力边界与禁止项

## 招聘：写操作走 prepare→apply，撤销类禁用

招聘**读操作**已可用（人才搜索、业务列表、人才详情卡片），用法见 [`recruit-read.md`](recruit-read.md)。

招聘**写操作**已实现五个（新建人才、安排面试、发送 Offer、办理入职、面试反馈编辑/催评），全部走 prepare → 用户明确确认 → apply 协议，且 offer.send / interview.arrange(notify) / feedback.urge 属 **L3 外部通知**（触达真实候选人/面试官），用法见 [`recruit-write.md`](recruit-write.md)。

**招聘撤销类写操作（取消改期入职）仍在禁用清单**，见 `weaver-work-cli ehr schema` 的 `withheldOperations`。原因：撤销动作破坏性最强且依赖独立入口链路，未迁移实现；不编造、不绕过，也不要引导用户改用源文档里的原始接口路径。

## 移动端考勤打卡：禁用

`attend.card.sign.mobile` 同样在 `withheldOperations` 中。

移动端打卡依赖真实经纬度、WiFi/蓝牙、设备信息与客户端加密凭证，这些 Agent 均无法真实获取，服务端校验必然拒绝。**严禁伪造定位坐标、WiFi 信息或设备凭证重试**。

正确的处理方式是：明确告知用户该环境需要移动端打卡，请改用 IM APP 移动端、移动端企业微信等完成打卡。若租户开启了「允许 PC 电脑端打卡」，则可改用 `ehr.attend.card.check.prepare` / `.apply`。

## 通用禁止项

- 禁止读取、复制或解析认证目录、Cookie、ETEAMSID、业务 Token。认证诊断只能通过 `weaver-work-cli auth` 系列命令与 `weaver-work-cli doctor --e10` 完成。
- 禁止把源文档里的原始接口路径当成可直接调用的地址。所有调用必须走 `weaver-work-cli --profile eteams ehr run <operation> --input -`。
- 禁止把未出现在 `weaver-work-cli ehr schema` 中的能力写成可用 operation。
- 禁止在写操作中跳过确认链：不得在 `prepare` 之后未经用户明确确认就调用 `apply`，不得自动重试 `apply`。
- 遇到 `partial`、`write_uncertain`、登录失效或网络中断时，立即停止当前写流程，先做只读回查。
- 涉及附件、图片、本地文件、远程 URL 或文件内容解析时，必须先向用户说明：文件内容可能会被上传到业务系统或解析服务，并可能进入当前大模型上下文。必须等待用户**明确确认**后才继续。

## 未实测声明

本技能的接口契约全部来自源文档，未在真实 E10 环境实测。以下差异点需要在你的环境中复核（详见交付说明中的待验证项清单）：

- 三个子系统的响应成功判定与分页结构差异。
- 各报表 `pageSize` 是否被页面配置固定为 100。
- PC 端打卡凭证算法与目标租户的打卡方式开关是否匹配。
- 各数据源的必填过滤字段是否严格为文档中标注的字段。
