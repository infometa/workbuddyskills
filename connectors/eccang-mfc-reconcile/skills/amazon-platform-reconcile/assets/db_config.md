# eccang-mfc-reconcile MCP 连接与数据约定

文件名沿用旧版本，本文说明本地运行环境、文件夹交付及 eccang-mfc-reconcile MCP 契约。脚本不读取 `.env`，不需要数据库主机、账号或密码，也没有数据库回退路径。

## 运行环境

- Python 3.10+。先对选定解释器执行 `--version`；低版本可能在加载脚本时就遇到语法／类型错误，不能靠启动脚本升级环境。
- 官方 MCP Python SDK v2：`mcp>=2,<3`，并要求 `mcp.Client` 与传递依赖的 `anyio.fail_after` 实际可导入、可调用。
- Excel 导出依赖 `openpyxl>=3.0.0` 及 `openpyxl.Workbook`；只输出控制台报告时不检查或加载 openpyxl。
- 解释器使用当前已选 Python 的绝对路径；Skill 根目录取本次加载的 `SKILL.md` 所在目录。安装后使用实际加载位置，不假定当前工作目录或固定安装路径。
- 依赖清单使用 `"<Skill根目录绝对路径>/scripts/requirements.txt"`；需要安装时先获得用户确认，使用同一解释器执行。安装示例见下文 [依赖问题与修复](#依赖问题与修复)，不自动修改全局 Python 环境。

### 本地环境检查

检查不需要 CSV；`reconcile.py` 与 `compare_orders.py` 均支持 `--check-env`。先执行解释器的 `--version`，再按 [定位目录与检查环境](../SKILL.md#定位目录与检查环境) 中的命令运行。

- 输出实际 Python 解释器路径、Python／MCP SDK／anyio／openpyxl 版本、所需入口及可用状态；不建立 MCP 会话、不读取账单、不生成文件、不安装依赖，也不自动加载开发目录 `.test-deps`。
- 核心依赖均可用返回 `0`；Excel 依赖不可用仍返回 `0`，但明确显示“仅 Excel 导出需要／可选功能不可用”。Python 或核心依赖失败返回 `1`。
- 与 `--csv`、`--output` 同时指定返回 `2`；未选择检查模式的普通对账仍须提供 `--csv`。
- 版本核验覆盖稳定发布版本（含 post／本地版本后缀）；预发行或无法识别的版本不判为通过，应先确认受支持的环境，不自动降级或升级。
- 普通对账完成 CSV 解析后、首次查询前执行核心检查；带 `--output` 时在查询前额外核验 Excel 依赖。输入或依赖失败均不请求远端服务、不导出结果。
- 检查通过仅说明本地依赖可用，不说明网络、服务端权限、工具契约或财务结果正确。

### 依赖问题与修复

| 提示 | 含义及处理 |
|---|---|
| 未安装或元数据缺失 | 当前选定解释器没有完整的发布包；先核对解释器路径，不假设其他 Python 中的安装可复用 |
| 版本不满足要求 | 例如 MCP v1 不符合当前 v2 接口；确认目标环境后再按依赖清单安装 |
| 缺少可调用入口 | 包版本元数据存在，但实际模块缺少 Client、fail_after 或 Workbook；核对环境及同名模块遮蔽 |
| 缺少模块（可能是传递依赖） | 例如 Windows 下的 pywintypes；检查同一解释器的完整依赖安装，不把开发依赖目录自动加入运行路径 |
| 导入失败及异常类型 | 可能为损坏的安装或不兼容二进制；不显示任意原始异常内容，不将其误报为 MCP 网络故障 |

缺依赖时给出的安装建议使用**当前解释器路径**及**实际脚本同目录的 requirements.txt 绝对路径**，并按 PowerShell／POSIX 正确引用路径；建议不会被脚本执行。已选虚拟环境中仍有问题时，先向用户解释再修复，不悄悄更换解释器。

仅在用户确认安装到当前选定环境后执行：

```powershell
& "<Python解释器绝对路径>" -m pip install -r "<Skill根目录绝对路径>/scripts/requirements.txt"
```

```bash
"<Python解释器绝对路径>" -m pip install -r "<Skill根目录绝对路径>/scripts/requirements.txt"
```

若当前没有合适的虚拟环境，先确认 Python 3.10+ 及用户选择的**新目录**，获准后才执行以下步骤。不要覆盖已有环境；创建和安装均不是检查命令的副作用。

Windows PowerShell：

```powershell
& "<已确认版本的Python绝对路径>" --version
& "<已确认版本的Python绝对路径>" -m venv "<新虚拟环境绝对路径>"
& "<新虚拟环境绝对路径>/Scripts/python.exe" -m pip install -r "<Skill根目录绝对路径>/scripts/requirements.txt"
& "<新虚拟环境绝对路径>/Scripts/python.exe" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --check-env
```

POSIX shell：

```bash
"<已确认版本的Python绝对路径>" --version
"<已确认版本的Python绝对路径>" -m venv "<新虚拟环境绝对路径>"
"<新虚拟环境绝对路径>/bin/python" -m pip install -r "<Skill根目录绝对路径>/scripts/requirements.txt"
"<新虚拟环境绝对路径>/bin/python" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --check-env
```

之后用新环境的解释器执行对账，不需要改变 Skill 安装位置或全局 Python 配置。

## 整理文件夹与界面安装

### 开发源码与安装副本

- 开发目录保留测试、依赖、缓存及用户文件；运行以本次加载的 `SKILL.md` 所在目录为准。不能只因源码不在标准发现目录就断定未安装。
- 开发辅助脚本 `scripts/prepare_skill.py` 仅整理文件夹，不安装 Skill、不配置 Qoder、不运行对账，也不安装依赖。它只使用 Python 标准库，不受当前环境是否安装 MCP 影响。
- 默认生成源码根目录下的 `dist/amazon-reconciliation/`，顶层直接是 `SKILL.md`，目录名与元数据 `name` 一致。安装副本不含整理脚本；日常对账不需要也不会调用整理器。
- 允许清单共 30 个文件：`SKILL.md`，`scripts/` 下的 `reconcile.py`、`compare_orders.py`、`requirements.txt`，`assets/db_config.md`、`assets/type_mapping.md`，站点索引引用的 23 份语言文档及 `references/RESULT_TEMPLATE.md`。站点索引与清单不一致时停止，需维护者核对后同步。
- 不复制 `.test-deps`、虚拟环境、测试、缓存、`.env`、CSV/Excel 业务文件或其他构建产物；不通过递归复制整个开发目录来制作交付物。

### 从开发源码整理

以下命令仅供维护者在准备交付时使用，不能要求用户在安装副本中运行。替换为实际绝对路径，保留引号；不要在整理期间并发修改源码或目标目录。

Windows PowerShell：

```powershell
& "<Python解释器绝对路径>" -X utf8 "<源码根目录绝对路径>/scripts/prepare_skill.py"
```

POSIX shell：

```bash
"<Python解释器绝对路径>" -X utf8 "<源码根目录绝对路径>/scripts/prepare_skill.py"
```

需要其他位置时，在上述命令末尾追加 `--output-dir "<新目标父目录绝对路径>/amazon-reconciliation"`；相对目标按调用时的工作目录理解，默认目标始终相对于源码根目录。

- 目标必须不存在，不能等于或包含源码目录；已有目标时停止，不覆盖、不清空。重复交付可选择另一全新的同名目标，不自动删除旧产物。
- 源文件缺失、不可读、索引或名称不符、越界路径、符号链接及目录联接等情况均停止。源文件快照校验完成后才创建目标，加载入口最后写入。
- 成功返回 `0`；整理失败返回 `1`，参数错误返回 `2`。复制中途失败会提示“产物未完成”，保留已产生文件供人工检查；不要拖入失败产物，也不要直接重试覆盖。

### 用户通过界面安装与验收

1. 交付物完成文件清单与运行验证后，将**整个 `amazon-reconciliation` 文件夹**拖入现有安装界面，按提示完成导入；不需要命令行安装，不代改 IDE 或全局 MCP 配置。
2. 在另一个项目确认技能是否可见及可手动触发；检查实际加载的 `SKILL.md` 和脚本路径来自安装副本，而非开发目录。
3. 按主文检查 Python 及依赖，并运行脚本 `--help`。缺依赖应先说明并取得修复许可，不把 `.test-deps` 自动加到安装环境。
4. 分别记录“界面导入、实际加载、手动触发、自动触发”结果。自动触发可仅要求说明技能用法，明确不发起财务查询；未观察到的项目标记“待用户验收”。整理成功、离线测试或 `--help` 成功均不能证明安装及自动触发通过。

不为安装验收默认重跑真实账单；需要业务复测时，由用户明确账单和时间口径后再执行。

## 连接参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--mcp-url` | `https://datacenter.eccang.com/nexus/mcp/stream` | Streamable HTTP 端点 |
| `--mcp-timeout` | `60` | 连接、初始化及单次请求的超时秒数，必须为有限正数 |

将占位符替换为实际绝对路径，保留引号。用户的相对 CSV／输出路径按调用时的工作目录定位；不切换工作目录，也不把业务路径改按 Skill 根目录解释。

Windows PowerShell：

```powershell
& "<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>" --date-type datetime
```

POSIX shell：

```bash
"<Python解释器绝对路径>" -X utf8 "<Skill根目录绝对路径>/scripts/reconcile.py" --csv "<CSV绝对路径>" --date-type datetime
```

脚本自行连接 MCP，不读取 IDE 的 `mcpServers` 配置。一次对账复用一个会话，由 SDK 处理握手、会话标识及 JSON/SSE 响应。只发送查询必需参数，不上传 CSV 全文。默认验证 TLS，不自动降级到 HTTP。

## 必需工具

### queryOrderByReferenceNo

输入：`{"orderId": "<参考单号>"}`。

脚本按 CSV 顺序最多尝试 10 个不重复订单号。有效结果必须有公司编码、店铺账号和平台；空数组或 JSON `null` 表示未找到，多条归属或不完整结果立即停止。

支持的字段：
- `companyCode` 或 `company_code`。
- `userAccount` 或 `user_account`。
- `platform`。

### queryFmsTransaction

输入字段均为字符串：

| 字段 | 来源 |
|---|---|
| `companyCode` | 订单查询得到的公司编码 |
| `userAccount` | 订单查询得到的店铺账号 |
| `dateType` | `datetime → entry`，`transaction → settlement` |
| `startTime` | 所选日期范围起点，`yyyy-MM-dd HH:mm:ss` |
| `endTime` | 所选日期范围终点，`yyyy-MM-dd HH:mm:ss` |

日期范围使用 CSV 中已有站点时间口径，不额外转换时区。默认 `datetime → entry`，不强制询问；显式选择 `transaction → settlement` 时使用结算日期，缺失则停止。每次只用一种口径，切换后重新查询。公司、店铺、口径和起止范围存为不可变查询上下文，每次调用获得独立参数副本，附加筛选不能覆盖这些字段；报告和 Excel 使用实际查询上下文。

财务记录要求 `type` 为非空字符串、`total` 为有效有限数值或数值字符串。明确的空数组表示无财务记录；`null`、字段缺失及非法金额不是零值。

## 差异下钻工具与未启用接口

描述汇总及简版交易明细用于自动差异下钻：费用项汇总匹配即结束；不匹配且本地记录校验通过后先查描述，再查差异组对应的全部实际原始 types。全费用明细、记录总数及额外显式查询入口尚未启用；目前仅保留输入校验与共用适配，不能将契约表当成可用 CLI 功能。

| 工具 | 使用状态 | 必需参数 | 附加筛选 |
|---|---|---|---|
| `queryFmsTransactionDescription` | 差异时自动调用 | 与类型汇总相同的五个字段 | 无；按 type + description 汇总 |
| `queryFmsTransactionDetail` | 差异时自动调用 | 五个公共字段及 `types: array[string]` | types 使用远端原始类型，至少一个非空值 |
| `queryFmsTransactionAllFeeDetail` | 尚未启用，无 CLI 入口 | 五个公共字段 | 可选字符串 type、description、amazonOrderId、sellerSku、warehouseSku |
| `queryFmsTransactionCount` | 尚未启用，无 CLI 入口 | 五个公共字段 | 无；记录总数不是去重订单数 |

- 工具清单只发现一次，返回清单供会话内复用。初始仅校验两个基础工具，其余在调用时校验；不因未使用工具缺失或结构变化阻断汇总。
- 简版明细 `types` 是字符串数组，全费用明细 `type` 是单个字符串，不得混用。全费用可选条件取交集，空值在服务端意味着不筛选；适配器拒绝显式空值，调用者应省略未使用字段。
- 描述接口只传五个公共参数，不传 type；简版明细只增加 types，不传 description。简版结果没有 description，定位覆盖差异类型的完整返回集合。
- 简版明细同时保留 `dateTimeSite` 和 `postedDateSite`，`dateType` 只控制过滤口径。所选时间必须有效且在本次范围内；非所选字段可为 null 或范围外，不要求两者都落在范围内。不额外换算时区。
- 全费用接口明确不分页；其余接口没有公开分页或截断契约，不添加猜测参数、不对失败请求自动重试或扩大范围。实际输出包装、空值和大结果集仍待获准样例验证。

## 响应格式与失败处理

- 优先读取 MCP `structuredContent`；否则读取单个文本块中的 JSON。
- 支持 `data`、`result` 包装；归属仅接受唯一对象，类型汇总接受 `type/total` 对象或记录数组。描述、简版明细使用独立解析器，解包后必须为数组；空数组保留无记录语义，但仍需金额回勾。
- 描述记录必须有 `type/description/total`，description 仅接受字符串或 null，缺字段不是空描述。简版明细必须有 `amazonOrderId/type/total/dateTimeSite/postedDateSite`；订单号接受字符串或 null，金额必须有效且有限，响应类型必须属于请求的 types。时间非 null 时当前只接受 `yyyy-MM-dd HH:mm:ss`；其他格式先索取脱敏样例，不猜测时区或毫秒含义。
- 描述按原始 type 回勾类型汇总后才生成比较结果；简版明细及本地定位记录也分别回勾原始 type 和比较组。无法回勾不推断缺单。工具错误、业务失败、未知结构、超时、权限或会话错误均标记流程失败，不据此输出对账成功。
- 已得到汇总后发生失败，报告保留汇总金额与差异，但标题标记流程未完成、返回 `1`、禁止正常 Excel 导出；描述缺列或 CSV 单边类型为部分可比较，不抹掉已确认金额差异。
- 已有两份真实账单按入账口径完成汇总、描述及订单层查询的执行记录；不代表所有站点、结算口径、全费用或逐笔一致性已验收。其他返回包装、时间字段语义及大结果集仍需获准样例验证；字段不兼容时先取得脱敏样例，不推测含义。离线 SDK 内存服务测试不是线上业务验收。
- 当前不查询财务记录总数或全费用明细。汇总匹配时描述/订单状态为“未执行”；不匹配时按实际层级显示“完成／部分可比较／失败”。`compare_orders.py` CLI 转发相同主流程及退出状态。

## 安全边界

- 优先 HTTPS；显式配置 HTTP 时会显示传输未加密警告。
- 公司及店铺访问权限由服务端校验，不能只信任传入的标识。
- 现有连接方式不携带认证信息；若服务要求认证，应先配置受支持的认证方案，不绕过权限控制或恢复数据库直连。
- `.env` 保持忽略，不应随 Skill 分发；本工具不修改远端凭据或全局 MCP 配置。
