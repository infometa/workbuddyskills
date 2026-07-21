# bdpan CLI 命令快速参考

## 认证命令

### login - 登录授权

> **⛔ Agent 必须通过登录脚本执行登录，禁止直接调用 `bdpan login`。详见 [SKILL.md](../SKILL.md) 安全约束。**

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/login.sh
```

脚本内置了安全免责声明和完整的 OOB 授权流程。无论 GUI 或非 GUI 环境，统一使用此脚本。

### logout - 注销登录

```bash
bdpan logout
```

清除本地存储的认证信息（`~/.config/bdpan/config.json`）。

### uninstall - 完全卸载

```bash
bash ${CLAUDE_SKILL_DIR}/scripts/uninstall.sh
```

完全卸载 bdpan CLI，自动执行以下操作：
1. 注销登录并清除授权信息
2. 删除配置目录（`~/.config/bdpan/`）
3. 删除 bdpan 二进制文件（`~/.local/bin/bdpan`）

**选项：**
- `--yes, -y` - 跳过确认提示（自动化场景）

**环境变量：**
| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BDPAN_INSTALL_DIR` | 二进制安装目录 | `~/.local/bin` |
| `BDPAN_CONFIG_DIR` | 配置文件目录 | `~/.config/bdpan` |

### whoami - 查看认证状态

```bash
bdpan whoami
```

显示当前登录状态、用户名和 Token 有效期信息。

**已登录时输出：**
```
认证状态: 已登录
用户名: your_username
Token 有效期至: 2026-04-04 10:30:00
```

**选项：**
- `--json` - JSON 格式输出

---

## 文件操作命令

### upload - 上传文件

```bash
bdpan upload <local> <remote>
```

| 参数 | 说明 |
|------|------|
| `local` | 本地文件或文件夹路径 |
| `remote` | 网盘目标路径（相对于 `/apps/bdpan/`） |

**示例：**
```bash
# 单文件上传
bdpan upload ./report.pdf report.pdf

# 文件夹上传
bdpan upload ./project/ project/

# 上传到子目录
bdpan upload ./data.tar.gz backup/data.tar.gz
```

**选项：**
- `--json` - JSON 格式输出上传结果

### download - 下载文件

```bash
bdpan download <remote> <local> [选项]
```

| 参数 | 说明 |
|------|------|
| `remote` | 网盘文件/文件夹路径（相对于 `/apps/bdpan/`）**或**百度网盘分享链接 |
| `local` | 本地保存路径 |

**选项：**
| 选项 | 说明 |
|------|------|
| `-p` | 提取码（用于分享链接，如果链接中未包含） |
| `-t` | 自定义转存目录（相对路径自动拼接 `/apps/bdpan`，绝对路径直接使用） |
| `--json` | JSON 格式输出下载结果 |

**示例：**
```bash
# 单文件下载
bdpan download report.pdf ./downloaded-report.pdf

# 文件夹下载
bdpan download project/ ./project-restore/

# 从分享链接下载（链接中包含提取码）
bdpan download "https://pan.baidu.com/s/1xxxxx?pwd=abcd" ./downloaded/

# 使用 -p 参数单独传入提取码
bdpan download "https://pan.baidu.com/s/1xxxxx" ./downloaded/ -p abcd

# 使用 -t 参数自定义转存目录
bdpan download "https://pan.baidu.com/s/1xxxxx?pwd=abcd" ./downloaded/ -t my-folder
```

**分享链接下载说明：**
- 自动识别分享链接格式 `https://pan.baidu.com/s/1{surl}?pwd={pwd}`
- 分享文件会先转存到 `/apps/bdpan/{日期}/` 目录（或使用 `-t` 指定的目录）
- 然后下载到指定的本地路径

### transfer - 转存分享文件到网盘（不下载到本地）

```bash
bdpan transfer <分享链接> [选项]
```

| 参数 | 说明 |
|------|------|
| `分享链接` | 百度网盘分享链接 |

**选项：**
| 选项 | 说明 |
|------|------|
| `-p` | 提取码（如果链接中未包含） |
| `-d` | 目标目录（相对路径自动拼接 `/apps/bdpan`，默认为应用根目录） |
| `--json` | JSON 格式输出转存结果 |

**示例：**
```bash
# 基本用法 - 转存到应用根目录 /apps/bdpan/
bdpan transfer "https://pan.baidu.com/s/1xxxxx" -p abcd

# 提取码在链接中
bdpan transfer "https://pan.baidu.com/s/1xxxxx?pwd=abcd"

# 指定目标目录
bdpan transfer "https://pan.baidu.com/s/1xxxxx" -p abcd -d my-folder/

# JSON 输出
bdpan transfer "https://pan.baidu.com/s/1xxxxx" -p abcd --json
```

**与 download 的区别：**
- `transfer` 仅将分享文件转存到自己的网盘，不下载到本地
- `download` 会先转存再下载到本地路径
- 适用于只需要保存到网盘、不需要本地副本的场景

### ls - 查看文件列表

```bash
bdpan ls [path]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `path` | 要查看的目录路径 | 根目录 |

**选项：**
- `--json` - JSON 格式输出

**示例：**
```bash
# 查看根目录
bdpan ls

# 查看子目录
bdpan ls backup

# JSON 输出
bdpan ls --json
```

**输出格式：**
```
类型    大小          修改时间              文件名
------  ------------  --------------------  --------
目录     -            2026-02-20 10:30:00  documents
文件    1.5 MB        2026-02-25 15:20:00  readme.txt
文件    256 KB        2026-02-24 09:15:00  config.yaml

共 3 项
```

### share - 创建分享链接

```bash
bdpan share <path>
```

| 参数 | 说明 |
|------|------|
| `path` | 要分享的文件或文件夹路径 |

**示例：**
```bash
# 分享文件
bdpan share report.pdf

# 分享文件夹
bdpan share project

# JSON 输出
bdpan share --json report.pdf
```

**输出格式：**
```
分享链接创建成功!
链接: https://pan.baidu.com/s/1xxxxxxx
提取码: abcd
有效期: 7 天
```

### search - 搜索文件

```bash
bdpan search <关键词> [选项]
```

| 参数 | 说明 |
|------|------|
| `关键词` | 搜索关键词（必填） |

**选项：**
| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--category` | int | `0` | 文件类型筛选：1=视频, 2=音频, 3=图片, 4=文档, 5=应用, 6=其他, 7=种子 |
| `--page-size` | int | `5` | 每页数量（最大 50） |
| `--page` | int | `1` | 页码 |
| `--no-dir` | bool | `false` | 仅显示文件，排除文件夹 |
| `--dir-only` | bool | `false` | 仅显示文件夹 |
| `--json` | - | - | JSON 格式输出 |

> `--no-dir` 和 `--dir-only` 互斥，不能同时使用。

**示例：**
```bash
# 搜索文件
bdpan search report

# 搜索图片类型文件
bdpan search photo --category 3

# 搜索文件，排除文件夹，每页 10 条
bdpan search data --no-dir --page-size 10

# 翻页
bdpan search report --page 2

# JSON 输出
bdpan search report --json
```

**输出格式：**
```
找到 15 个结果（第 1 页，共 3 页）

#   名称              类型    大小      修改时间
--- ----------------- ------- --------- ----------------
1   report.pdf        文档    1.5 MB    2026-02-25 15:20
2   report-draft.docx 文档    256 KB    2026-02-24 09:15

提示: 使用 --page 2 查看下一页
```

### mv - 移动文件或文件夹

```bash
bdpan mv <源路径> <目标目录>
```

| 参数 | 说明 |
|------|------|
| `源路径` | 要移动的文件或文件夹路径（相对于 `/apps/bdpan/`） |
| `目标目录` | 目标目录路径（相对于 `/apps/bdpan/`） |

**示例：**
```bash
# 移动文件到子目录
bdpan mv report.pdf backup

# 移动文件夹
bdpan mv old-project archive

# JSON 输出
bdpan mv report.pdf backup --json
```

**输出格式：**
```
已移动 report.pdf -> backup
```

### cp - 复制文件或文件夹

```bash
bdpan cp <源路径> <目标目录>
```

| 参数 | 说明 |
|------|------|
| `源路径` | 要复制的文件或文件夹路径（相对于 `/apps/bdpan/`） |
| `目标目录` | 目标目录路径（相对于 `/apps/bdpan/`） |

**示例：**
```bash
# 复制文件到子目录
bdpan cp report.pdf backup

# 复制文件夹
bdpan cp project project-copy

# JSON 输出
bdpan cp report.pdf backup --json
```

**输出格式：**
```
已复制 report.pdf -> backup
```

### rename - 重命名文件或文件夹

```bash
bdpan rename <路径> <新名称>
```

| 参数 | 说明 |
|------|------|
| `路径` | 要重命名的文件或文件夹路径（相对于 `/apps/bdpan/`） |
| `新名称` | 新文件名（仅名称，不含路径） |

**示例：**
```bash
# 重命名文件
bdpan rename old-name.pdf new-name.pdf

# 重命名子目录中的文件
bdpan rename docs/draft.md final.md

# JSON 输出
bdpan rename old-name.pdf new-name.pdf --json
```

**输出格式：**
```
已重命名 old-name.pdf -> new-name.pdf
```

### mkdir - 创建文件夹

```bash
bdpan mkdir <路径>
```

| 参数 | 说明 |
|------|------|
| `路径` | 要创建的文件夹路径（相对于 `/apps/bdpan/`） |

**示例：**
```bash
# 创建文件夹
bdpan mkdir backup

# 创建多级目录
bdpan mkdir backup/2026/03

# JSON 输出
bdpan mkdir backup --json
```

**输出格式：**
```
已创建文件夹: backup
```

---

## 版本管理命令

### update - 自动更新 Skill

> **使用 `bash ${CLAUDE_SKILL_DIR}/scripts/update.sh` 更新 Skill 文件。CLI 更新由 `bdpan` 自身管理。**

```bash
# 检查并更新（交互式，需用户确认）
bash ${CLAUDE_SKILL_DIR}/scripts/update.sh

# 仅检查更新，不执行
bash ${CLAUDE_SKILL_DIR}/scripts/update.sh --check

# 跳过确认，自动更新（自动化场景）
bash ${CLAUDE_SKILL_DIR}/scripts/update.sh --yes
```

**功能说明：**
- 通过百度配置接口获取最新 Skill 版本信息
- 对比本地 VERSION 文件判断是否需要更新
- 下载 zip 包并解压覆盖，更新 VERSION 文件
- 支持 SHA256 完整性校验（如配置中包含 checksum）

**选项：**
| 选项 | 说明 |
|------|------|
| `--check, -c` | 仅检查更新，不执行安装 |
| `--yes, -y` | 跳过用户确认，自动执行更新 |
| `--help` | 显示帮助信息 |

### version - 查看版本信息

```bash
# 查看当前版本
bdpan version

# 检查是否有更新
bdpan version --check
```

---

## init - 查看安装信息（v3.4.0+）

```bash
bdpan init
```

显示安装路径、配置文件路径和 PATH 配置建议。

**输出示例：**
```
bdpan 安装信息
────────────────────────────
安装路径: /home/user/.local/bin/bdpan
配置路径: /home/user/.config/bdpan/config.json

PATH 配置建议:
  export PATH="$HOME/.local/bin:$PATH"
```

---

## 全局选项

| 选项 | 说明 |
|------|------|
| `--config-path <path>` | 指定配置文件完整路径（适用于 AI Agent 集成） |
| `--json` | JSON 格式输出 |
| `--no-check-update` | 禁用版本更新检查 |
| `--help` | 显示帮助 |
| `--version` | 显示版本 |

---

## JSON 输出格式

### ls 命令输出

```json
[
  {
    "fs_id": 524080722157776,
    "path": "我的应用数据/report.pdf",
    "server_filename": "report.pdf",
    "size": 1536000,
    "isdir": false,
    "md5": "a1b2c3d4e5f6...",
    "server_mtime": "2026-02-25T15:20:00+08:00",
    "server_ctime": "2026-02-25T14:00:00+08:00"
  },
  {
    "fs_id": 841873986109404,
    "path": "我的应用数据/documents",
    "server_filename": "documents",
    "size": 0,
    "isdir": true,
    "md5": "",
    "server_mtime": "2026-02-20T10:30:00+08:00",
    "server_ctime": "2026-02-20T09:00:00+08:00"
  }
]
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `fs_id` | number | 文件唯一 ID |
| `path` | string | 文件路径（中文显示名，如 `我的应用数据/...`） |
| `server_filename` | string | 文件名 |
| `size` | number | 文件大小（字节），目录为 0 |
| `isdir` | boolean | 是否为目录（`true`/`false`，注意是小写布尔值） |
| `md5` | string | 文件 MD5 值，目录为空字符串 |
| `server_mtime` | string | 服务端修改时间（ISO 8601 带时区） |
| `server_ctime` | string | 服务端创建时间（ISO 8601 带时区） |

> **注意：** `path` 字段返回中文显示名（`我的应用数据/...`），不是 API 路径（`/apps/bdpan/...`）。展示给用户时可直接使用此路径。

### share 命令输出

```json
{
  "link": "https://pan.baidu.com/s/1xxxxxxx",
  "short_url": "xxxxxxx",
  "share_id": 25747091668,
  "period": 7,
  "pwd": "abcd"
}
```

### upload/download 命令输出

```json
{
  "status": "success",
  "local_path": "./report.pdf",
  "remote_path": "report.pdf"
}
```

### transfer 命令输出

```json
{
  "status": "success",
  "remote_path": "my-folder/shared-file.pdf",
  "share_link": "https://pan.baidu.com/s/1xxxxx",
  "file_count": 1
}
```

### search 命令输出

```json
{
  "total": 15,
  "page": 1,
  "page_size": 5,
  "results": [
    {
      "fs_id": 524080722157776,
      "path": "我的应用数据/bdpan/report.pdf",
      "server_filename": "report.pdf",
      "size": 1536000,
      "isdir": false,
      "category": 4,
      "server_mtime": "2026-02-25T15:20:00+08:00"
    }
  ]
}
```

### mv/cp/rename/mkdir 命令输出

```json
{
  "status": "ok"
}
```

---

## 路径规则

- 所有路径相对于应用根目录 `/apps/bdpan/`
- 支持相对路径: `backup/data.tar.gz`
- 支持绝对路径: `/apps/bdpan/backup/data.tar.gz`
- 路径穿越 `..` 会被自动阻止

> **⛔ 双向路径映射规则：** 调用 bdpan 命令时，"我的应用数据" 必须转换为 `/apps`；向用户展示路径时，`/apps` 必须转换为 "我的应用数据"。详见 [路径规则](../SKILL.md) 章节。

---

## 配置文件位置

```
~/.config/bdpan/config.json
```

**环境变量：**

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `BDPAN_CONFIG_PATH` | 配置文件完整路径（优先级最高） | 无 |
| `BDPAN_CONFIG_DIR` | 配置文件目录 | `~/.config/bdpan` |
| `BDPAN_INSTALL_DIR` | 二进制安装目录 | `~/.local/bin` |

**配置路径优先级（v3.4.0+）：**
1. `--config-path` 命令行参数（最高优先级）
2. `BDPAN_CONFIG_PATH` 环境变量
3. `BDPAN_CONFIG_DIR` 环境变量 + `config.json`
4. `~/.config/bdpan/config.json`（默认路径）

**使用示例：**
```bash
# 使用命令行参数指定配置
bdpan --config-path /custom/path/config.json ls

# 使用环境变量指定配置
export BDPAN_CONFIG_PATH=/custom/path/config.json
bdpan ls
```

### AI Agent 集成

当 AI Agent 无法通过默认路径读取配置时，可以通过以下方式指定：

```python
import subprocess
import os

env = os.environ.copy()
env["BDPAN_CONFIG_PATH"] = "/home/user/.config/bdpan/config.json"

result = subprocess.run(
    ["bdpan", "ls", "--json"],
    env=env,
    capture_output=True,
    text=True
)
```

---

## 常见错误码

| 错误 | 说明 | 解决方案 |
|------|------|---------|
| Token expired | Token 过期 | 重新登录 |
| Path not allowed | 路径不在允许范围 | 使用 /apps/bdpan/ 下的路径 |
| File not found | 文件不存在 | 检查路径是否正确 |
| errno=13045 | 自己的分享链接 | 文件已在网盘中，直接使用 `bdpan ls` 查找 |

---

## 平台支持

| 功能 | macOS | Linux | Windows (WSL) |
|------|-------|-------|---------------|
| 基础功能 | ✅ | ✅ | ✅ |
| WebView 登录 | ✅ | - | -（WSL 无图形界面，使用 OOB 模式） |
