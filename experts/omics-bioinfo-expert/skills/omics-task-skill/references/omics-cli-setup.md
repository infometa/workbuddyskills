# omics-platform-cli 通用安装 · 授权 · 配置流程（Setup Guide）

> **本文档是共享参考规范**，适用于：
> - `omics-task-skill`（通用任务 SKILL）
> - 所有依赖 `omics-platform-cli` 的 SKILL
>
> **SKILL 使用方式（强制）**：进入 Step -1 / Step 0 / Step 1 / Step 2 之前，
> 必须显式读取本文档对应章节，不得凭记忆执行。
>
> **版本**：v1.2（2026-08-27）  
> **关联文档**：[cli_commands.md](cli_commands.md) · [../SKILL.md](../SKILL.md) · [../CONTRACT.md](../CONTRACT.md)

---

## 设计原则（第一性原理）

**核心问题**：用户要用 Omics Skills，但 CLI 是唯一的平台能力出口。如果 CLI 不存在、未登录、或未配置——Skills 什么都干不了。

**因此，所有 Skills 必须在执行任何业务逻辑之前，保证三件事就绪**：
1. CLI 已安装（存在且可执行）
2. 用户已登录（session 有效）
3. 本地配置已就绪（region / project / env / bucket 已写入）

**设计约束**：
- **无感化**：已就绪的条件不应打扰用户；只在缺失时才介入
- **渐进式**：按 Step -1 → 0 → 1 → 2 顺序推进，每步都可独立成功
- **不抢权**：配置引导是帮助用户选择，而非替用户决策
- **跨平台**：macOS / Linux / Windows 三平台一致行为

**交互方式约束（⚠️ 强制执行）**：

> 本 SKILL 运行在 WorkBuddy 对话界面中。所有需要用户做选择的步骤，**必须**使用 `AskUserQuestion` 工具以交互式选项卡的形式呈现，禁止以纯文字列出让用户在消息框手动输入编号或命令。
>
> - Agent 负责在后台执行所有查询命令（`list *`），将结果解析为结构化选项
> - 用户通过点击选项卡完成选择，无需在终端手动输入任何命令
> - 每个选项卡的 `label` 应简明可读（如 `ap-guangzhou（广州）`），`description` 补充说明细节

---

## 总体流程图

```
SKILL 触发
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Step -1：CLI 存在性检查                               │
│   omics version 或 which omics                       │
│   ├── 存在 → 继续                                     │
│   └── 不存在 → 进入安装引导（§A）────────────────┐   │
└─────────────────────────────────────────────────────┘  │
    │                                                    │
    ▼                                                    ▼
┌─────────────────────────────────────────────────────┐  ┌──────────────────────┐
│ Step 0：鉴权 + 配置双重预检                           │  │ 安装引导（§A）        │
│   whoami → exit 0 → config show → 字段完整？         │  │ 自动 / 手动两路       │
│   ├── 全部 OK（B端）→ 直接跑业务                      │  └──────────────────────┘
│   ├── 全部 OK（C端）→ Step 0.3 配额首检               │
│   ├── whoami exit 2 → Step 1（Login）                │
│   └── config 缺字段 → Step 2（Config）               │
└─────────────────────────────────────────────────────┘
    │
    ├──→ Step 1：登录授权（§B）
    │
    └──→ Step 2：配置引导（§C）
              ├── B端正式用户 → §C-B
              └── C端体验用户 → §C-C（静默配置，固定 env-b65ys9kj / trial-user-1323714374）
```

---

## § Step -1：CLI 存在性检查

### -1.1 检测方法

```bash
python3 scripts/omics_cli.py version
```

通过 `find_cli()` 在 PATH 中搜索 `omics` 可执行文件。

**结果处理**：

| 结果 | 含义 | 行动 |
|------|------|------|
| exit 0，打印版本号 | CLI 已安装 | 继续 Step 0 |
| `FileNotFoundError` / `command not found` | CLI 未安装 | 进入安装引导（§A） |
| exit 非 0，其他错误 | 安装损坏或路径异常 | 提示用户重装，给出安装链接 |

### -1.2 PATH 更新注意

新安装的 CLI 默认放到 `~/.local/bin`（macOS/Linux）或 `%LOCALAPPDATA%\Microsoft\WindowsApps`（Windows）。
安装脚本会写入 `.zshrc`/`.bashrc`，但**当前进程的 PATH 不会自动更新**。

SKILL 在安装完成后必须：
1. 检查 `~/.local/bin/omics`（macOS/Linux）或 Windows 安装路径是否存在
2. 若存在，使用完整路径 `~/.local/bin/omics version` 验证，而非依赖 PATH 更新

---

## §A：CLI 安装引导

> **触发条件**：Step -1 检测到 CLI 未安装。

### A.1 双路安装方案

SKILL 检测到 CLI 未安装后，**使用 `AskUserQuestion` 工具**询问用户偏好，再执行对应路径。

```
[AskUserQuestion 调用示例]
question: "检测到本机尚未安装 omics-platform-cli（组学平台官方 CLI 工具），请选择安装方式："
header: "安装方式"
options:
  - label: "自动安装（推荐）"
    description: "由 Skill 自动下载并安装到 ~/.local/bin，全程无需手动操作"
  - label: "手动安装"
    description: "前往官方下载页自行下载安装包，适合网络受限或有特殊安装需求的场景"
```

### A.2 方案一：自动安装

> **设计依据**：
> - CLI 提供 `scripts/install.sh`（macOS/Linux）和 `scripts/install.ps1`（Windows），这是官方安装路径
> - install.sh 默认安装到 `~/.local/bin`，不需要 sudo
> - 安装包托管在 CNB：`https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/raw/main`

#### A.2.1 macOS / Linux 自动安装流程

```
Step A.2.1.1: 检测平台
  OS = uname -s   → Darwin(mac) / Linux
  ARCH = uname -m → arm64 / amd64

Step A.2.1.2: 构建下载 URL（基于 CNB 仓库结构）
  BASE = "https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/raw/main"

  # 获取最新版本号
  latest_url = BASE + "/dist/release/latest.json"
  version = 从 latest.json 中取 .version 字段

  # 构建平台包文件名
  pkg_os = "mac"（macOS）或 "linux"
  pkg_name = "omics-{version}-{pkg_os}.tar.gz"

  download_url = BASE + "/dist/release/{version}/{pkg_name}"
  sha256_url   = BASE + "/dist/release/{version}/metadata.json"（取 assets.{pkg_os}.sha256）

Step A.2.1.3: 下载 + 校验 + 安装
  临时工作目录 = mktemp -d
  1. curl -fLO {download_url}
  2. 从 metadata.json 取 SHA256 → 校验
  3. tar -xzf {pkg_name} -C {tmpdir}
  4. mkdir -p ~/.local/bin
  5. install -m 0755 {tmpdir}/omics ~/.local/bin/omics
  6. [macOS] xattr -d com.apple.quarantine ~/.local/bin/omics 2>/dev/null || true
  7. 验证：~/.local/bin/omics version

Step A.2.1.4: PATH 处理
  检查 ~/.local/bin 是否已在 PATH：
  ├── 已在 → 不需要操作，使用完整路径继续
  └── 不在 → 以完整路径执行（~/.local/bin/omics），并告知用户：
             "安装成功！PATH 已更新至 ~/.zshrc，新建终端窗口后即可直接使用 omics 命令。
              本次 Skill 已使用完整路径完成安装验证。"
```

#### A.2.2 Windows 自动安装流程

```
Step A.2.2.1: 检测平台
  platform = "windows"，arch = amd64（当前仅支持 amd64）

Step A.2.2.2: 构建下载 URL
  BASE = "https://cnb.cool/tencenthealthcareomics/omics-platform-cli/-/raw/main"
  version = 从 latest.json 取 .version
  pkg_name = "omics-{version}-windows.zip"
  download_url = BASE + "/dist/release/{version}/{pkg_name}"

Step A.2.2.3: 下载 + 安装
  install_dir = %LOCALAPPDATA%\Microsoft\WindowsApps（或用户指定路径）
  1. 下载 zip 到临时目录
  2. SHA256 校验
  3. 解压 omics.exe 到 install_dir
  4. 验证：{install_dir}\omics.exe version

  ⚠️ Windows PATH 写入限制：
  SKILL 不自动修改注册表或系统 PATH；
  告知用户将 install_dir 加入 PATH，或使用完整路径继续本次操作。
```

#### A.2.3 自动安装的错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| 网络连接失败（CNB 不可达） | 展示手动安装链接（§A.3），建议用户手动下载 |
| SHA256 校验失败 | 删除临时文件，告知用户重试，或手动下载后告诉 SKILL 安装路径 |
| 安装目录无写权限 | 提示用户手动执行：`bash install.sh --prefix ~/bin` |
| Windows 执行策略限制 | 引导用户运行 `Set-ExecutionPolicy -Scope Process Bypass`，或手动安装 |
| 平台不支持（非 x86_64/arm64） | 告知当前平台暂不支持，引导手动安装 |

### A.3 方案二：手动安装

展示以下信息，等待用户完成后回复「已安装」：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
手动安装 omics-platform-cli
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 前往下载页：
   https://cnb.cool/tencenthealthcareomics/omics-platform-cli

2. 根据您的系统下载对应安装包（页面中 README 有详细指引）：
   macOS (Apple Silicon M1/M2/M3): omics-vX.X-darwin-arm64.tar.gz
   macOS (Intel):                  omics-vX.X-darwin-amd64.tar.gz
   Linux (x86_64):                 omics-vX.X-linux-amd64.tar.gz
   Windows (x86_64):               omics-vX.X-windows-amd64.zip

3. 下载安装脚本并执行：
   macOS / Linux: bash install.sh
   Windows:       .\install.ps1

4. 验证安装：omics version

完成后，请回复「已安装」，我将继续引导您登录和配置。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### A.4 安装完成后验证

无论自动安装还是手动安装，用户告知「已安装」后：

```bash
# 尝试标准 PATH
python3 scripts/omics_cli.py version

# 若失败，尝试常见安装路径
~/.local/bin/omics version      # macOS / Linux 默认
# Windows: %LOCALAPPDATA%\Microsoft\WindowsApps\omics.exe version
```

验证成功后，继续 Step 0。
验证仍失败，提示用户：

```
安装验证失败：无法在常见路径找到 omics 命令。
可能原因：
  1. 安装路径不在 PATH 中 → 请新开一个终端窗口后重试
  2. 安装目录不是默认位置 → 请告诉我 omics 的完整安装路径
     （可通过 `which omics` 或 `where omics` 查询）
```

---

## §B：登录授权

> **触发条件**：Step 0 中 `whoami` 返回 exit 2（未登录或 session 过期）。

### B.1 SKILL 主动调用 login

```bash
python3 scripts/omics_cli.py login
```

行为：
- CLI 在本机启动 `localhost:18000` 监听
- **自动打开浏览器**到 OneID OAuth 授权确认页
- 用户在浏览器点击「确认授权」，CLI 接收 ticket → 兑换 session_id → 持久化到 `~/.omics-platform-cli/auth.json`

提示用户：
```
已为您打开浏览器登录授权页，请在浏览器中点击「确认授权」完成登录。
授权完成后系统将自动继续。
（等待中...最长 120 秒）
```

### B.2 登录后轮询验证

```
最多轮询 3 次，间隔 2s：
  python3 scripts/omics_cli.py whoami

  ├── exit 0 → 登录成功
  │           → 解析 whoami 输出，判断用户类型（B端 / C端）
  │           → 继续 Step 0 配置检查（Step 2）
  │
  └── exit 2 → 仍未登录
              → 3 次后提示：
              "授权似乎未完成，请确认浏览器中已点击「确认授权」。
               如需重新发起授权，请回复「重试」。"
```

### B.3 用户类型识别

`whoami` exit 0 后，解析输出判断用户类型：

| 类型 | 识别条件 | 后续流程 |
|------|---------|---------|
| **C端体验用户** | `Role == "trial_user"` 且 `Capabilities` 含 `"misc:trial"` | Step 2-C（简化配置） |
| **B端正式用户** | 其他情况 | Step 2-B（完整引导配置） |

> **login 的适用场景限制**：
> `omics login` 会打开本地浏览器，仅适用于**用户本机**场景。
> 纯远程无桌面环境（容器/SSH）无法接收 localhost 回调，此命令不适用。
> 遇此情况告知用户在有浏览器的本地机器运行 CLI 并授权。

---

## §C：配置引导

> **触发条件**：Step 0 中 `config show` 缺少必要字段（任一字段为空则 exit 1）。

配置文件路径：`~/.omics-platform-cli/omics_config.json`
必要字段：`Region / ProjectId / ProjectName / EnvironmentId / EnvironmentName / CosBucketName`

### §C-B：B端正式用户完整配置流程

> 每步 Agent 均在**后台执行**查询命令，将结果通过 **`AskUserQuestion` 选项卡**呈现给用户点选，禁止让用户在终端手动输入命令或编号。步骤顺序即执行顺序，不得跳步或提前。

> **异常分支引导语（强制使用）**：当检测到 B 端正式用户缺少项目/环境/COS 桶等必要配置时，**必须**按下列引导语提醒用户前往对应入口创建：
>
> | 缺失项 | 强制引导 URL | 操作入口 |
> |--------|-------------|---------|
> | **无项目** | `https://omics.qq.com/platform/project/list` | 组学平台 → 项目列表 → 创建项目 |
> | **无环境** | `https://console.cloud.tencent.com/omics/env/env-list` | 组学控制台 → 环境管理 → 创建环境 |
> | **选定环境无绑定 COS 桶** | `https://console.cloud.tencent.com/omics/env/env-list` | 组学控制台 → 环境管理 → 环境详情 → 绑定 COS 桶 |

**Step C-B-1：选择地域**

```bash
python3 scripts/omics_cli.py list region -o json
```

解析结果 → `AskUserQuestion`：
- `question`: "请选择要使用的地域"
- `header`: "地域选择"
- `options`: 每条 `label: "{RegionId}（{RegionName}）"`（最多 4 个；超出时优先列常用地域，description 注明"还有更多，可直接输入地域 ID"）

→ 记录 `<selectedRegion>`

---

**Step C-B-2：并行查询项目和环境，先展示项目选择**

```bash
# 并行执行（两条命令同时发出，结果分别缓存）
python3 scripts/omics_cli.py list project -o json
python3 scripts/omics_cli.py list env --region <selectedRegion> -o json
```

解析项目结果，过滤 `Region == selectedRegion` → `AskUserQuestion`：
- `question`: "请选择要使用的项目"
- `header`: "项目选择"
- `options`: 每条 `label: "{ProjectName}"` + `description: "ID: {ProjectId}"`

若无项目（过滤后为空）→ 进入 §C-B-no-project 分支

→ 记录 `<selectedProjectId>`、`<selectedProjectName>`

---

**Step C-B-3：展示环境选择**

复用 Step C-B-2 已缓存的 `list env` 结果，过滤 `Available=true` → `AskUserQuestion`：
- `question`: "请选择要使用的运行环境"
- `header`: "环境选择"
- `options`: 每条 `label: "{EnvironmentName}"` + `description: "ID: {EnvironmentId}"`

若无可用环境（`Available=true` 条目为空）→ 进入 §C-B-no-env 分支

→ 记录 `<selectedEnvId>`、`<selectedEnvName>`

---

**Step C-B-4：临时写入 config（后台，无需用户感知）**

```bash
python3 scripts/omics_cli.py config set \
  -r <selectedRegion> -p <selectedProjectId> \
  -e <selectedEnvId> -b PLACEHOLDER
```

> 此步使 `list cos-bucket` 能读到有效 `EnvironmentId`，必须在查询桶列表前完成。

---

**Step C-B-5：选择 COS 存储桶**

```bash
python3 scripts/omics_cli.py list cos-bucket -o json
```

解析结果，过滤 `Associated=true` → `AskUserQuestion`：
- `question`: "请选择要绑定的 COS 存储桶"
- `header`: "存储桶选择"
- `options`: 每条 `label: "{CosBucketName}"` + `description: "已授权关联"`

若无可用桶 → 进入 §C-B-no-bucket 分支

→ 记录 `<selectedBucket>`

---

**Step C-B-6：正式写入配置（后台，无需用户感知）**

```bash
python3 scripts/omics_cli.py config set \
  -r <selectedRegion> \
  -p <selectedProjectId> \
  -e <selectedEnvId> \
  -b <selectedBucket>
```

输出确认摘要：
```
配置已完成：
   地域：{selectedRegion}
   项目：{selectedProjectName}（{selectedProjectId}）
   环境：{selectedEnvName}（{selectedEnvId}）
   COS 桶：{selectedBucket}
```

#### §C-B-no-project：无可用项目

```
检测到您已登录，但账号下无可用项目（或指定地域下无项目）。

组学 Skill 需要在项目中运行任务。
请先前往组学平台创建项目：

https://omics.qq.com/platform/project/list

操作路径：组学平台 → 项目列表 → 创建项目

完成后请回复「已就绪」，我将重新检测并引导您完成配置。
```

#### §C-B-no-env：无可用环境

```
检测到您已登录但账号下无可用环境。

组学 Skill 需要一个容器运行环境来执行任务。
请先前往控制台创建环境：

https://console.cloud.tencent.com/omics/env/env-list

操作路径：组学控制台 → 环境管理 → 创建环境
（创建包括：容器环境配置 + 绑定 COS 存储桶）

完成后请回复「已就绪」，我将重新检测并引导您完成配置。
```

#### §C-B-no-bucket：环境存在但无绑定存储桶

```
检测到您选定的环境（{selectedEnvName}）未绑定 COS 存储桶。

COS 存储桶用于存储任务的输入/输出数据，是运行任务的必要条件。

请前往组学控制台为当前环境绑定对应的 COS 存储桶：

https://console.cloud.tencent.com/omics/env/env-list

操作路径：组学控制台 → 环境管理 → 找到 {selectedEnvName} → 环境详情 → 存储桶 → 关联存储桶到环境
（如尚未创建 COS 存储桶，请先创建后再绑定。）

完成后回复「已绑定」，我将重新拉取桶列表继续配置。
```

### §C-C：C端体验用户简化配置流程

> **说明**：C 端用户使用共享资源池，**全程无需用户选择配置**，由 SKILL 静默完成。
> 共享资源的环境 ID 和 COS 桶由平台统一管理，固定值如下：
> - 地域：`ap-guangzhou`
> - 环境 ID：`env-b65ys9kj`（C端共享计算资源池）
> - COS 桶：`trial-user-1323714374`（C端体验共享桶）

```
① 地域：固定 ap-guangzhou（无需用户选择）

② 查询项目列表（后台执行，无需用户感知）
   python3 scripts/omics_cli.py list project -o json
   → 解析结果：
     [若列表非空] → 自动取第一条 ProjectId
                    记录 <selectedProjectId>、<selectedProjectName>
     [若列表为空] → 立即停止，输出以下提示，不得继续配置流程：

       检测到您的账号下暂无可用项目，无法完成配置。

       这可能是账号初始化尚未完成，请联系我们获取帮助：
       omics@tencent.com

③ 写入配置（后台静默执行）
   python3 scripts/omics_cli.py config set \
     -r ap-guangzhou \
     -p <selectedProjectId> \
     -e env-b65ys9kj \
     -b trial-user-1323714374

④ 验证配置写入（后台执行，不向用户展示过程）
   python3 scripts/omics_cli.py config show -o json
   → 检查 Region / ProjectId / EnvironmentId / CosBucketName 四字段均非空

   [若四字段均非空] → 配置验证通过，向用户输出：
     配置已就绪，您可以开始使用了！
        地域：ap-guangzhou（广州）
        项目：{selectedProjectName}
        运行环境：共享计算资源池（env-b65ys9kj）
        存储桶：trial-user-1323714374

   [若任一字段为空] → 立即停止，输出以下提示，不得进入业务流程：
     配置验证失败，无法继续使用。

     请联系我们获取帮助：
     omics@tencent.com
```

> **说明**：
> - `env-b65ys9kj` 和 `trial-user-1323714374` 为 C端体验用户固定共享资源，由平台统一管理，无需用户配置。
> - 步骤②空列表和步骤④验证失败均属于平台侧问题，SKILL 不提供用户侧重试方案，直接联系运营处理。
> - 配置完成后，立即执行 §D-Step 0.3 配额首检。

---

## §D：快速检查（Step 0 完整流程）

> **每次 SKILL 触发时均需执行 Step 0，以确保就绪**。

```bash
# D.1 鉴权预检
python3 scripts/omics_cli.py whoami
# exit 0 → 解析用户类型，继续 D.2
# exit 2 → 进入 §B（Login）

# D.2 配置完整性检查
python3 scripts/omics_cli.py config show -o json
# exit 0 + 所有字段非空 → 全部就绪，复述配置摘要后：
#   B端用户 → 直接进入业务逻辑
#   C端用户 → 继续执行 D.3 配额首检（§D-Step 0.3）
# exit 1 或字段有空值 → 进入 §C（Config），按用户类型分流
```

**配置就绪时向用户复述**：
```
当前配置：
   地域：{Region}
   项目：{ProjectName}（{ProjectId}）
   环境：{EnvironmentName}（{EnvironmentId}）
   COS 桶：{CosBucketName}
```

---

## §D-Step 0.3：C端体验用户配额首检（登录/配置就绪后必执行）

> **触发条件**：Step 0.2 配置验证通过（D.2 检查通过）且用户类型为 C端体验用户。
> **执行时机**：每次 SKILL 启动，登录+配置就绪后必须执行一次（"首检"）。不得跳过，不受用户指令影响。
> **与运行前检查的关系**：此为"首检"，仅在登录完成后执行一次。每次实际提交 `omics run` 前，还会再次强制执行配额检查。两层检查共同保障 C端用户配额不被超用。

```bash
python3 scripts/omics_cli.py quota -o json
```

解析返回字段 `remain_days`（剩余体验天数）和 `run_remain_limit`（今日剩余次数），按以下优先级判断：

### 场景一：已到期（`remain_days == 0`）→ **阻断，停止流程**

```
温馨提示：您的免费体验已到期，将无法继续运行任务，历史结果仍可查看。
您可开通组学平台正式版，体验更多功能。

立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
了解平台 → https://cloud.tencent.com/product/omics
```

> ⚠️ **阻断要求**：展示以上话术后立即终止本次 SKILL 流程，不得继续进入业务逻辑。

---

### 场景二：今日次数已用完（`run_remain_limit == 0` 且 `remain_days > 0`）→ **阻断，停止流程**

```
温馨提示：今日免费体验运行已用完，明日 00:00 重置。
您可开通组学平台正式版，享受无限制运行。

立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb
```

> ⚠️ **阻断要求**：展示以上话术后立即终止本次 SKILL 流程，不得继续进入业务逻辑。

---

### 场景三：临近到期（`remain_days <= 3` 且 `remain_days > 0` 且 `run_remain_limit > 0`）→ **提示，继续流程**

```
温馨提示：您的免费体验即将到期（剩余 {remain_days} 天）。
到期后将无法继续运行任务，历史结果仍可查看。
您可开通组学平台正式版，体验更多功能。

立即开通 → https://cloud.tencent.com/apply/p/phrs1vb0chb

今日剩余运行次数：{run_remain_limit} 次
```

> 展示以上话术后继续进入业务逻辑，不阻断。

---

### 场景四：正常体验（`remain_days > 3` 且 `run_remain_limit > 0`）→ **简短提示，继续流程**

```
免费体验版配额：今日剩余 {run_remain_limit} 次 · 剩余 {remain_days} 天
```

> 一行简短展示后直接进入业务逻辑，不阻断。

---

## 退出码处理规范

| 退出码 | 含义 | 处理 |
|--------|------|------|
| 0 | 成功 | 解析 stdout，继续流程 |
| 1 | 业务错误 | 转述 stderr；配置缺失时引导走 §C |
| 2 | 鉴权失败 | 进入 §B（Login），不循环重试 |
| `FileNotFoundError` | CLI 未安装 | 进入 §A（安装引导） |

---

## 引用方式（SKILL.md 中的标准写法）

```markdown
## Step -1：CLI 存在性检查
> **强制读取**：[references/omics-cli-setup.md §Step -1](references/omics-cli-setup.md)

## Step 0：鉴权与配置预检
> **强制读取**：[references/omics-cli-setup.md §D](references/omics-cli-setup.md)

## Step 1：登录授权
> **强制读取**：[references/omics-cli-setup.md §B](references/omics-cli-setup.md)

## Step 2：配置引导
> **强制读取**：[references/omics-cli-setup.md §C](references/omics-cli-setup.md)
> （B端用户 → §C-B；C端用户 → §C-C）
```

---

> 文档版本：v1.2（2026-08-27）
> 维护者：omics-task-skill
> 关联：[cli_commands.md](cli_commands.md) · [../SKILL.md](../SKILL.md) · [../CONTRACT.md](../CONTRACT.md)
