# 对账输出结果模板

## 控制台输出格式

### 匹配成功

```
============================================================
  🎉🎊 对账结果：完全匹配！恭喜恭喜！太棒了！ 🎊🎉
============================================================
  客户代码    ：{company_code}
  店    铺    ：{user_account}
  平    台    ：{platform}
  账单开始时间：{start_time}
  账单结束时间：{end_time}
  Excel 订单总数    ：{excel_total_rows}
  MCP 结算订单总数  ：{db_total_rows}
  Excel 总结算金额  ：{excel_total_amount}
  MCP 总结算金额    ：{db_total_amount}

  ✅ 所有订单金额完美匹配，账单核对无误！
  💪 你的数据真的很干净，继续保持！加油！
============================================================
```

### 存在差异

```
============================================================
  😢😔 对账结果：存在差异，需要核查...
============================================================
  客户代码    ：{company_code}
  店    铺    ：{user_account}
  平    台    ：{platform}
  账单开始时间：{start_time}
  账单结束时间：{end_time}
  Excel 订单总数    ：{excel_total_rows}
  MCP 结算订单总数  ：{db_total_rows}
  Excel 总结算金额  ：{excel_total_amount}
  MCP 总结算金额    ：{db_total_amount}
  自动补齐订单数    ：{auto_matched_count}
  差异条数          ：{diff_count}

  😔 发现差异，别灰心，一起查清楚！加油！💪
============================================================
```

---

## Excel 输出文件结构

文件名：`{原文件名}_reconcile_result.xlsx`

| Sheet 名 | 内容 |
|---------|------|
| 对账摘要 | 汇总信息、时间范围、订单数、金额对比、结论 |
| 差异明细 | 差异订单列表（orderId、Excel金额、MCP金额、差值、差异类型） |
| Excel明细 | Excel 全量数据（orderId、settlementAmount、order_settled_time） |
| MCP结算明细 | MCP 结算全量数据（orderId、settlementAmount） |

### 差异类型说明

| 类型 | 含义 |
|------|------|
| `金额差异` | Excel 与 MCP 结算均有该订单，但金额不一致 |
| `Excel有/MCP无` | Excel 有该订单且金额≠0，但 MCP 结算没有 |
| `MCP有/Excel无` | MCP 结算有该订单，但 Excel 没有 |

### 对账摘要 Sheet 字段

```
start_time        | {start_time}
end_time          | {end_time}

客户代码          | {company_code}
店铺              | {user_account}
平台              | {platform}
账单开始时间      | {start_time}
账单结束时间      | {end_time}

                  | Excel     | MCP结算  | 是否一致
订单总数          | 1683      | 1683      | ✅
总结算金额        | 35068361  | 35068361  | ✅
自动补齐订单数    | 13        |           |
差异条数          | 0         |           | ✅

对账结论          | 🎉 完全匹配，账单核对无误！太棒了！
```
