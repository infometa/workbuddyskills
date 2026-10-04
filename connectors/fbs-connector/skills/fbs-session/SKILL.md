---
name: fbs-session
description: 福帮手访问码激活、权益预检、流程完结与退出会话。仅处理用户明确提出或主线明确要求的高级后续，不作为首轮业务入口。
metadata:
  ai.workbuddy.description_zh: 处理福帮手原业务会话的访问码、预检、完结和退出。
  ai.workbuddy.description_en: Handle legacy FBSir activation, entitlement prechecks, completion and business-session logout.
  ai.workbuddy.version: 2026.9.25-r7
  ai.workbuddy.author: FBSir
---
# 福帮手会话后续

执行本技能时遵守[公共路由](../fbs-connector/SKILL.md)。

本页四项保留 canonical 旧业务合同，须当前实际开放。历史独立 OAuth 预览的条件桥只开放 core3，不开放skill_activate/skill_precheck/skill_finish/skill_logout；在该资源停止本页动作，不借会员工具或另一连接绕过。

组织任何写入前完整读取 `references/session-write-outcomes.md`。

## 路由

- `skill_activate`：用户明确提供访问码，或主线返回明确要求激活；必填 `accessCode`、`skillCode`。
- `skill_precheck`：身份或会话已经明确，用户要求校验指定权益或积分；必填 `skillCode`。
- `skill_finish`：业务流程已经真实完成且有使用记录；必填 `usageId`、`status`。
- `skill_logout`：用户明确要求退出或重置会话。

## 边界

- 不向用户索要未被当前步骤需要的凭证；访问码、会话令牌只在授权链路内部原样传递。
- 激活、预检与完结都不替代聊天首值，也不自动触发奖励。
- `skill_finish` 不用于首轮入口或首值记录；主线进度由 `skill_consume` 负责。
- 不因网络错误、重试或内部诊断擅自登出。
- `skill_logout` 只退出旧业务会话，不代表撤销全部 OAuth、删除画像或注销账号；授权失效不自动调用它。
- 成功必须由对应工具回执证明；没有回执就只报告未确认状态。
- 超时、连接中断或缺失回执属于 `outcome_unknown`，不是明确失败；在确认当前 `tools/list` 提供安全状态回读前不得自动重放写操作。
