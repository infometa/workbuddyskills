---
name: tencentads-advertiser
description: "腾讯营销（原腾讯广告）广告主信息查询与管理技能。支持查询关联广告主账号列表、查询/修改账户日预算、查询资金账户余额、查询共享钱包信息、获取资金账户日结明细"
license: MIT. See LICENSE for full terms.
compatibility: any
metadata:
  author: Tencent Ads Delivery Team
  version: "0.5.8"
  icon: users
  category: tencent-ads
---

# 腾讯广告 - 客户账号查询技能

> **前置依赖**：需安装 `tencentads-cli`（Node.js ≥ 20）。执行 `npm install -g tencentads-cli@latest` 安装或升级；版本过低时 `tencentads` 会给出提示。
> - **脚本调用**: 所有 API 操作通过本 Skill 目录下的脚本执行，格式为 `node scripts/<脚本名>.mjs '<JSON参数>'`。
> - **认证依赖**: 本技能依赖 `tencentads-auth` 技能配置的 API Key 凭据，如遇认证错误请先完成鉴权。
> **脚本调用格式统一**：`node scripts/<脚本名>.mjs '<JSON 参数>'`
> 执行脚本时先进入本 skill 根目录，再按相对 `scripts/` 路径调用。

### ⚠️ 跨平台 JSON 参数传递规则（经实测验证）

脚本调用格式为 `node scripts/<脚本名>.mjs '<JSON参数>'`，但 **JSON 参数的引号包裹方式因操作系统/终端而异**，传递不当会导致 `JSON.parse` 报错（如 `Expected property name or '}' in JSON at position 1`）。

| 终端环境 | 正确写法 | 说明 |
|---------|---------|------|
| **Linux / macOS (Bash/Zsh)** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 单引号包裹，内部双引号原样保留 |
| **Windows Git Bash** | `node scripts/xxx.mjs '{"key":"value"}'` | ✅ 同 Bash |
| **Windows CMD** | `node scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 双引号包裹 + 反斜杠转义 |
| **Windows CMD (备选)** | `node scripts/xxx.mjs "{""key"":""value""}"` | ✅ 双引号包裹 + 双双引号转义 |
| **Windows PowerShell 5.x** | `node --% scripts/xxx.mjs "{\"key\":\"value\"}"` | ✅ 必须加 `--%` 停止解析符 |
| **Windows PowerShell 5.x (备选)** | `` node scripts/xxx.mjs "{\`"key\`":\`"value\`"}" `` | ✅ 反斜杠 + 反引号组合转义 |

> **⛔ PowerShell 5.x 是重灾区**：单引号 `'...'`、反引号 `` `" `` 、反斜杠 `\"` 三种常见写法**全部失败**（双引号会被吞掉）。必须使用 `--% ` 停止解析符或 `` \`" `` 组合转义。
> **⛔ Windows CMD 不支持单引号包裹字符串**，单引号会被当作普通字符传入脚本，导致 JSON 解析失败。

## 脚本列表

| 脚本 | 功能 | 必填参数 | 可选参数 |
|------|------|---------|---------|
| `scripts/get-account-list.mjs` | 查询当前用户关联的竞价广告主账号列表 | - | corporation_name_fuzzy_list, page, page_size |
| `scripts/get-daily-budget.mjs` | 查询账户日预算 | account_id | - |
| `scripts/update-daily-budget.mjs` | 修改账户日预算 | account_id, daily_budget | use_min_daily_budget |
| `scripts/get-funds.mjs` | 查询资金账户信息（余额/锁定金额/今日消耗） | account_id | fund_type_list |
| `scripts/get-wallet.mjs` | 查询共享钱包信息（余额/绑定账户等） | account_id | - |
| `scripts/get-daily-balance-report.mjs` | 获取资金账户日结明细（包含日终结余） | account_id, date_range | page, page_size |
| `scripts/get-wallet-basic-info.mjs` | 通过钱包 ID 查询共享钱包基础信息 | account_id, wallet_id | - |

## 查询广告主账号列表

调用 `user_account_list/get` 接口，获取当前 user_id 下关联的**竞价广告主**账户信息列表。

> ⚠️ **仅返回竞价广告主账户**，不包含代理商等其他类型账户。

```bash
# 查询全部关联账号（默认分页）
node scripts/get-account-list.mjs

# 按公司名称模糊搜索（最多 2 个关键词，每个 2~50 字符）
node scripts/get-account-list.mjs '{"corporation_name_fuzzy_list":["广州","西安"]}'

# 指定分页参数（page_size 范围 1~500）
node scripts/get-account-list.mjs '{"page":2,"page_size":20}'
```

> **分页上限限制**：严格要求 `page * page_size <= 13000`，超出此限制接口将报错。

**接口详情见**: [references/user-account-list-get.md](references/user-account-list-get.md)

## 适用场景

### 场景 A：用户需要查找某个公司的竞价广告主账号

1. 从用户描述中提取公司名称关键词
2. 调用 `get-account-list.mjs`，传入 `corporation_name_fuzzy_list`
3. 将匹配到的账号列表展示给用户

### 场景 B：用户需要浏览所有关联的竞价广告主账号

1. 调用 `get-account-list.mjs`（不传参数或仅传分页参数）
2. 展示第一页结果和分页信息
3. 如果有多页，告知用户总数并询问是否需要查看更多

## 注意事项

1. **仅支持竞价广告主**：`get-account-list.mjs` 仅返回竞价广告主账户，不包含其他类型
2. **无需传入 account_id**：`get-account-list.mjs`接口基于当前登录用户的 user_id 查询，不需要指定广告主账号
3. **分页默认值**：不传 `page` 默认为 1，不传 `page_size` 默认为 10
4. **模糊匹配限制**：`corporation_name_fuzzy_list` 最多传 2 个字符串，每个字符串长度限制 2~50 个字符
5. **认证依赖**：本技能依赖 `tencentads-auth` 技能配置的 API Key 凭据，如遇认证错误请先完成鉴权
6. **分页上限限制**：`get-account-list.mjs` 严格要求 `page * page_size <= 13000`，超出此限制接口将报错
7. **所有枚举值禁止猜测，必须通过 `get-enum-options.mjs` 查询确认**：

## 错误处理

- 如果返回认证错误，引导用户使用 `tencentads-auth` 技能重新配置 API Key
- 如果 `corporation_name_fuzzy_list` 参数不合法（超过 2 个、字符串长度不在 2~50 范围），脚本会返回明确的错误提示
- 如果查询结果为空，告知用户未找到匹配的账号，建议调整搜索关键词或检查是否有关联账号

---

## 接口文档索引

| 功能 | 文档 | 说明 |
|------|------|------|
| 广告主账号列表查询 | [user-account-list-get.md](references/user-account-list-get.md) | 查询当前用户关联的竞价广告主账号列表 |
| 账户日预算查询与修改 | [advertiser-daily-budget.md](references/advertiser-daily-budget.md) | 查询当前日预算、修改日预算，含 Agent 使用流程和 use_min_daily_budget 决策规则 |
| 资金账户信息查询 | [funds-get.md](references/funds-get.md) | 查询各类资金账户余额、锁定金额、今日消耗，支持按 fund_type 过滤 |
| 钱包信息查询 | [wallet-get.md](references/wallet-get.md) | 查询共享钱包余额、名称、代理商、主体及绑定账户信息 |
| 资金账户日结明细查询 | [daily-balance-report-get.md](references/daily-balance-report-get.md) | 查询资金账户日结明细，包含日终结余数据，支持按日期范围查询 |
| 钱包基础信息查询（按钱包 ID） | [wallet-basic-info-get.md](references/wallet-basic-info-get.md) | 通过钱包 ID 查询共享钱包基础信息，含资金信息和监控预警 |

## 相关技能

- **tencentads-auth** - 配置 API Key 鉴权凭据
