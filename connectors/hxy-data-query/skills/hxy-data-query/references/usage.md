# 沪小游调用说明

## 运行与凭证

技能包含 Python 3.8+ 标准库脚本，无需 pip 安装。先将工作目录切到本技能目录，再执行 `python3 scripts/hxy_query.py --help`。Windows 可以使用 `py -3` 替代 `python3`。需要能够通过 HTTPS 访问沪小游服务。

已有沪小游 MCP 连接器时，优先直接调用工具，凭证由连接器注入。独立运行脚本时，由用户在运行环境配置 `TENANT_KEY` 与 `TENANT_SECRET`，或提供本人可访问的私有 JSON 文件：

```json
{
  "tenantKey": "填写自己的租户 Key",
  "tenantSecret": "填写自己的租户密钥"
}
```

上面仅表示配置结构，不是真实凭证。由用户在自己的配置界面或本地编辑器填写，不要求用户把密钥发送到对话中；不要把文件放进技能包、项目仓库或共享目录。macOS/Linux 文件权限需为 `600`，脚本不创建或修改凭证文件。

```bash
python3 scripts/hxy_query.py --credentials-file "/绝对路径/credentials.json" doctor
python3 scripts/hxy_query.py --credentials-file "/绝对路径/credentials.json" resources
```

`--credentials-file` 放在子命令前，显式指定时优先于环境变量；之后每次调用都使用同一配置方式。不自动读取 WorkBuddy 或其他应用的配置。环境变量只需配置一次，后续调用不在命令行追加真实密钥。

`doctor` 只检查配置格式，不访问网络。无凭证时输出 `AUTH_REQUIRED` 并退出，不代表服务故障，也不代表查询结果为空。连接器配置的密钥不会自动变成脚本环境变量；两种入口选择其一即可。

macOS 上如果 Python 没有附带 CA 且未显式配置证书位置，脚本会使用系统的 `/etc/ssl/cert.pem`，仍然验证证书和域名。如果提示 `TLS_ERROR`，修复当前 Python 的可信 CA 配置（标准环境变量 `SSL_CERT_FILE` 支持指定管理员提供的 CA 文件），或使用证书配置正常的系统 Python。不要关闭 HTTPS 验证或下载来历不明的证书。脚本不会安装运行时、变更系统证书或自动重试。

## 工具和命令对应

| 意图 | MCP 工具 | 脚本命令 | 返回内容 |
|---|---|---|---|
| 发现授权资源 | `hxy_list_resources({})` | `resources` | `resources`，含标识、名称、可用返回方式及默认方式 |
| 获取参数说明 | `hxy_describe_resource({"resourceCodes":["exhibition.list","activity.list"]})` | `describe exhibition.list activity.list` | `resources`，含扁平参数、实际字段、授权、组合约束和示例 |
| 查询 | `hxy_query({...})` | `query --request-json '{...}'` | 数量、名称或原有列表/对象，以后台授权为准 |

使用真实服务返回的标识，不推断名称相似的接口已授权。单次 `describe` 最多 10 个资源；脚本每次调用执行一次 MCP 初始化、完成通知和一次工具调用，无全目录预加载、无自动翻页、无权限缓存。

## 数量和时间示例

用户询问“本月新增商业展会有多少”：先确认 `exhibition.list` 可用并读取说明，将用户所在业务月份转换成上海时区的完整范围。以下仅以 2026 年 10 月为例：

```bash
python3 scripts/hxy_query.py describe exhibition.list
python3 scripts/hxy_query.py query --request-json '{"resourceCode":"exhibition.list","filters":{"queryMode":"count","timeType":"create","startTime":"2026-10-01 00:00:00","endTime":"2026-11-01 00:00:00"}}'
```

也可把完全相同的 JSON 对象传给原生 `hxy_query`。`queryMode` 位于 `filters` 内；以上范围按创建时间统计，包含 10 月 1 日零点，不包含 11 月 1 日零点。不能描述为“10 月举办的展会数量”。

脚本返回 `isError:false` 后，从 `result.total` 读取实际数量，结合 `result.meta` 解释口径。回答例如“按系统创建时间，2026 年 10 月新增商业展会为本次返回的 total 条，范围为上海时间 10 月 1 日零点至 11 月 1 日零点，不含终点”。把“本次返回的 total”替换为实际数值，不生成示例数字冒充真实查询。

## 名称与分页示例

仅在资源返回的 `modes` 包含 `names` 时使用：

```bash
python3 scripts/hxy_query.py query --request-json '{"resourceCode":"activity.list","filters":{"queryMode":"names"},"page":{"currentPage":1,"pageSize":10}}'
```

输出中的 `result.records` 保留服务端授权的原名称字段，`result.pagination` 表示当前分页。活动当前名称字段是 `activityName`，仍以实时 `responseFields` 和实际结果为准。不要补出未返回的 ID、电话、地址或详情。只有用户需要完整列表时才继续分页；不同记录可以同名，不能按名称去重。

## 范围筛选示例

酒店渠道参数放在 `filters.hotelChannel`，例如 `"携程"`。只有当前角色授权且资源支持时才能使用；“携程、美团”的记录会命中“携程”。省略筛选的语义以该资源当前角色说明为准，不视为解除授权。授权不允许时呈现拒绝原因，不通过换接口、换模式或删除筛选获得数据。

`timeType/startTime/endTime` 与 `lastTime` 互斥。关键词、区域、分类、等级等参数名和位置全部来自 `parameters`；不要把一个资源的筛选项复制到另一个资源。计数不使用分页；名称/列表每页默认 10、上限 100。

## 结果与失败

脚本将服务端结构化结果放入 `result`，保留 `isError`。服务端工具错误中的 `code/message/errorCode/parameter` 均在 `result` 内，不靠中文错误文本推断类别。成功退出码为 0，所有失败为 1；`--help` 是帮助文本并以 0 退出。

区分没有授权、凭证失效、参数错误、网络失败和真实数量为 0。任何 `isError:true` 都没有可用于统计的成功结果；不要把错误对象中的 `code` 当作业务数量。部分资源失败时，只报告已成功的部分及缺失原因。

可以在没有凭证、没有网络时检查帮助、配置结构和输入错误，但这些检查不验证业务查询，也不代表 WorkBuddy 官方沙箱评测已通过。真实查询评测必须提供有效的评测租户凭证和相应数据权限，不能把密钥内置进公开包。
