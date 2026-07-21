---
name: repo-source
description: 帮助配置和管理系统软件源，包括 yum/dnf 仓库源、pip 源、npm 源等。 支持查看当前源配置、切换国内镜像源（腾讯云、阿里云等）、排查源相关问题。 覆盖 TencentOS Server 2/3/4 各版本差异。
description_zh: 软件源配置与管理
description_en: Software repository source configuration and management
version: 1.0.0
---

# 软件源配置管理

帮助查看、配置和管理系统软件源（yum/dnf 仓库、pip 源、npm 源），支持切换镜像、排查源相关问题。

## 安全原则

> ⚠️ **重要**：AI 可自动执行只读的诊断和查看命令。
>
> 涉及修改源配置的操作（如编辑 .repo 文件、替换镜像地址、配置全局 pip/npm 源等），仅作为参考提供给用户，由用户自行判断和手动执行。
> 修改前建议备份原配置文件。

## 适用场景

### 用户可能的问题表述

**查看源配置**：
- "查看 yum 源"、"看下当前配置了哪些仓库"
- "yum repolist"、"dnf repolist"
- "repo 有哪些"、"仓库列表"

**配置/换源**：
- "怎么配置 yum 源"、"换成腾讯云的源"
- "配置国内镜像"、"yum 源换成阿里的"
- "怎么加 epel 源"、"添加一个自定义仓库"
- "pip 怎么换源"、"npm 换成腾讯的源"

**源问题排查**：
- "yum 报错了"、"仓库不可用"
- "Cannot find a valid baseurl"、"repodata 404"
- "GPG check FAILED"、"Couldn't resolve host"
- "yum makecache 很慢"

**本地/离线源**：
- "搭建本地 yum 源"、"离线安装怎么弄"
- "createrepo 怎么用"

## 诊断步骤（AI 可自动执行）

以下命令为只读查看命令，可由 AI 自动执行。

### 步骤 1：识别系统版本和包管理器

```bash
# 查看系统版本
cat /etc/os-release

# 确认包管理器
# TencentOS 2：yum
# TencentOS 3/4：dnf（yum 为 dnf 的别名）
which dnf 2>/dev/null && echo "使用 dnf" || echo "使用 yum"
```

### 步骤 2：查看当前 yum/dnf 仓库配置

```bash
# 列出所有已启用的仓库
yum repolist          # 或 dnf repolist
yum repolist all      # 列出所有仓库（包括禁用的）

# 查看仓库详细信息
yum repoinfo          # 或 dnf repoinfo

# 查看 repo 配置文件
ls -la /etc/yum.repos.d/
cat /etc/yum.repos.d/*.repo

# 查看 yum/dnf 主配置
cat /etc/yum.conf      # TencentOS 2
cat /etc/dnf/dnf.conf  # TencentOS 3/4
```

### 步骤 3：检查源连通性

```bash
# 测试源是否可达
yum makecache fast 2>&1 | tail -20    # TencentOS 2
dnf makecache 2>&1 | tail -20         # TencentOS 3/4

# 测试镜像连通性
curl -I https://mirrors.tencent.com/   2>/dev/null | head -5
curl -I https://mirrors.cloud.tencent.com/ 2>/dev/null | head -5
```

### 步骤 4：查看 pip 源配置

```bash
# 查看 pip 版本
pip3 --version 2>/dev/null

# 查看当前 pip 配置
pip3 config list 2>/dev/null

# 查看 pip 配置文件
cat ~/.pip/pip.conf 2>/dev/null
cat /etc/pip.conf 2>/dev/null
cat ~/.config/pip/pip.conf 2>/dev/null
```

### 步骤 5：查看 npm 源配置

```bash
# 查看 npm/node 版本
npm --version 2>/dev/null
node --version 2>/dev/null

# 查看当前 registry
npm config get registry 2>/dev/null

# 查看完整 npm 配置
npm config list 2>/dev/null

# 查看 .npmrc 文件
cat ~/.npmrc 2>/dev/null
cat /etc/npmrc 2>/dev/null
```

### 步骤 6：源错误排查

```bash
# 清理缓存后重试
yum clean all && yum makecache      # TencentOS 2
dnf clean all && dnf makecache      # TencentOS 3/4

# 检查 repodata 是否可访问（替换为实际 baseurl）
# curl -sL <baseurl>/repodata/repomd.xml | head -5

# 检查 GPG key
rpm -qa gpg-pubkey*

# 检查 DNS 解析
nslookup mirrors.tencent.com 2>/dev/null
```

---

## 操作参考（仅供用户手动执行）

> 🛑 **以下命令涉及修改配置，AI 不会自动执行！**
>
> 请用户根据实际情况自行判断和手动执行。建议修改前先备份配置。

---

### 一、yum/dnf 源配置

#### 1. TencentOS 官方源（TencentOS 3）

TencentOS Server 3 默认使用腾讯云官方源：

```bash
# /etc/yum.repos.d/tlinux-official.repo（默认自带，通常不需要手动配置）
[tlinux-official-base]
name=TencentOS Server 3 - Base
baseurl=https://mirrors.tencent.com/tlinux/3.1/tlinux/x86_64/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-tlinux3

[tlinux-official-updates]
name=TencentOS Server 3 - Updates
baseurl=https://mirrors.tencent.com/tlinux/3.1/tlinux-updates/x86_64/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-tlinux3
```

#### 2. 腾讯云镜像源（通用 CentOS 兼容）

适用于需要额外软件包的场景：

```bash
# 备份原配置
cp -r /etc/yum.repos.d/ /etc/yum.repos.d.backup_$(date +%F)

# 创建腾讯云 CentOS 镜像源配置（以 CentOS 8 Stream 兼容为例）
cat > /etc/yum.repos.d/tencent-mirror.repo << 'EOF'
[tencent-os]
name=Tencent Mirror - OS
baseurl=https://mirrors.tencent.com/centos/$releasever/BaseOS/$basearch/os/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[tencent-appstream]
name=Tencent Mirror - AppStream
baseurl=https://mirrors.tencent.com/centos/$releasever/AppStream/$basearch/os/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial

[tencent-extras]
name=Tencent Mirror - Extras
baseurl=https://mirrors.tencent.com/centos/$releasever/extras/$basearch/os/
enabled=1
gpgcheck=0
EOF
```

#### 3. 添加 EPEL 源

```bash
# TencentOS 3 / 4 安装 EPEL
dnf install -y epel-release

# 安装后可选替换为腾讯云 EPEL 镜像
sed -i 's|^metalink=|#metalink=|g' /etc/yum.repos.d/epel*.repo
sed -i 's|^#baseurl=https://download.example/pub/epel/|baseurl=https://mirrors.tencent.com/epel/|g' /etc/yum.repos.d/epel*.repo

# 或直接手动创建
cat > /etc/yum.repos.d/epel-tencent.repo << 'EOF'
[epel]
name=EPEL - Tencent Mirror
baseurl=https://mirrors.tencent.com/epel/$releasever/Everything/$basearch/
enabled=1
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-$releasever
EOF
```

#### 4. 添加自定义 yum 仓库

```bash
# 方法 1：手动创建 .repo 文件
cat > /etc/yum.repos.d/custom.repo << 'EOF'
[custom-repo]
name=My Custom Repository
baseurl=https://repo.example.com/centos/$releasever/$basearch/
# 或使用本地路径：baseurl=file:///opt/localrepo/
enabled=1
gpgcheck=0
# 如有 GPG key：
# gpgcheck=1
# gpgkey=https://repo.example.com/RPM-GPG-KEY-custom
priority=10
EOF

# 方法 2：使用 yum-config-manager
yum-config-manager --add-repo https://repo.example.com/centos/custom.repo
# TencentOS 3/4：
dnf config-manager --add-repo https://repo.example.com/centos/custom.repo
```

#### 5. 仓库管理操作

```bash
# 启用/禁用仓库
yum-config-manager --enable custom-repo
yum-config-manager --disable custom-repo
# TencentOS 3/4：
dnf config-manager --set-enabled custom-repo
dnf config-manager --set-disabled custom-repo

# 临时使用指定仓库安装
yum install --enablerepo=custom-repo package-name
dnf install --enablerepo=custom-repo package-name

# 刷新缓存
yum clean all && yum makecache
dnf clean all && dnf makecache
```

#### 6. .repo 文件字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `[repo-id]` | 仓库唯一标识 | `[tencent-base]` |
| `name` | 仓库描述名称 | `Tencent Mirror - Base` |
| `baseurl` | 仓库地址（HTTP/FTP/本地） | `https://mirrors.tencent.com/...` |
| `mirrorlist` | 镜像列表 URL（与 baseurl 二选一） | `https://mirrorlist.example.com/...` |
| `metalink` | 元数据链接（与 baseurl 二选一） | `https://mirrors.example.com/metalink` |
| `enabled` | 是否启用（1=启用，0=禁用） | `1` |
| `gpgcheck` | 是否验证 GPG 签名 | `1` |
| `gpgkey` | GPG 公钥路径 | `file:///etc/pki/rpm-gpg/RPM-GPG-KEY-...` |
| `priority` | 优先级（数字越小越优先，需 yum-plugin-priorities） | `10` |
| `sslverify` | 是否验证 SSL 证书 | `1` |
| `exclude` | 排除的包 | `kernel* php*` |
| `includepkgs` | 仅包含的包（白名单） | `nginx* python3*` |
| `skip_if_unavailable` | 不可用时跳过而非报错 | `1` |

---

### 二、pip 源配置

#### 1. 腾讯云 pip 镜像源

```bash
# 临时使用（单次安装）
pip3 install -i https://mirrors.tencent.com/pypi/simple/ package-name

# 设置为全局默认源（推荐）
pip3 config set global.index-url https://mirrors.tencent.com/pypi/simple/
pip3 config set global.trusted-host mirrors.tencent.com

# 或手动编辑配置文件
mkdir -p ~/.pip
cat > ~/.pip/pip.conf << 'EOF'
[global]
index-url = https://mirrors.tencent.com/pypi/simple/
trusted-host = mirrors.tencent.com

[install]
trusted-host = mirrors.tencent.com
EOF
```

#### 2. 其他常用 pip 镜像源

```bash
# 阿里云
pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 清华大学
pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/

# 华为云
pip3 config set global.index-url https://repo.huaweicloud.com/repository/pypi/simple/
```

#### 3. pip 全局配置（系统级，影响所有用户）

```bash
# 系统级配置文件
cat > /etc/pip.conf << 'EOF'
[global]
index-url = https://mirrors.tencent.com/pypi/simple/
trusted-host = mirrors.tencent.com
timeout = 120

[install]
trusted-host = mirrors.tencent.com
EOF
```

#### 4. pip 配置文件优先级

| 级别 | 路径 | 说明 |
|------|------|------|
| 系统级 | `/etc/pip.conf` | 影响所有用户 |
| 用户级 | `~/.pip/pip.conf` 或 `~/.config/pip/pip.conf` | 仅当前用户 |
| 虚拟环境级 | `$VIRTUAL_ENV/pip.conf` | 仅当前虚拟环境 |
| 命令行 | `-i https://...` | 仅当次命令 |

优先级从低到高：系统级 < 用户级 < 虚拟环境级 < 命令行参数。

---

### 三、npm 源配置

#### 1. 腾讯云 npm 镜像源

```bash
# 查看当前源
npm config get registry

# 设置为腾讯云镜像（推荐）
npm config set registry https://mirrors.tencent.com/npm/

# 验证配置
npm config get registry
npm info express version    # 测试是否可用
```

#### 2. 其他常用 npm 镜像源

```bash
# 淘宝镜像（npmmirror）
npm config set registry https://registry.npmmirror.com/

# 恢复官方源
npm config set registry https://registry.npmjs.org/

# 华为云
npm config set registry https://repo.huaweicloud.com/repository/npm/
```

#### 3. 使用 .npmrc 文件配置

```bash
# 用户级配置 ~/.npmrc
cat > ~/.npmrc << 'EOF'
registry=https://mirrors.tencent.com/npm/
# 如有私有源需要额外配置 scope
# @mycompany:registry=https://npm.mycompany.com/
EOF

# 项目级配置（项目根目录 .npmrc）
# 仅影响当前项目，适合团队统一配置
echo "registry=https://mirrors.tencent.com/npm/" > .npmrc
```

#### 4. 使用 nrm 管理多个源（可选）

```bash
# 安装 nrm（npm registry manager）
npm install -g nrm

# 列出可用源
nrm ls

# 切换源
nrm use tencent    # 腾讯云
nrm use taobao     # 淘宝
nrm use npm        # 官方

# 添加自定义源
nrm add myregistry https://npm.mycompany.com/

# 测试各源速度
nrm test
```

#### 5. npm 配置文件优先级

| 级别 | 路径 | 说明 |
|------|------|------|
| 项目级 | `项目目录/.npmrc` | 仅当前项目 |
| 用户级 | `~/.npmrc` | 仅当前用户 |
| 全局级 | `$PREFIX/etc/npmrc` | 影响所有用户 |
| 内置 | npm 内置 | 默认 registry.npmjs.org |

优先级从高到低：项目级 > 用户级 > 全局级 > 内置。

---

### 四、搭建本地 yum 源（离线/内网场景）

#### 1. 基于本地目录

```bash
# 安装 createrepo 工具
yum install -y createrepo    # TencentOS 2
dnf install -y createrepo_c  # TencentOS 3/4

# 准备 RPM 包目录
mkdir -p /opt/localrepo
# 将 RPM 包复制到该目录
cp /path/to/*.rpm /opt/localrepo/

# 生成仓库元数据
createrepo /opt/localrepo/

# 配置本地源
cat > /etc/yum.repos.d/local.repo << 'EOF'
[local-repo]
name=Local Repository
baseurl=file:///opt/localrepo/
enabled=1
gpgcheck=0
EOF

# 更新缓存
yum clean all && yum makecache
```

#### 2. 基于 HTTP 服务（局域网共享）

```bash
# 安装 HTTP 服务
yum install -y httpd    # 或 nginx

# 创建仓库目录
mkdir -p /var/www/html/repo
cp /path/to/*.rpm /var/www/html/repo/
createrepo /var/www/html/repo/

# 启动 HTTP 服务
systemctl enable --now httpd

# 客户端配置
cat > /etc/yum.repos.d/lan-repo.repo << 'EOF'
[lan-repo]
name=LAN Repository
baseurl=http://192.168.1.100/repo/
enabled=1
gpgcheck=0
EOF
```

#### 3. 同步官方源到本地（完整镜像）

```bash
# 安装 reposync 工具
yum install -y yum-utils    # TencentOS 2
dnf install -y dnf-utils    # TencentOS 3/4

# 同步指定仓库
reposync --repoid=tlinux-official-base -p /opt/mirror/
# TencentOS 3/4：
dnf reposync --repoid=tlinux-official-base -p /opt/mirror/

# 更新仓库元数据
createrepo --update /opt/mirror/tlinux-official-base/
```

---

### 五、常见问题排查

**Q1：yum/dnf 报错 "Cannot find a valid baseurl for repo"**

```bash
# 检查网络连通性
ping -c 3 mirrors.tencent.com

# 检查 DNS 解析
nslookup mirrors.tencent.com

# 检查 baseurl 是否可访问
curl -sL <baseurl>/repodata/repomd.xml | head -5

# 如果是网络问题，临时使用 IP
# 在 /etc/hosts 中添加解析
```

**Q2：GPG check FAILED**

```bash
# 方案 1：导入 GPG key
rpm --import https://mirrors.tencent.com/path/to/RPM-GPG-KEY

# 方案 2：临时跳过 GPG 检查（不推荐用于生产环境）
yum install --nogpgcheck package-name

# 方案 3：在 repo 配置中禁用 GPG 检查
# 编辑 .repo 文件，设置 gpgcheck=0
```

**Q3：yum makecache 很慢**

```bash
# 清理旧缓存
yum clean all

# 检查是否有不可用的源拖慢速度
yum repolist -v 2>&1 | grep -E "(Repo-id|Repo-status|Repo-baseurl)"

# 禁用不需要的源
yum-config-manager --disable slow-repo-id

# 配置超时时间（在 /etc/yum.conf 或 /etc/dnf/dnf.conf 中）
# timeout=30
# fastestmirror=1    # 自动选择最快镜像（TencentOS 2）
# max_parallel_downloads=10  # 并行下载数（TencentOS 3/4 dnf）
```

**Q4：pip install 超时或连接失败**

```bash
# 临时使用镜像源
pip3 install -i https://mirrors.tencent.com/pypi/simple/ --trusted-host mirrors.tencent.com package-name

# 增加超时时间
pip3 install --timeout=120 package-name

# 使用代理
pip3 install --proxy http://proxy:8080 package-name
```

**Q5：npm install 卡住或报错**

```bash
# 清理缓存
npm cache clean --force

# 检查代理配置（可能有残留代理）
npm config get proxy
npm config get https-proxy
npm config delete proxy
npm config delete https-proxy

# 换源重试
npm config set registry https://mirrors.tencent.com/npm/
npm install
```

---

### 六、dnf.conf / yum.conf 常用配置

```bash
# TencentOS 3/4：/etc/dnf/dnf.conf
# TencentOS 2：/etc/yum.conf

[main]
gpgcheck=1                      # 全局 GPG 检查
installonly_limit=3             # 保留的内核版本数
clean_requirements_on_remove=True
best=True                       # 安装最佳可用版本
skip_if_unavailable=False       # 仓库不可用时是否跳过
# max_parallel_downloads=10     # 并行下载数（dnf 专有）
# fastestmirror=1               # 最快镜像选择（dnf 专有）
# timeout=30                    # 超时秒数
# proxy=http://proxy:8080       # 全局代理
# exclude=kernel*               # 全局排除包
```

---

### 七、腾讯云镜像源地址汇总

| 类型 | 镜像地址 | 说明 |
|------|----------|------|
| **yum/dnf (TencentOS)** | `https://mirrors.tencent.com/tlinux/` | TencentOS 官方仓库 |
| **yum/dnf (CentOS)** | `https://mirrors.tencent.com/centos/` | CentOS 兼容包 |
| **EPEL** | `https://mirrors.tencent.com/epel/` | 额外扩展包 |
| **pip (PyPI)** | `https://mirrors.tencent.com/pypi/simple/` | Python 包 |
| **npm** | `https://mirrors.tencent.com/npm/` | Node.js 包 |
| **Docker Hub** | `https://mirror.ccs.tencentyun.com` | Docker 镜像（腾讯云内网） |
| **腾讯云镜像站首页** | `https://mirrors.tencent.com/` | 所有镜像列表 |

> 💡 腾讯云内网服务器访问 `mirrors.tencentyun.com` 速度更快（走内网不计流量）。

---

### 八、TencentOS 版本差异

| 操作 | TencentOS 2 | TencentOS 3 / 4 |
|------|-------------|------------------|
| 包管理器 | `yum` | `dnf`（`yum` 为别名） |
| 主配置文件 | `/etc/yum.conf` | `/etc/dnf/dnf.conf` |
| 并行下载 | 不支持 | `max_parallel_downloads=10` |
| 最快镜像 | `yum-plugin-fastestmirror` | `fastestmirror=1`（内置） |
| 模块化仓库 | 不支持 | 支持（`dnf module`） |
| 仓库管理 | `yum-config-manager` | `dnf config-manager` |
| 同步仓库 | `reposync` | `dnf reposync` |

## 相关技能

- **package-version**：软件包版本查询、升级、回退管理
