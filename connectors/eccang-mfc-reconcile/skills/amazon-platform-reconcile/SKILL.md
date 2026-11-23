---
name: amazon-reconciliation
description: Amazon账单对账技能。解析Amazon月度统一交易CSV账单，由Python脚本调用eccang-mfc-reconcile MCP查询订单归属及财务type/total汇总，差异时自动分析描述并定位订单聚合差异。适用于Amazon卖家月度账单核对、财务对账和reconciliation场景。账单特征：CSV 含 type+total+amazonOrderId（或葡语 tipo+id do pedido）。平台未确认时先用 platform-reconcile-router 技能判定。
license: Proprietary
compatibility: 需要 Python 3.10+、mcp>=2,<3 及 eccang-mfc-reconcile MCP 的 HTTPS 网络访问；Excel 导出另需 openpyxl>=3.0.0，无需数据库驱动或凭据。
metadata:
  author: amazon-duizhang
  version: "2.0"
---

# Amazon 账单对账技能

## Step 0 — 平台自检（执行前必做）

本技能**只处理 Amazon 账单**。动手前先确认文件确实是 Amazon 导出：

- 特征：CSV，表头含 `type` + `total` + `amazonOrderId`（英文导出），或 `tipo` + `id do pedido`（葡语/巴西站导出）
- 表格文件表头可能不在第 1 行（前面常有说明行），应在表头行定位后再取数

**若文件不是 Amazon 账单，立即停止**——不要执行本技能脚本、不要输出对账结果。改由
`platform-reconcile-router` 技能判定平台（`python scripts/detect_platform.py <文件> --json`），
再分发到对应平台技能。跑错平台会产出满屏假差异，比不跑更糟。

## 适用场景

- 用户提供 Amazon 月度统一交易 CSV（MonthlyUnifiedTransaction），要求账单核对、财务对账或 reconciliation 时使用。
- 一份账单应来自同一公司、店铺和币种。脚本自行连接 eccang-mfc-reconcile MCP，不依赖助手代查或 IDE 的 MCP 注册配置。
- 先比较排除 Transfer 后的所有费用项；一致即结束，有差异自动分析描述并定位订单聚合差异。总金额相等不代表费用项一致，聚合匹配不代表交易逐笔一致。
- 默认只输出控制台报告；全费用明细、记录总数及额外显式查询入口尚未启用。

## 定位目录与检查环境

主脚本位于 `scripts/reconcile.py`。执行前先定位路径：

1. 以**本次加载的 `SKILL.md` 所在目录**为 Skill 根目录；使用界面安装后的实际位置，不猜测安装目录，也不把当前工作目录当作 Skill 根目录。
2. 优先使用用户已选虚拟环境中 Python 解释器的绝对路径，先执行该解释器的 `--version` 确认版本至少为 3.10，再启动脚本；解释器不存在或版本过低时先说明问题，不静默切换。脚本与 `scripts/requirements.txt` 的绝对路径均由 Skill 根目录拼接，不能写死开发机目录。
3. 用户提供的相对 CSV／输出路径按**调用时的工作目录**定位，确认后传入绝对路径。不要为运行技能切换工作目录；相对业务路径不能改按 Skill 根目录解释。
4. 下列占位符须替换为实际绝对路径，保留引号以支持中文和空格。依赖缺失时先向用户说明，安装命令仅在获准后执行；不自动安装到全局环境。

先检查 Python 版本，再使用 `--check-env` 检查依赖，无需提供 CSV。

Windows PowerShell：

```powershell
& "<Python解释器绝对路径>" --version
& "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --check-env
```

POSIX shell（例如 bash）：

```bash
"<Python解释器绝对路径>" --version
"<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --check-env
```

检查仅验证本地 Python、MCP SDK／anyio 入口及可选 Excel 依赖，不读取账单、不连接 MCP、不安装或升级依赖、不生成输出文件或导入字节码缓存。核心环境可用返回 `0`；缺少 openpyxl 只显示“可选功能不可用”。核心环境失败返回 `1`；`--check-env` 与 `--csv` 或 `--output` 同用返回参数错误 `2`。通过不代表网络、权限或业务数据已验证。

普通对账在解析 CSV 后、首次远端请求前检查核心依赖；显式指定 `--output` 时同时检查 openpyxl，失败不查询、不导出。脚本不自动加载 `.test-deps`、创建虚拟环境或更换解释器。无合适虚拟环境时，按 [运行环境与修复说明](assets/db_config.md#运行环境) 先向用户说明并取得确认。

依赖修复及新建虚拟环境的命令见 [依赖问题与修复](assets/db_config.md#依赖问题与修复)。安装副本不包含测试依赖，环境检查失败不能靠引用开发目录绕过。

## 执行对账

### 执行脚本

确认环境可用、账单路径明确后执行；占位符替换为实际绝对路径，保留引号。

Windows PowerShell：

```powershell
& "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>" --date-type datetime
```

POSIX shell：

```bash
"<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>" --date-type datetime
```

仅在用户明确要求导出时追加 `--output "<输出绝对路径>"`。`scripts/compare_orders.py` 是同一流程的薄入口，可替换上述脚本路径，接受相同参数及退出状态；其纯本地比较函数不发网络请求。

### 选择时间口径与站点

- 默认 `--date-type datetime` → MCP `dateType=entry`，使用 `date_start_time/date_end_time`；不强制再次询问，也不向 MCP 传字面值 `datetime`。
- 结算模式 `--date-type transaction` → `dateType=settlement`，使用 `transaction_start_date/transaction_end_time`。每次只选一个口径，缺结算日期时停止，不过滤缺失记录或切换口径。
- 日期范围由对应时间列的最小／最大日期扩展到全天，查询格式为 `yyyy-MM-dd HH:mm:ss`；不额外转换时区。公司、店铺、口径及范围固定为本次上下文，切换口径重新查询。
- 默认 `--site auto` 自动查找表头，兼容前置说明行。新增 ES、NL、SE、PL、TR、JP、BE 按已配特征进入受限路径，也可显式指定；配置不兼容或 FR／BE 特征冲突则停止。
- AU 必须显式传 `--site AU`，不从英语表头推断站点。JP 仍可能因未知日语 Type 或 `JST` 后缀停止。
- 23 站文档不等于全部支持：8 个既有站点、7 个受限候选站点、1 个受限英语站点、7 个未接入站点。只在需要时按 [站点与语言文档索引](assets/type_mapping.md#站点与语言文档索引) 读取对应资料，无需加载全部语言文档。

### 输入校验

- 汇总 `type/total`，保留 CSV 物理起始行号、原始／规范类型、订单号、描述、SKU、数量、市场、两个时间、费用原值及 Decimal total；不可靠的下钻金额标记错误，不补零。
- 新增受限路径仅接受 UTF-8（含 BOM）、逗号分隔 CSV。缺必需列、重复／冲突列、行宽不一致、未知或空 Type、非法或歧义金额均在连接 MCP 前停止，返回 `1`，不导出。整份账单须有订单号及有效的所选日期范围。
- 新增路径按全文件一致的数字语法解析金额，不按国家推定小数点，不对子集重新推断；英语 FBA 长名称先规范化。只接受已配置的确切英语 Type 及排除项 `transfer`。
- 新增路径仅按非 Transfer 记录计算查询范围；入账日期必须有效，释放日期非空也须有效。结算模式要求每条非 Transfer 记录都有标准英语 `Transaction Release Date`，不猜测本地化列名；入账模式允许释放日期缺失。
- 受限路径只接受已配日期／月份及 `PDT`、`PST`、`UTC`、`GMT`、`GMT-数字` 或无时区后缀；`JST`、`AEDT` 等仍待样本确认。上述严格校验不表示既有 8 站已完成同等验证，详见 [受限解析边界](assets/type_mapping.md#新增路径的受限解析边界)。

### 参数说明

- `--csv`：Amazon 月度交易 CSV 文件路径；普通对账必需
- `--check-env`：仅检查本地环境，不需要 CSV；不能与 `--csv` 或 `--output` 同时使用
- `--site`：可选，`auto`（默认）、`ES`、`NL`、`SE`、`PL`、`TR`、`JP`、`BE`、`AU`；大小写均可。AU 严格路径必须显式指定；原有 8 站继续使用 `auto`
- `--mcp-url`：可选，MCP 服务地址，默认使用 HTTPS
- `--mcp-timeout`：可选，连接及单次调用超时秒数，默认 `60`，必须为有限正数
- `--date-type`：对账日期类型，`datetime` 使用入账时间（默认），`transaction` 使用结算日期
- `--output`：可选，输出 Excel 文件路径（**仅在用户明确要求时才传此参数**）

## 差异定位

以下操作由脚本自动完成，不需要助手额外发起查询。接口契约及错误处理详见 [MCP 连接与数据约定](assets/db_config.md)。

1. **建立查询上下文**：使用官方 SDK 复用一个 Streamable HTTP 会话，默认端点为 `https://datacenter.eccang.com/nexus/mcp/stream`。工具清单发现一次，先校验归属和类型汇总工具，其余按需校验。按 CSV 顺序最多尝试 10 个不重复订单号获取公司、店铺、平台；仅空结果可换下一单，多条归属或调用失败立即停止。
2. **比较全部费用项**：调用一次 `queryFmsTransaction`，会话内按 [类型映射与比较规则](assets/type_mapping.md#类型映射与比较规则) 合并、排除 Transfer，四舍五入到两位后严格比较。CSV 零值而 MCP 缺少对应类型时仅在内存按零比较，不写远端。按 `|total|` 降序展示；各费用项一致即结束，不查其他明细。
3. **分析描述构成**：有差异且本地记录和所选时间校验通过后，调用一次 `queryFmsTransactionDescription`，只传五个公共参数；先按原始 type 回勾，再本地筛选差异比较组。description 只去两端空白，保留原文，空值成组；CSV 缺描述列则仅展示远端构成、标记“部分可比较”并继续订单定位，不把缺列当零。
4. **定位订单差异**：差异组展开成实际远端原始 type，去重后调用一次 `queryFmsTransactionDetail(types=[...])`；不传 description，不假装按描述筛选。按“订单号 + 比较组”累计，保留重复交易及来源记录数，展示“仅 CSV 有／仅 MCP 有／金额不同”。空订单号按费用组单列并附本地描述、行号；CSV 单边类型无远端原始 type 时只展示本地记录，不造 type、不发空 types、不据此推断缺单。
5. **回勾与失败处理**：本地记录、描述及订单明细分别回勾原始类型和比较组金额。明细保留两个返回时间，所选时间须有效且在范围内，非所选时间允许 null 或范围外。超时、接口／响应错误、缺字段、非法金额、时间越界或回勾失败均停止后续定位，保留已知汇总事实并标记“流程未完成”，返回 `1`，即使指定 `--output` 也不导出正常报告。金额回勾不能排除正负抵消的漏记录，不能证明逐笔完整。

## 输出与限制

- 按 [分层对账结果模板](references/RESULT_TEMPLATE.md) 输出最终报告，展示实际时间口径、查询范围和各层状态。控制台与显式 Excel 导出共用查询结果，不另查数据。
- **默认仅控制台输出；只有用户明确要求导出时才传 `--output` 生成 xlsx。** 财务记录总数显示“未查询”，不能用类型条数替代；CSV 数量为全部交易记录行数，不是去重订单数。
- 正常对账退出状态：`0` 汇总金额匹配且流程成功；`2` 已确认金额差异且流程成功；`1` 输入、接口、响应、回勾、会话或导出失败。argparse 参数错误也返回 `2`，须结合错误信息区分；“部分可比较”不抹掉已确认金额差异。
- 全费用明细、记录总数及额外显式查询入口尚未启用，不因用户要求就编造可用参数或自动调用这些工具。
- 旧 `--env` 已移除，不读取 `.env`，不回退数据库、不调用其他平台工具替代 Amazon 明细、不修改费用映射来掩盖差异。
- 已有两份真实账单按入账口径执行的记录；这不代表所有站点、结算口径、全费用或交易逐笔一致性已验收。合成 CSV、模拟 MCP 及 SDK 内存服务测试不替代真实业务验收。
- 用户通过界面拖入文件夹安装。源码目录不在标准发现目录不能证明未安装；以实际加载位置为准。整理方式及导入、加载、触发的分别验收见 [文件夹交付与界面安装](assets/db_config.md#整理文件夹与界面安装)。
