# 跨平台家目录路径处理铁律

> 本文件是团队级共用规则（团队协作机制铁律引用本文件），**任何成员在文档或执行过程中涉及 `~/.workbuddy/...` 这类"用户家目录下的固定路径"时，都必须遵循本文件的处理方式**，不要在各自文档里各写一套、各留各的坑。

## 一、核心原则

**`~` 不是一个在所有运行环境下都指向同一个真实目录的符号。** 本专家团的Agent 可能运行在三类环境下，`~` 在其中任意一种下的实际展开结果都不一样：

| 运行环境 | `~` 实际展开到哪 | 是否等于 WorkBuddy 客户端真实数据目录 |
|---|---|---|
| macOS / Linux（原生） | `/Users/<用户名>` 或 `/home/<用户名>` | ✅ 是，直接可用 |
| Windows 原生（PowerShell / CMD） | 视工具实现而定，**很多场景下不会被展开**，且没有统一约定 | ❌ 不可靠，不要写死 `~` |
| **Windows + WSL（Bash 工具）** | WSL 自己虚拟的 `/home/<wsl用户>` | ❌ **不是**，这是最隐蔽的坑——WorkBuddy 桌面客户端是原生 Windows 程序，真实数据写在 `C:\Users\<用户名>\.workbuddy\`，WSL 的 `~` 与之完全不相关，是两个独立文件系统下的两个目录 |

**后果**：如果不做区分，直接对Windows/WSL 环境执行 `~/.workbuddy/xxx`，**大概率表现为"文件不存在/读不到数据"，而不会报出"路径错了"这种明确错误**——这种静默失败最容易被误判成"用户没登录""数据未生成"等错误结论，比直接报错更危险。

## 二、三种环境的正确路径写法（一一对应表）

| 用途 | macOS / Linux | Windows 原生（PowerShell/CMD） | Windows + WSL（Bash） |
|---|---|---|---|
| WorkBuddy 用户数据库 | `~/.workbuddy/workbuddy.db` | `%USERPROFILE%\.workbuddy\workbuddy.db`（CMD）/ `$env:USERPROFILE\.workbuddy\workbuddy.db`（PowerShell） | `/mnt/c/Users/<用户名>/.workbuddy/workbuddy.db` |
| WorkBuddy session 文件 | `~/.workbuddy/app/sessions.json` | `%USERPROFILE%\.workbuddy\app\sessions.json` | `/mnt/c/Users/<用户名>/.workbuddy/app/sessions.json` |
| 已安装 Skill 目录 | `~/.workbuddy/skills/` | `%USERPROFILE%\.workbuddy\skills\` | `/mnt/c/Users/<用户名>/.workbuddy/skills/` |
| 已安装专家目录 | `~/.workbuddy/experts/` | `%USERPROFILE%\.workbuddy\experts\` | `/mnt/c/Users/<用户名>/.workbuddy/experts/` |
| 打包/导出输出目录 | `~/.workbuddy/skillhub-outputs/` | `%USERPROFILE%\.workbuddy\skillhub-outputs\` | `/mnt/c/Users/<用户名>/.workbuddy/skillhub-outputs/`（或直接用 WSL 自己的 `~/.workbuddy/skillhub-outputs/`，因为这是**新建**的输出目录，不要求必须和 Windows 原生路径重合，见下方「新建输出目录」的例外说明） |

> `<用户名>` 需要实际探测获得（如执行 `whoami` 或读环境变量），不能凭空猜测拼写。

## 三、「读取已存在数据」vs「新建输出目录」——两类场景的风险等级不同

- **读取已存在数据**（如 wb_user_id、已安装 Skill 列表）：**必须严格对应真实数据所在目录**，路径不对会导致读取失败（静默或报错），**必须按上表分环境处理，不能偷懒**。
- **新建输出目录**（如打包产物、本地导出兜底）：目录是当前会话临时创建的，只要能被用户之后找到即可，**WSL 环境下用 WSL 自己的 `~` 建目录也是可以接受的**（只是意味着产物在 WSL 文件系统里，用户需要知道去哪找，不算功能性错误）；但仍**建议**优先尝试落到 Windows 原生可见目录（`/mnt/c/Users/<用户名>/...`），方便用户在 Windows 原生环境直接看到产物。

## 四、判断当前运行环境的方式

不确定自己当前处于哪种环境时，按以下顺序探测（不要凭猜测直接选路径）：

1. 执行 `uname -s` 或检查 `$OSTYPE`：返回 `Linux` 且`/mnt/c/` 目录存在 → WSL；返回 `Darwin` → macOS；返回 `MINGW`/`MSYS` → Git Bash（此时 `~` 通常已正确映射到 `%USERPROFILE%`，可按 macOS/Linux 那一列直接用）
2. 若工具本身运行在 PowerShell/CMD（非 Bash 环境）→ 按"Windows 原生"列处理
3. 仍无法判断 → **两套路径都尝试一遍**，哪个能读到数据就用哪个，不要只试一次就下结论"读不到"

## 五、`{baseDir}` 模板变量与本规则无关，不要混淆

各 Agent 文档中出现的 `{baseDir}`（如 `{baseDir}/scripts/pack_and_hash.sh`）是**运行时由平台注入的模板变量**，代表"本专家团插件自身的安装目录"，**不是**本文件讨论的"硬编码 `~/.workbuddy/...` 路径"问题——`{baseDir}` 本身已经是跨平台安全的，不需要额外做操作系统判断。只有当 Agent 文档里**直接写死** `~/.workbuddy/...`（而不是用 `{baseDir}` 变量）时，才需要按本文件的规则处理。

## 六、本专家团内需要应用本规则的已知位置

| 文件| 涉及路径 | 风险等级 |
|---|---|---|
| `skillhub-ops-expert.md` 步骤 5.1 | `~/.workbuddy/workbuddy.db` / `~/.workbuddy/app/sessions.json`（读取 wb_user_id） | 高（读取已存在数据，静默失败会误判用户未登录） |
| `skillhub-ops-expert.md` 步骤 3 / 步骤 5.6 | `~/.workbuddy/skillhub-outputs/`（打包输出/本地兜底导出） | 低（新建输出目录，按本文件§三处理） |
| `skill-tester/SKILL.md`（已安装 Skill 发现） | `~/.workbuddy/skills/` | 高（读取已存在数据，静默失败会误判"没有可用技能"） |
| `expert-creator/SKILL.md` / `skill-creator/SKILL.md` | `~/.workbuddy/experts/`、`~/.workbuddy/skills/{name}/`（默认输出目录） | 低（新建输出目录） |
| `wenjuan-fallback-submit`（问卷提交脚本输出目录） | `~/.workbuddy/skillhub-outputs/wenjuan` | 低（新建输出目录） |

## 七、自检口令

任何成员在执行前，看到自己要读取或写入一个含`~/.workbuddy/` 的路径时，先问自己：
1. 这是"读取已存在数据"还是"新建输出目录"？→ 决定按§三哪一档处理
2. 当前运行环境是哪一种（§四判断）？→ 决定用§二哪一列的路径
3. 如果是"读取已存在数据"且读不到 → **先怀疑是路径/环境问题，再怀疑是数据本身不存在**，两套路径都试过之后仍读不到，才能下"数据确实不存在"的结论
