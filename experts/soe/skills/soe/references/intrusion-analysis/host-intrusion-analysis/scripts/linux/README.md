# get_log_all_in_one.sh

Linux 安全应急响应日志采集工具 —— 一键采集服务器安全状态，输出单个标准化文本文件，供 AI 自动化分析。

## 适用场景

当一台 Linux 服务器疑似被入侵（勒索病毒、挖矿、后门植入等），你需要快速了解这台机器上发生了什么。运行本脚本，几秒钟内获得一份完整的安全状态快照，然后交给 AI 分析。

## 快速开始

```bash
# 最简单的用法：以 root 权限运行
sudo bash get_log_all_in_one.sh

# 指定输出目录
sudo bash get_log_all_in_one.sh --output-dir /tmp/incident

# 只采集最近 3 天的日志
sudo bash get_log_all_in_one.sh --days-back 3

# 只执行网络信息采集（步骤 4）
sudo bash get_log_all_in_one.sh --step 4
```

运行完成后，在当前目录（或 `--output-dir` 指定的目录）生成一个 `.txt` 文件：

```
log_<IP>_<主机名>_<用户>_<时间戳>.txt
```

## 采集内容

脚本分 9 个步骤，全面覆盖安全应急响应所需的关键信息：

| 步骤 | 名称 | 采集内容 |
|------|------|---------|
| 1 | **SystemInfo** | 用户身份、操作系统版本、硬件配置、安全配置检查（SELinux/防火墙/SSH）、可登录用户、sudo 权限、关键命令完整性（MD5 hash） |
| 2 | **AuthLogs** | SSH 登录成功/失败记录、密钥认证、sudo 命令执行、用户创建/修改记录 |
| 3 | **Processes** | CPU/内存 Top 15 进程、PID 1 子进程、反弹 Shell 模式检测 |
| 4 | **Network** | 监听端口、已建立连接、路由表、ARP 表、DNS 配置、防火墙规则、IP 转发状态 |
| 5 | **Persistence** | 定时任务（crontab/cron.d）、init.d 脚本、systemd 自定义服务、Shell profile 文件、rc.local |
| 6 | **SSH** | sshd 二进制校验、配置文件审查、authorized_keys、PAM 配置检查 |
| 7 | **ShellHistory** | 所有用户的 bash/zsh 命令历史 |
| 8 | **Environment** | 环境变量（LD_PRELOAD/LD_LIBRARY_PATH 等可疑项高亮）、已加载内核模块（无签名模块检查）、系统时区与 NTP 同步状态 |
| 9 | **FileIntegrity** | 包文件校验（rpm -Va / debsums）、关键二进制单独校验（sshd/sudo/su 等）、SUID/SGID 文件列表 |

## 命令行参数

```
用法: sudo bash get_log_all_in_one.sh [选项]

选项:
  --days-back N        采集最近 N 天的日志（默认: 7）
  --max-lines N        每个子段最大输出行数（默认: 2000）
  --max-file-size N    输出文件最大大小，单位 MB（默认: 50）
  --cmd-timeout N      单个命令超时时间，单位秒（默认: 30）
  --output-dir DIR     输出文件存放目录（默认: 脚本所在目录）
  --step N             只执行指定步骤（1-9），默认执行全部
  --version            显示版本信息
  --help               显示帮助信息
```

## 设计原则

| 原则 | 说明 |
|------|------|
| **纯采集，零检测** | 只负责收集数据，不做恶意判定（交给后续 AI 分析） |
| **零安装** | 不安装任何软件包，只用系统自带命令 |
| **单文件输出** | 所有结果写入一个 `.txt` 文件，无临时文件 |
| **容错不中断** | 命令不存在、权限不足、超时 —— 记录后继续，不影响后续步骤 |
| **输出大小可控** | 全局文件大小上限（默认 50MB），防止后续分析时 token 爆炸 |

## 兼容性

- **Debian 系**: Ubuntu, Debian, Kali
- **RHEL 系**: CentOS, RHEL, Rocky, Alma, Fedora, Oracle Linux
- **依赖**: bash + coreutils（零额外安装）
- **权限**: 需要 root（安全日志读取必须）

脚本自动检测发行版，适配日志路径（`/var/log/auth.log` vs `/var/log/secure`）、crontab 位置、防火墙工具等差异。

## 输出格式

输出文件采用三级层次的纯文本格式，方便程序解析：

```
REPORT_BEGIN
META: _CollectionMeta
Hostname: webserver01
IP: 192.168.1.100
...

======== SECTION: SystemInfo ========        ← 一级：大段

  -------- SUB: whoami --------              ← 二级：子段
-- cmd: whoami --                            ← 三级：命令输出边界
root
-- cmd: id --
uid=0(root) gid=0(root) groups=0(root)

  -------- CATEGORY: SSH --------            ← 二级：分类
    -------- EVENTS: ssh_login_success ----  ← 三级：事件类型
...日志行...

META: _ExecutionTiming
Step 1 (SystemInfo): 0.2s
...
Total: 2.5s
REPORT_END
```

### 分隔符说明

| 格式 | 含义 |
|------|------|
| `======== SECTION: xxx ========` | 一级章节（9 个采集步骤） |
| `-------- SUB: xxx --------` | 二级子段 |
| `-------- CATEGORY: xxx --------` | 二级分类（用于分组） |
| `-------- EVENTS: xxx --------` | 三级事件类型 |
| `-- cmd: xxx --` | 命令输出的边界标签 |
| `-- file: /path --` | 文件内容的边界标签 |

## 安全注意事项

- 脚本**仅在本地写文件**，不上传数据、不发网络请求
- 输出文件包含敏感信息（命令历史可能含密码/Token、authorized_keys 等），**请妥善保管**
- `env_integrity` 子段记录关键命令（`ps`, `ss`, `bash`, `sshd` 等）的路径和 MD5 hash，可用于检测命令是否被替换
- META 段记录 `$PATH` 环境变量，可检测 PATH 是否被篡改

## 已知限制

| 限制 | 影响 |
|------|------|
| auth.log 时间格式无年份 | 跨年日志可能误匹配（7 天窗口内几乎不会遇到） |
| 文件日志时间过滤为"尽力模式" | 可能多采集少量超出时间窗口的日志行 |
| 仅支持 gz 压缩日志 | 不处理 xz/bz2 格式（绝大多数发行版使用 gzip 轮转） |
| 被篡改的命令无法自证 | 只记录 hash，需外部已知 hash 数据库比对 |

## License

MIT
