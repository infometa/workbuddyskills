# workbuddy-asset-migration

详细使用与排障文档。Skill 总览与命令参数请看 `SKILL.md`。

## 它到底搬了什么

权威清单看 `references/asset_inventory.md`。脚本会读这个文件作为白名单，**修改这个文件就能调整迁移范围，不用改代码**。

简要分类：
- **DB 表**：sessions / automations / automation_runs / automation_runtime_state / workspaces
- **文件资产**：skills/、memory/、settings.json、mcp.json、models.json、IDENTITY.md、SOUL.md、USER.md、plugins/known_marketplaces.json
- **可选**：projects/ 下的 conversation jsonl（`--no-conversations` 排除）、connectors/ 下的 OAuth 凭证（`--no-credentials` 排除）
- **不迁**：认证 token、日志、审计日志、二进制、缓存

## 端到端示例

### 同机 cn → intl，只迁 skills + memory + 不带会话

```bash
python scripts/export.py \
  --source ~/.workbuddy \
  --output /tmp/wb-cn.zip \
  --no-conversations --no-credentials

python scripts/import.py \
  --package /tmp/wb-cn.zip \
  --target ~/.workbuddy-ai \
  --dry-run
# 看 dry-run 输出没问题后正式跑
python scripts/import.py \
  --package /tmp/wb-cn.zip \
  --target ~/.workbuddy-ai
```

### 跨机器整套搬迁（含 conversation 历史）

```bash
# 旧机
python scripts/export.py --source auto --output ~/Desktop/wb.zip
# 把 wb.zip 传到新机
# 新机（确保 WorkBuddy 退出）
python scripts/import.py --package ~/Desktop/wb.zip --target auto
```

### 不同 user_id 的迁移（uid 重写）

如果源端登录 uid 是 `07b79ac1-...`，目标端是 `b32cee8d-...`，需要把数据"过户"到目标 uid：

```bash
python scripts/import.py \
  --package wb.zip \
  --target ~/.workbuddy-ai \
  --uid-map 07b79ac1-...=b32cee8d-...
```

效果：
- DB 里 sessions.user_id 列里所有 `07b79ac1-...` 替换为 `b32cee8d-...`
- `memory/07b79ac1-..._memory.md` 文件被重命名为 `memory/b32cee8d-..._memory.md`
- `connectors/07b79ac1-.../` 目录改名为 `connectors/b32cee8d-.../`

## OAuth 凭证重授权

如果导出时带了 `.credentials.json`（缺省行为是带），导入到另一台机器后，**很可能各 connector 的 OAuth token 已经失效**——服务端会拒绝陌生设备指纹的 refresh_token。处理：

1. 打开 WorkBuddy
2. 设置 → Connectors → 找到每个失败的 connector
3. 点"重新连接"或"重新授权"
4. 浏览器弹出授权页，正常登录即可

或者干脆 export 时加 `--no-credentials`，目标端从零授权。

## 回滚

每次 import 前脚本会把目标端要动的文件备份成 `<name>.bak-<timestamp>`：

```
~/.workbuddy/workbuddy.db.bak-20260607-154212
~/.workbuddy/settings.json.bak-20260607-154212
~/.workbuddy/mcp.json.bak-20260607-154212
~/.workbuddy/memory/<uid>_memory.md.bak-20260607-154212
...
```

回滚步骤：
1. 退出 WorkBuddy
2. 在目标根目录下：
   ```bash
   cd ~/.workbuddy
   ts=20260607-154212  # 改成实际备份时间戳
   for f in *.bak-$ts memory/*.bak-$ts; do
     mv "$f" "${f%.bak-$ts}"
   done
   ```
3. 启动 WorkBuddy 验证

备份**不会自动清理**，确认导入没问题后手动 `rm *.bak-*` 即可。

## DB 锁问题

如果脚本报：
```
[error] target DB is locked (WorkBuddy seems running). Exit and retry.
exit code: 2
```

说明 WorkBuddy 客户端进程还在跑（也包括隐藏在 dock 后台的）。退出步骤：
- macOS：`pkill -f WorkBuddy` 或 dock 右键退出
- 等几秒让 SQLite WAL flush，再重跑 import

## FAQ

**Q: 国内版和海外版的 DB schema 一样吗？**
A: 当前调研下完全一致。脚本用 `PRAGMA table_info` 做列交集 INSERT，即便未来一边加字段也能兼容（多出来的字段会丢弃并 warn）。

**Q: 我之前用过几个企业账号登录，memory 目录下有好几个 _memory.md，导入会怎么样？**
A: 多 uid 必须用 `--uid-map`，否则脚本拒绝执行。给每个源 uid 写一条映射（`--uid-map A=X --uid-map B=X` 把都合并到 X，或者 `A=X B=Y` 各自映射）。

**Q: 包里多大？**
A: 没 conversations 时一般几 MB（skills 多的话更大）；带 conversations 可能几百 MB 到几 GB。建议先 `--no-conversations` 试一次。

**Q: 国内 → 海外 后还能用国内的 connector / skill 吗？**
A: skill 本身是文件，能跑就能跑。connector 看具体的服务（比如腾讯文档的国内版账号对接海外版 WorkBuddy 可能没意义），按需重新授权或禁用。

**Q: 资产包里的 `.credentials.json` 含明文 token 吗，安全吗？**
A: 是的，含 access_token / refresh_token。**不要传到不可信通道**。推荐做法：用 `--no-credentials` 导出，到目标端重新授权。

## 跨机器迁移（v0.2 新增）

同机迁移（cn ↔ intl）什么都不用配，workspace 路径目标机一样能访问。**跨机器**就需要：

### 三个新参数

| 参数 | 作用 |
|---|---|
| `--with-workspaces` | 导出时多产出 `<output>-workspaces.zip`，含 workspace 文件树 |
| `--path-map src=dst` | 导入时按前缀重写路径。可重复，最长匹配优先 |
| `--target-os darwin\|win32\|linux` | 导入时按目标 OS 规范化路径分隔符 |

### 示例：mac → Win 完整迁移

```bash
# 源端（mac）：先 dry-run 看 workspace 大小
python scripts/export.py --source ~/.workbuddy --dry-run --with-workspaces

# 实际打包（生成两个 zip）
python scripts/export.py --source ~/.workbuddy --output ~/wb.zip --with-workspaces
# 产出：~/wb.zip + ~/wb-workspaces.zip

# 目标端（Win）：dry-run 看映射方案
python scripts/import.py --package wb.zip --target %USERPROFILE%\.workbuddy --dry-run \
    --target-os win32 \
    --path-map /Users/laurent=C:\Users\new

# 实际导入（含 workspace 文件解压）
python scripts/import.py --package wb.zip \
    --workspaces-package wb-workspaces.zip \
    --target %USERPROFILE%\.workbuddy \
    --target-os win32 \
    --path-map /Users/laurent=C:\Users\new
```

### workspace 默认排除什么

`references/workspace_excludes.md` 是完整白名单。简述：

- **排除**：`node_modules/`、`.git/`、`dist/`、`build/`、`__pycache__/`、`.venv/`、`*.sqlite`、`*.iso/*.dmg/*.vmdk` 等仓库型垃圾和大体积文件
- **不排除（默认带走）**：`.env`、`.envrc`、私钥（`*.pem/*.key/id_rsa`）、`secrets.*`、credentials、数据库 dump —— 这些是用户个人项目里的工作配置，默认全带

### 敏感物的告知机制

`--dry-run` 输出的 JSON 里有 `caveats` 段，**显式列出**有多少个 .env 文件、多少个私钥、多少个 secrets 文件。每条带 `note` 字段提示"Included by default. Exclude via --workspace-exclude-pattern if not wanted."

调用本 skill 的 agent **必须主动告知用户**这份清单，由用户决定是否要剔除：

```bash
# 如果用户说"别带 .env 文件"
python scripts/export.py --source ~/.workbuddy --with-workspaces \
    --workspace-exclude-pattern '*.env' \
    --workspace-exclude-pattern '*.envrc'
```

### 同机判定

manifest 里记录了 `source_os`、`source_hostname`、`source_home`。import 时三者全部等于本机 → 标记为 **same-machine** 模式：不要求 `--path-map`，不重写路径，workspace 包即便提供也按原路径解压。

### 路径重写覆盖范围

跨机模式下，以下位置都会按 `--path-map` 重写：

| 位置 | 处理 |
|---|---|
| `sessions.cwd` 列 | 字符串前缀替换 |
| `workspaces.path` 主键 | 主键 update，冲突时保留目标端 |
| `automations.cwds` JSON 数组 | 数组里每条字符串重写 |
| `automation_runs.source_cwd` | 字符串前缀替换 |
| `projects/<projectId>/` 目录名 | 按 `compressWorkspacePath(新cwd)` rename |
| `projects/*/*.meta.json` 的 cwd 字段 | json 字段重写 |
| `settings.json` 的 `defaultWorkspaceRoot` | json 字段重写 |
| `mcp.json` / `connectors/*/mcp.json` 的 `mcpServers.*.{command,cwd}` | json pattern 重写 |

**最容易忽略的一条**：`projects/<projectId>/` 目录名是 cwd 字面派生的（`compressWorkspacePath` 算法），cwd 一改这个目录名就对不上了——脚本会同步 rename。

## 重启提示

导入完成后 stdout 会自动打印：

```
============================================================
✓ 导入完成。请重启 WorkBuddy 客户端使改动生效。

重启后生效：db, settings.json, models.json, SOUL.md, USER.md, plugins/known_marketplaces.json
已热加载（不用重启）：mcp.json, IDENTITY.md
============================================================
```

判定依据在 `references/asset_inventory.md` 的 `<!-- machine:restart_required -->` 段。

## 内部实现说明

- `scripts/lib/detect.py`：根目录自动探测、cn/intl 判别、uid 提取
- `scripts/lib/manifest.py`：manifest.json 的 schema 与读写（v2 含 source_os/hostname/home）
- `scripts/lib/db.py`：ATTACH + 合并 SQL 生成器、`rewrite_path_columns` 跨机路径重写
- `scripts/lib/fs.py`：文件树合并、`rename_project_dirs` 跨机目录改名、workspace 解压
- `scripts/lib/configs.py`：JSON 语义合并、`rewrite_paths_in_json` 字段重写
- `scripts/lib/pathmap.py`：跨 OS 路径前缀映射器、`compress_workspace_path` 算法
- `scripts/lib/walk.py`：workspace 扫盘、glob 排除、du 统计、敏感物检测
- `scripts/lib/report.py`：dry-run 渲染、stdout 报告、写盘报告、重启提示
- `scripts/test_migration.py`：22 个 fixture 端到端测试

## 测试

```bash
cd workbuddy-asset-migration
python -m unittest scripts/test_migration.py -v
```
