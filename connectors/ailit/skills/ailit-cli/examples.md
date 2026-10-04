# Space CLI Examples

## Login first

```powershell
ailit auth login
```

## Non-TTY login continuation

```powershell
ailit auth login --non-interactive --format json
ailit auth login --resume <workflowId> --result-set <resultSetId> --select 1 --format json
```

## Health check

```powershell
ailit doctor
ailit doctor --format json
```

## Search customer

```powershell
ailit customer list
ailit customer search 张三
ailit customer search 张三 --format json
ailit customer search --result-set <resultSetId> --select 1 --format json
```

## Search product

```powershell
ailit product list 
ailit product search 面巾纸
ailit product search 面巾纸 --format json
ailit product search --result-set <resultSetId> --select 1 --format json
```

## Search settlement account

```powershell
ailit account search 支付宝
ailit account search 支付宝 --format json
ailit account search --result-set <resultSetId> --select 1 --format json
```

## Full-payment sale preview

```powershell
ailit sale create --json skills/ailit-cli/templates/sale-quick-create-full.json --dry-run
```

Use this default preview for user confirmation. It shows customer, salesperson, bill date, line items, settlement details, freight, received amount, and total amount.

## On-account sale preview

```powershell
ailit sale create --json skills/ailit-cli/templates/sale-create-on-account.json --dry-run
```

For raw request inspection instead of user-facing preview:

```powershell
ailit sale create --json skills/ailit-cli/templates/sale-quick-create-full.json --dry-run --format json
```

When `unitPrice` is omitted, the CLI resolves price as customer quote, then product retail price, then `0.00`:

```json
{"productId":"123","productSkuId":"456","productName":"商品A","quantity":2}
```

To force a price, include `unitPrice`; it overrides the automatic price chain:

```json
{"productId":"123","productSkuId":"456","productName":"商品A","quantity":2,"unitPrice":3.5}
```

## Real create after confirmation

```powershell
ailit sale create --json skills/ailit-cli/templates/sale-quick-create-full.json
```

## Sale return

Set numeric `company_id` and `items[].product_id` in `sale-return.json` before running the command. Keep `warehouse_id` as `0` to use the configured default warehouse.

```powershell
ailit sale return --json skills/ailit-cli/templates/sale-return.json
```

## Batch product create

Use the draft template, preview first, then wait for the user's explicit 「确认」 before creating:

```powershell
ailit product batch-create --json skills/ailit-cli/templates/product-batch-create.json --dry-run
ailit product batch-create --json skills/ailit-cli/templates/product-batch-create.json
```

## Query sales orders

```powershell
ailit sale list --today
ailit sale list --week
ailit sale list --start 2024-01-01 --end 2024-01-31
ailit sale list --today --format json
ailit sale get <单据ID>                # numeric bill ID from `sale list`, not the bill code
ailit sale get <单据ID> --format json
```

## Stock queries

```powershell
ailit stock list --format json
ailit stock low                      # 按库存升序返回库存最低的一页
ailit stock low --threshold 5        # 返回库存 <= 阈值 的商品
ailit stock out                      # 缺货商品
```

## Sales reports

```powershell
ailit report all                     # 综合报表（推荐，并发效率最高）
ailit report all --format json
ailit report today
ailit report week
ailit report month
ailit report hot-sale
ailit report hot-sale --start 2024-01-01 --end 2024-01-31 --format json
```

## Customer debt

```powershell
ailit customer debt
ailit customer debt --format json
ailit customer get <id> --format json
```

## Purchase records

```powershell
ailit purchase list --today
ailit purchase list --week
ailit purchase list --start 2024-01-01 --end 2024-01-31 --format json
ailit purchase supplier
```

## Suggested agent sequence — sale creation

1. If auth state is unknown, run `ailit doctor`
2. If ordinary CLI/Codex/Claude Code auth is missing, use `ailit auth login` for terminal users, or `ailit auth login --non-interactive --format json` in non-TTY environments
3. If login returns `selection_required`, show the numeric `selectToken`, `displayName`, and `fields` when available, falling back to `summary`, then continue with `ailit auth login --resume <workflowId> --result-set <resultSetId> --select 1 --format json`
4. If `AILIT_AUTH_SOURCE=client`, ask the user to log in to Ailit Client again instead of running CLI login
5. Re-run `ailit doctor`
6. `ailit customer search <keyword>`
7. If search returns `selection_required`, present the structured candidate fields and continue with `--result-set <resultSetId> --select 1 --format json`
8. `ailit product search <keyword>` (an empty or broad keyword will return many results and trigger `selection_required` in JSON mode)
9. If search returns `selection_required`, present the structured candidate fields and continue with `--result-set <resultSetId> --select 1 --format json`
10. If search returns 0 results, ask the user: 商品「<名称>」不存在，是否需要先创建？
    - If yes: check unit (`product unit list`), pick category (`product type list`), create (`product create --name --type --unit --price`), then re-search to get `productId`/`productSkuId`
    - If no: remove the line or ask for a replacement product
11. Extract `productId`, `productSkuId`, `displayName` from `validatedItems[0].meta` — no need to call `ailit product get` again
12. `ailit account search <keyword>` when payment mode is `FULL` and the automatic account resolution is insufficient
13. If search returns `selection_required`, present the structured candidate fields and continue with `--result-set <resultSetId> --select 1 --format json`
14. `ailit sale create --json <file> --dry-run`
15. Use the dry-run preview as the confirmation view for the user; only switch to `--format json` if raw request inspection is needed
16. Only after explicit confirmation, run `ailit sale create --json <file>`

## Suggested agent sequence — daily business overview

1. `ailit doctor`
2. `ailit report all --format json`     # 今日/本周/本月汇总 + 热销
3. `ailit stock low --format json`      # 低库存预警
4. `ailit customer debt --format json`  # 欠款客户

## When JSON is appropriate

```powershell
ailit doctor --format json
ailit product search 面巾纸 --format json
ailit product search --result-set <resultSetId> --select 1 --format json
ailit auth login --non-interactive --format json
ailit auth login --resume <workflowId> --result-set <resultSetId> --select 1 --format json
ailit sale create --json skills/ailit-cli/templates/sale-quick-create-full.json --dry-run --format json
ailit report all --format json
ailit stock low --format json
ailit customer debt --format json
```
