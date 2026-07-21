---
name: workbuddy-asset-migration
description: 在 WorkBuddy 国内版（~/.workbuddy/）和海外版（~/.workbuddy-ai/）之间，或跨机器之间，迁移用户个人资产（skills、memory、conversations、automations、sessions、MCP/connectors 配置、IDENTITY/SOUL/USER 等）。导出为单 zip 包，导入端默认只合并不覆盖。用于"用户在国内版用了很久、想切到海外版（或反过来），不想从零开始"的场景。支持 `--with-workspaces` 把项目工作目录一起搬走，`--path-map` 跨机器重写路径。触发关键词：WorkBuddy 迁移、资产迁移、国内版/海外版切换、换电脑搬家。
description_zh: WorkBuddy 国内版/海外版/跨机器之间迁移个人资产
description_en: Migrate WorkBuddy assets between CN/AI editions or across machines
version: 0.2.0
allowed-tools: Read,Write,Bash
---

# WorkBuddy 资产迁移

把一台机器（或一个 WorkBuddy 变体）上的个人资产打包，搬到另一台机器（或另一个变体）。导入端如果已经有数据，默认走"合并、不覆盖"策略，不会把现有的东西冲掉。

## 适用场景

- 国内版 `~/.workbuddy/` → 海外版 `~/.workbuddy-ai/`（同机或跨机）
- 反向：海外版 → 国内版
- 同变体跨机器搬家（旧 Mac → 新 Mac、Mac → Linux）

## 快速开始

```bash
# 1. 在源端导出
python scripts/export.py --source auto --output ~/Desktop/wb-assets.zip

# 2. 把 zip 拷到目标机器（airdrop / scp / U 盘均可）

# 3. 在目标端导入（先 dry-run 看会做什么）
python scripts/import.py --package ~/Desktop/wb-assets.zip --target auto --dry-run
python scripts/import.py --package ~/Desktop/wb-assets.zip --target auto
```

**重要**：导入前请退出 WorkBuddy 客户端，否则 SQLite 写锁会拿不到，脚本会直接报错退出。

## 命令参数

### export.py
| 参数 | 说明 |
|---|---|
| `--source <path\|auto>` | 源根目录；auto 按 `WORKBUDDY_CONFIG_DIR` → `~/.workbuddy` → `~/.workbuddy-ai` 顺序探测 |
| `--output <path>` | 输出 zip 或目录（缺省 `./workbuddy-assets-<yyyymmdd-HHMM>.zip`） |
| `--no-conversations` | 不带 `projects/*.jsonl`（包体可大幅缩小） |
| `--no-credentials` | 不带 `.credentials.json`（推荐跨机器使用） |
| `--no-archive` | 输出目录树而非 zip |

### import.py
| 参数 | 说明 |
|---|---|
| `--package <zip\|dir>` | 必填，迁移包路径 |
| `--target <path\|auto>` | 目标根目录，auto 探测规则同 export |
| `--overwrite` | 冲突时覆盖（默认 skip）；自动备份 `.bak-<ts>` |
| `--dry-run` | 只打印计划，不动文件 |
| `--uid-map src=dst` | 重写 user_id（memory 文件名、connectors 子目录、sessions.user_id）|
| `--no-conversations` / `--no-credentials` | 即便包里有也排除 |
| `--skip-db` / `--skip-skills` / `--skip-configs` | 分类排除（运维用） |

## 冲突合并策略

| 资产 | 默认（无 --overwrite） |
|---|---|
| DB 表（sessions/automations/...） | `INSERT OR IGNORE`，同 id 保留导入端 |
| Skills 同名目录 | skip |
| memory/{uid}_memory.md | 追加分隔符后 append，绝不删原内容 |
| settings.json/mcp.json/models.json | 浅 merge，导入端 key 优先 |
| IDENTITY.md/SOUL.md/USER.md | 已存在时落 `*.imported.md`，让用户手工合并 |
| projects/*.jsonl 同 session | skip |
| .credentials.json | 走 `--no-credentials` 推荐排除（OAuth token 跨机器易失效）|

## 风险与限制

- 不迁移：认证 token（在 CodeBuddyExtension 目录下，机器/账号绑定）、日志、审计日志、`binaries/`、缓存
- OAuth token：跨机器、跨变体大概率失效，建议导入后到 connector 面板手动重新授权
- 多 uid：同机器多账号登录过时，必须用 `--uid-map` 显式映射，否则脚本拒绝执行避免数据混乱
- 备份：所有 `.bak-<ts>` 文件不自动清理，导入结束时 stdout 会列出位置和大小，自行决定何时删

## 跨机器 / 带 workspace（v0.2）

### 同机迁移（cn ↔ intl）—— 默认场景

不用动 workspace，对话和 workspace 是解耦的（同一台机器上 cn 和 intl 看到的是同一份 workspace 文件）。直接：
```bash
python scripts/export.py --source ~/.workbuddy --output ~/wb.zip --no-credentials
python scripts/import.py --package ~/wb.zip --target ~/.workbuddy-ai
```

### 跨机器迁移

跨机器**只迁对话不够**——目标机上没有源机的 workspace 路径，对话点开会失败。两种选择：

1. **只迁对话元数据**（用户接受历史只是用来查阅，不能直接打开）：
   ```bash
   python scripts/import.py --package wb.zip --target ~/.workbuddy \
       --path-map /Users/old=/Users/new --target-os darwin
   ```
   sessions.cwd / workspaces.path / automations.cwds / meta.json 全部按 `--path-map` 重写，新机上找得到对应工作目录就能继续。

2. **连 workspace 文件一起搬**（用户要把项目代码也带过去）：
   ```bash
   # 源端
   python scripts/export.py --source ~/.workbuddy --output ~/wb.zip \
       --with-workspaces                 # 多产出一个 ~/wb-workspaces.zip
   # 目标端
   python scripts/import.py --package ~/wb.zip \
       --workspaces-package ~/wb-workspaces.zip \
       --target ~/.workbuddy \
       --path-map /Users/old=/Users/new --target-os darwin
   ```

### Agent 调用流程（dry-run JSON）

skill 自身不提问，由调用它的 host agent 负责跟用户交互。流程：

1. `export.py --source auto --dry-run --with-workspaces` → stdout 输出 JSON 计划
2. agent 解析 JSON，重点呈现给用户：
   - 主包大小（一般几 MB）
   - **每个 workspace 的 du、排除后大小、预估 zip 大小**
   - **`caveats` 段里的敏感物清单**（.env 文件数、私钥数、symlink 数等）—— 这些**默认会被带走**，agent 必须主动告知用户，让用户决定是否要用 `--workspace-exclude-pattern '*.env'` 剔除
3. 用户决策后，agent 再调一次 export（不带 dry-run）正式打包
4. 用户在另一台机器接收包后，agent 跑 `import.py --dry-run` 看路径映射建议（自动从 manifest 的 `source_home` 推断），用户确认 `--path-map` 规则后正式 import

### `--with-workspaces` 默认排除的内容

按 `references/workspace_excludes.md` 的清单——主要是 `node_modules/`、`.git/`、`dist/`、`__pycache__/`、`.venv/`、构建产物、缓存、本地 sqlite、镜像文件、`*.log` 等仓库型垃圾。

**不在默认排除清单**的：`.env`、私钥、secrets、credentials 等——这些是用户个人资产，默认全带，但 dry-run 会在 caveats 里列出，让 agent 转告用户做决定。

### 重启提示

导入完成后 stdout 会自动打印"请重启 WorkBuddy"。哪些资产需要重启：DB 表、`models.json`、`settings.json`、`SOUL.md`、`USER.md`、`plugins/known_marketplaces.json`。哪些热加载：`mcp.json`、`IDENTITY.md`、`memory/`、`skills/`。

## 内部参考

- 资产清单白名单：`references/asset_inventory.md`
- workspace 排除规则：`references/workspace_excludes.md`
- 完整 FAQ 与回滚步骤：`README.md`
