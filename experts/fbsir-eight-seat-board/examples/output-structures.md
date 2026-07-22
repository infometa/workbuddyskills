# 独董会输出结构示例

以下只示范结构，不提供可套用的行业事实、阈值或结论。

## 决策起手卡

```text
【真议案】是否在不突破现金安全边界的前提下，对候选项目进行一个可逆的小规模试点？
【决策选项】不做 / 小试 / 直接投入
【已知事实】仅列用户明确提供且已确认口径的事实
【待验证假设】列出需要校准的市场、成本和执行假设
【关键缺口】列出会改变合法性、选项或承受力的缺口
【建议模式】standard_review
【建议席位及理由】战略、资本财务、法务风控
【唯一下一步】确认议案边界并补充最小必要数据
【可直接回复】确认议案卡并开始独立审议 / 更正：… / 补充事实：…
```

## 确认后的会议计划

用户确认起手卡后，召集人在建团前先形成并校验计划信封：

```json
{
  "schema": "fbsir.review-plan/v1",
  "runId": "run_example",
  "revision": 1,
  "reviewMode": "standard_review",
  "agendaItems": [
    {
      "agendaItemId": "agenda_1",
      "decisionQuestion": "在既定约束下应优先验证哪个可逆方案？"
    }
  ],
  "specialistSeatIds": ["growth-partner", "operations-partner"],
  "supportSeatIds": ["board-secretary"],
  "userConfirmed": true,
  "confirmationReceiptId": "user_confirmation_example",
  "singleNextAction": "request_team_create"
}
```

该信封不能作为团队已经创建或成员已经调度的证明。

## 专业席回传

```text
seatId=strategy-partner | stance=有条件赞成 | confidence=中 | conclusionReady=true | receiptId=<宿主真实回执>

一、独立性、关联与证据偏差
二、本席核心判断
三、支撑事实、推断与假设
四、立场及成立条件
五、最大风险和失效条件
六、最小补数或人工复核要求
七、对其他席位的质询
```

## 审议备忘录

```text
# 独董会审议备忘录
【表态统计】赞成 X / 有条件赞成 Y / 反对 Z / 不具备表态条件 W
【一句话建议】……

一、议案、选项与 Non-goals
二、证据、假设与关键缺口
三、各席核心判断
四、质询、修正与保留异议
五、建议、成立条件与失效条件
六、7/30/90 天行动
七、证据台账与回执索引
八、人工关卡与专业边界
```
