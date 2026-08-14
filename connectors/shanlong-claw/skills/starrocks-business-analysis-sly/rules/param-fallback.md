# param-fallback.md — `#{变量名}` 缺失按需补全策略

> 本文件描述当 AI 构造 SQL 时，所需 `#{变量名}` 缺失时，AI 的**按需预查询补全**流程与**降级行为**。

---

## 一、两个核心变量

| 占位符 | 含义 | 注入规则 | 严重性 |
|--------|------|---------|--------|
| `#{SL_UNIFIED_G_ID}` | 集团 G 号 | 系统在 SQL 执行前自动注入 | 🔴 致命（所有 SQL 必须） |
| `#{omShopCodes}` | 门店 C 号列表 | 系统始终注入（默认为全部授权门店；用户指定门店时缩窄为指定门店） | 🔴 致命（所有 SQL 必须） |
| `#{omShopCodeOrgNameMap}` | 门店码→门店名映射 | 辅助展示 | ⚪ 无（无查询影响） |

**AI 视角规则**：
- SQL 模板**仅使用 `#{变量名}` 占位符**，永不硬编码真实 G 号 / 门店码
- 真实值由系统在 SQL 执行前自动注入，AI 不应读取配置文件
- ⚠️ **值范围硬约束**：SQL 中出现的 `group_code` / `store_code` 值**必须 100% 来自 `#{SL_UNIFIED_G_ID}` / `#{omShopCodes}` 占位符的注入值，AI **不得私自添加、枚举、或推断**任何不在占位符范围内的值（含硬编码、额外 OR 条件、子查询返回非授权值）

> 💡 **变量来源说明（实现层，仅供理解）**：`#{变量名}` 真实值由机器人配置层提供，AI 无需、不应、不能直接读取该层。

---

## 二、门店编码获取（`sl store find`）

> 🎯 **触发场景**：用户输入中**明确出现**门店名称 / 简称 / 别名 / 门店 ID 时，必须先调用 `sl store find` 获取标准 `omShopCode`，将 `#{omShopCodes}` 缩窄为指定门店。
> **不触发场景**：用户问"全集团/全部门店"等无具体门店指向的查询时，跳过此步骤，`#{omShopCodes}` 使用系统默认值（全部授权门店）。SQL 中仍**必须**包含 `store_code IN (#{omShopCodes})`。

### 2.1 CLI 命令

> 🔧 **路径**：下文 `sl` 同 [`SKILL.md` CLI 入口](../SKILL.md#cli-入口)。**Bash 首选**自动选 Windows `sl.cmd` / macOS `sl`；**禁止** Bash 内写 `%USERPROFILE%\...`，**禁止**依赖 PATH / `which` / `where`。

```bash
# 按名称精确查询（Mac / Linux / Windows Git Bash 通用）
SL="$HOME/.slclaw/bin/sl"; [ -f "$HOME/.slclaw/bin/sl.cmd" ] && SL="$HOME/.slclaw/bin/sl.cmd"
"$SL" store find --type crm --name "<门店关键词>" --format json

# 按关键词或门店 ID 模糊查询
"$SL" store find --type crm --keyword "<门店关键词或门店ID>" --format json
```

### 2.2 候选结果处理

CLI 返回 JSON 是**门店候选数组**，关键字段：

| 字段 | 用途 |
|------|------|
| `omShopCode` | 后续 `#{omShopCodes}` 取值（门店 C 号） |
| `orgName` | 门店名称（消歧用） |

**三种命中情况**：

| 命中数 | AI 行为 |
|--------|---------|
| 0（`[]`） | 🛑 停止：`⚠️ 未找到与"<关键词>"匹配的门店，请检查关键词或提供门店 ID 后重试。` |
| 1 | ✅ 直接使用该 `omShopCode`，无需确认 |
| ≥ 2 | ⚠️ **必须列表让用户确认**，禁止静默取第一条 |

**多候选展示模板**：

```
找到以下 <N> 家匹配 "<关键词>" 的门店，请确认您要查询的是哪一家：

| # | 门店名（orgName） | 门店码（omShopCode） | 集团码 |
|---|----------------|-------------------|--------|
| 1 | <orgName1> | <omShopCode1> | <groupCode1> |
| 2 | <orgName2> | <omShopCode2> | <groupCode2> |
| ... | ... | ... | ... |

请回复编号（1/2/...）或门店码。
```

### 2.3 Token 降级

CLI 返回 `token missing store list` / `permission denied` 等错误时：

1. 执行 `sl token refresh dc` 刷新门店权限
2. 等待刷新成功后**重试一次**同一条 CLI
3. 仍失败则按 2.2 "未找到门店" 模板告知用户

### 2.4 成功后的衔接

> ✅ 所有 SQL 的 WHERE 中**始终**包含 `store_code IN (#{omShopCodes})`，无例外。
> `#{omShopCodes}` 的值分两种场景：

| 场景 | `#{omShopCodes}` 取值 |
|------|---------------------|
| 用户**未指定**门店（集团级查询） | token 配置层默认门店码列表（全部门店） |
| 用户**明确指定**门店（通过 `sl store find` 解析） | 用户确认的 `omShopCode`（单店或多店逗号拼接） |

---

## 三、缺失降级行为

### 3.1 `#{SL_UNIFIED_G_ID}` 缺失

**无法通过 SQL 推算得到**（集团码是外部授权概念），直接提示：

```
⚠️ 当前账号未配置集团编码权限（SL_UNIFIED_G_ID 缺失），无法执行数据查询。
请联系管理员在机器人配置中添加 SL_UNIFIED_G_ID 参数。
```

### 3.2 `#{omShopCodes}` 缺失（异常情况）

> ⚠️ 正常运行时 `#{omShopCodes}` 始终由系统注入（默认为全部授权门店），此降级仅在系统配置异常时触发。

若检测到 `#{omShopCodes}` 确实缺失（配置异常），提示用户修复配置：

```
⚠️ 当前未配置门店权限（omShopCodes 缺失），无法执行数据查询。
请联系管理员在机器人配置中添加门店权限，或执行 sl connector status 重新初始化。
```

**不得**在 `#{omShopCodes}` 缺失时省略 `store_code` 过滤条件执行查询。

---

## 四、缓存与配额

| 规则 | 说明 |
|------|------|
| **缓存范围** | 会话内（单次对话），不跨会话 |
| **重复利用** | 同一会话已补全的参数直接复用 |
| **失败不缓存** | 补全失败的参数下次仍会尝试（可能是网络抖动） |
| **配额占用** | 预查补全占用「单轮查询 10 次」上限，**优先补全**再执行业务查询 |

---

## 五、与 SQL 预查询的边界

| 维度 | `sl store find` | SQL 预查询补全 |
|------|----------------|---------------|
| **触发条件** | 用户**明确指定**门店 | 用户**未指定**门店但 `#{omShopCodes}` 缺失 |
| **作用** | 名称 → `omShopCode` 解析 | 已有 `#{SL_UNIFIED_G_ID}` → 补 `#{omShopCodes}` 列表 |
| **使用场景** | "查陶陶居万国店" | "查全集团门店"（`#{omShopCodes}` 未注入时） |
| **依赖** | 独立 CLI，与配置层解耦 | 强依赖 `#{SL_UNIFIED_G_ID}` 可用 |
| **失败处理** | 提示用户换关键词 / 触发 `sl token refresh dc` | 🛑 报错并提示用户检查配置（`#{omShopCodes}` 为强制项，不可省略） |

**SQL 预查询补全的参考 SQL**（仅 `#{omShopCodes}` 缺失时使用）：

```sql
-- 从 POS 视图获取近 30 天有交易的门店码列表
SELECT CONCAT("'", GROUP_CONCAT(DISTINCT store_code SEPARATOR "','"), "'") AS shop_codes
FROM dm.v_pos_corp_sale_analysis_with_sly
WHERE group_code = '#{SL_UNIFIED_G_ID}'
  AND settle_biz_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
LIMIT 1
```

> 📌 **注意**：此方法只能获取**近 30 天有交易**的门店，可能遗漏无近期营业记录的门店。适用于启动补全，不适合替代完整门店权限配置。
