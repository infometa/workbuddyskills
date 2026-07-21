# Workspace 默认排除清单

`--with-workspaces` 打包时，下列模式默认排除。可用 `--no-default-excludes` 关掉、或 `--workspace-exclude-pattern <glob>` 追加。

格式：每条一行，glob 风格（`fnmatch` 语义）。`/` 结尾代表目录、其余按文件或目录名匹配。

<!-- machine:default_excludes
[
  "node_modules/",
  "bower_components/",
  ".pnpm-store/",
  "vendor/",

  ".git/",
  ".svn/",
  ".hg/",

  "dist/",
  "build/",
  "out/",
  "target/",
  ".next/",
  ".nuxt/",
  ".svelte-kit/",
  ".turbo/",
  ".vite/",
  "DerivedData/",

  "__pycache__/",
  ".venv/",
  "venv/",
  ".tox/",
  ".mypy_cache/",
  ".pytest_cache/",
  ".ruff_cache/",
  "*.pyc",
  "*.pyo",

  ".cache/",
  ".parcel-cache/",
  ".gradle/",
  ".idea/caches/",

  "Pods/",
  "xcuserdata/",

  "coverage/",
  ".nyc_output/",
  "htmlcov/",

  "*.sqlite",
  "*.db",
  "*.duckdb",
  "*.sqlite-journal",

  "*.iso",
  "*.dmg",
  "*.vmdk",
  "*.qcow2",
  "*.box",

  ".DS_Store",
  "Thumbs.db",
  "desktop.ini",

  "*.log"
]
-->

## 各类别说明

### 仓库型垃圾
- `node_modules/`、`bower_components/`、`.pnpm-store/`、`vendor/` —— 包管理器产物，目标端 `npm install` 即可重建。一个大型前端项目这块常占 1-5GB

### VCS 大体积
- `.git/` —— 整个 git 目录默认排除。objects 子目录是大头，包不带 git history。**如果用户明确要带历史**，传 `--workspace-exclude-pattern '!.git'` 反选（或者更简单：去 src 端先 `git clone --depth=1` 一份再迁）

### 构建产物
- `dist/`、`build/`、`out/`、`target/`、`.next/`、`.nuxt/`、`.svelte-kit/`、`.turbo/`、`.vite/`、`DerivedData/` —— 编译/打包产出，跨机器再编一次就有

### Python
- `__pycache__/`、`.venv/`、`venv/`、`.tox/`、`*.pyc/.pyo`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`

### 通用缓存
- `.cache/`、`.parcel-cache/`、`.gradle/`、`.idea/caches/`

### iOS / Xcode
- `Pods/`（CocoaPods）、`xcuserdata/`（用户私有 Xcode 设置）

### 覆盖率
- `coverage/`、`.nyc_output/`、`htmlcov/`

### 本地数据库（默认 skip + warn）
- `*.sqlite`、`*.db`、`*.duckdb`、`*.sqlite-journal` —— 用户可能拿它们当业务 DB（几十 GB 常见）。**即便迁过去，目标机版本不匹配也可能起不来**。Warn 而不是静默跳，让用户决定

### 虚拟机镜像
- `*.iso`、`*.dmg`、`*.vmdk`、`*.qcow2`、`*.box`

### 操作系统垃圾
- `.DS_Store`（mac Finder）、`Thumbs.db`（Win 缩略图）、`desktop.ini`（Win 文件夹元数据）

### 日志
- `*.log` —— 不影响项目功能，重启后会自动重建

## 默认**会**带走（个人资产，不排除）

下列文件是用户的个人资产，**默认全部打包**，不进入排除清单。但 dry-run 的 `caveats` 段会显式列出，让 agent 或用户在打包前知情决定是否要手动排除：

- `.env`、`.envrc`、`.envrc.local`（环境变量、可能含 token —— 但这些通常是项目正常运行必需）
- `*.pem`、`*.key`、`id_rsa`、`id_ed25519`（私钥 —— 用户跨机后还要继续用）
- `*.dump`、`*.bak.sql`、`*.sql.gz`（数据库 dump —— 体积可能大但用户可能需要）
- `secrets.*`、`*credentials*`、`config.local.*`

**调用方约定**：agent 收到 dry-run JSON 后，看到 `caveats` 里有 `env_files` / `private_keys` 等条目时，**主动告知用户**"我会带走 N 个 .env 文件、N 个私钥"，用户确认或选择排除某些项后，再决定是否给 `--workspace-exclude-pattern '*.env'` 等参数。

**为什么默认带**：这是用户自己的个人电脑数据，迁移到自己的另一台设备/客户端，类似 Time Machine。如果默认排除，用户会觉得"我的项目搬过去就跑不起来了"。安全责任在传输环节（用户自己选择安全的传输介质），不在打包工具。

## 大小阈值

- `size_warn_per_dir_bytes`: 1 GB —— 单 workspace 排除后超过这个，dry-run 会标 warn
- `size_warn_total_bytes`: 10 GB —— 全部 workspaces 总和超过，dry-run 会标 warn
- `size_limit_per_dir_bytes`: 5 GB —— 单 workspace 超过这个**默认 skip**（除非显式 `--workspace-include <path>`）

## 检测 Docker volume / 大数据目录

无法从文件名识别，**用 size threshold 兜底**：包含 > 1GB 子目录的 workspace，dry-run 会在 caveats 里单独列出，提示用户检查是否是 mounted volume / 数据目录。
