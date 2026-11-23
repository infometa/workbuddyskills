---
name: hithink-finance-shared
description: '管理 hithink-finance CLI 的 OAuth/API Key 登录、配置、自检、版本更新、卸载和 Skills 安装/同步/修复；查询 CLI 可用能力及通用输出规则。'
---

# hithink-finance-shared

CLI 认证、配置、输出和生命周期入口。宿主优先依据各内置 Skill 的 description 选择业务域；此处提供通用规则及需要时的辅助选路。

## 前置条件表

| 条件                            | 操作                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------- |
| 第一次接触此 CLI 或怀疑版本漂移 | 运行 `hithink-finance version --format json`；需要发现未知命令时再读取 `capabilities` |
| 需要机器读取                    | 始终加 `--format json`                                                                |
| 结果可能很大                    | 使用命令声明的 `--output <path>` 落盘；远端 stdout 只返回摘要                         |
| 需要远端同花顺金融数据服务      | 先用 `auth status` 复用当前有效凭据；首次登录默认推荐 OAuth                           |

## 快速决策

| 用户意图                   | 首选命令 / 路由                                                                                                                                                                                    |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 检查 CLI 是否可用或版本    | `hithink-finance version --format json`                                                                                                                                                            |
| 查看真实能力清单           | `hithink-finance capabilities --format json`                                                                                                                                                       |
| 查看某个命令参数契约       | `hithink-finance schema <capability-id> --format json`                                                                                                                                             |
| 首次登录（默认推荐 OAuth） | `hithink-finance auth login --method oauth`；先用 `auth status` 复用当前有效凭据                                                                                                                   |
| 显式选择 API Key 登录      | 先复用统一来源的 Key，缺失时在 https://fuyao.aicubes.cn/admin/ 获取；用 `hithink-finance auth login --method api-key --api-key-stdin --format json` 登录，交互终端使用 `--method api-key` 隐藏输入 |
| 检查认证状态               | `hithink-finance auth status --format json`                                                                                                                                                        |
| 查看非敏感配置             | `hithink-finance config show --format json`                                                                                                                                                        |
| 诊断运行环境               | `hithink-finance doctor --format json`                                                                                                                                                             |
| 同步/修复配套 Skills       | `hithink-finance skills status --format json` 或 `hithink-finance skills sync --format json`                                                                                                       |
| 更新 CLI                   | `hithink-finance update --check --format json` 只检查；确认后用 `hithink-finance update --format json` 更新到最新版                                                                                |
| 预览卸载                   | `hithink-finance uninstall --plan --format json`                                                                                                                                                   |

## 业务辅助选路

明确的业务请求由宿主依据领域 Skill 的 description 直接选择。需要区分范围或选择其他业务域时，用下表补充定位；随后读取该领域 Skill 和目标命令 reference。

| 任务范围                                                                                                        | 领域 Skill                                                               |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 标的识别和代码表路由。目标是把自然语言名称、ticker、thscode 或代码表需求变成后续可执行的证券标识。              | [hithink-finance-symbol](../hithink-finance-symbol/SKILL.md)             |
| 普通行情和本地行情派生能力。优先使用本地库覆盖的历史/面板能力，必要时走远端同花顺金融数据服务。                 | [hithink-finance-market](../hithink-finance-market/SKILL.md)             |
| 特色榜单和事件型数据入口。强调窗口约束和榜单口径，不替代普通行情或财报。                                        | [hithink-finance-special-data](../hithink-finance-special-data/SKILL.md) |
| 资讯查询入口。保留正文 HTML、链接、字符串标识、空值与原有顺序。                                                 | [hithink-finance-news](../hithink-finance-news/SKILL.md)                 |
| 新股资料与发行阶段查询入口。区分沪深、北交所和港股；港股发行标识来自日历。                                      | [hithink-finance-ipo](../hithink-finance-ipo/SKILL.md)                   |
| A 股财务报表和指标入口。把报告期、时间窗口和 limit 约束转成稳定命令。                                           | [hithink-finance-financials](../hithink-finance-financials/SKILL.md)     |
| 指数目录、指数成分和指数行情入口。只处理指数对象及其成分关系。                                                  | [hithink-finance-index](../hithink-finance-index/SKILL.md)               |
| 基金资料、机构与经理、财务、业绩、披露和场内行情入口。根据基金类型、标识来源与市场形态选择稳定命令。            | [hithink-finance-fund](../hithink-finance-fund/SKILL.md)                 |
| 期货公开资料和行情入口。按完整 thscode、品种与日期语义选择稳定命令。                                            | [hithink-finance-futures](../hithink-finance-futures/SKILL.md)           |
| 期权公开资料和行情入口。按完整 thscode 和固定行情参数查询。                                                     | [hithink-finance-options](../hithink-finance-options/SKILL.md)           |
| A 股当前估值快照入口。按用户给出的股票代码批量返回服务端口径的估值指标，不自行补算或扩展指标。                  | [hithink-finance-valuation](../hithink-finance-valuation/SKILL.md)       |
| 本地数据生命周期和 SQL 入口。负责让数据可用、可校验、可导出，而不是解释所有研究结论。                           | [hithink-finance-data](../hithink-finance-data/SKILL.md)                 |
| 研究工作流路由。它不拥有独立 `research` 命令，而是指导 Agent 组合 data、db 和 market panel 产出可复现数据证据。 | [hithink-finance-research](../hithink-finance-research/SKILL.md)         |

## References

| 需要了解                            | 读取                                                    |
| ----------------------------------- | ------------------------------------------------------- |
| JSON 输出、大结果、安全规则         | [global-rules.md](references/global-rules.md)           |
| 全局凭据、一次性迁移、配置          | [auth-and-config.md](references/auth-and-config.md)     |
| version、doctor、update、uninstall  | [lifecycle.md](references/lifecycle.md)                 |
| skills status/sync/remove           | [skills-management.md](references/skills-management.md) |
| 查询worker状态/停止、启动与失败处理 | [query-worker.md](references/query-worker.md)           |

## 权限表

| 能力                                                                                  | 凭据                                                         |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| 本地 data/db/market panel                                                             | 本地读取和导出通常无需认证；远端初始化或同步使用当前有效凭据 |
| symbol/market remote/special/ipo/news/financials/index/fund/futures/options/valuation | 使用当前启用的 OAuth 或 API Key                              |
| skills/update/uninstall                                                               | 需要本机文件系统权限；不要写全局非 CLI 管理目录              |

## 边界声明

- 用户可以为了便利把 API Key 提供给 Agent 上下文；Agent 不复述，并提示聊天平台可能保留消息记录。不要把 Key 写入命令参数、项目配置、日志、Markdown、Git 或其他可共享内容；本地配置优先 stdin、用户级持久来源或系统凭据库。
- 不要把 stderr 更新提示、诊断详情或完整大数据结果当作最终答案原样展开。
