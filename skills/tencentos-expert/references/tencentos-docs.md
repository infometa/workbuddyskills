---
name: tencentos-docs
description: 提供 TencentOS Server 产品文档的实时查询能力。通过 web_fetch 实时抓取腾讯云 官方文档，确保信息始终是最新的。覆盖版本信息、维护周期、产品特性、CentOS 迁移 指南、镜像更新日志、安全公告、常见问题等。
description_zh: TencentOS Server 产品文档实时查询
description_en: TencentOS Server documentation real-time query
version: 1.0.0
---

# TencentOS Server 文档查询

提供 TencentOS Server 产品文档的**实时查询**能力。通过抓取腾讯云官方文档获取最新信息，包括版本信息、维护周期、产品特性、CentOS 迁移指南、镜像更新日志、常见问题等。

## 安全原则

> ⚠️ **重要**：AI 可自动执行只读的查看和诊断命令。
>
> 涉及系统迁移、内核升级等重大变更操作，仅作为参考提供给用户，由用户自行判断和手动执行。
> 操作前务必备份数据。

## 核心工作方式：实时抓取官方文档

> 🔑 **本 skill 的核心原则**：
>
> **不要依赖任何写死的信息回答用户！所有产品信息必须通过 `web_fetch` 实时获取腾讯云官方文档。**
>
> 版本号、维护周期、更新日志等信息随时可能变化，只有实时抓取才能确保回答的准确性。

### 文档 URL 映射表

根据用户问题类型，选择对应的文档 URL 进行实时抓取：

| 问题类型 | 文档名称 | URL | 抓取时机 |
|----------|----------|-----|----------|
| 产品概述/简介 | 产品概述 | `https://cloud.tencent.com/document/product/1397/72777` | 用户问"TencentOS 是什么"等概述性问题 |
| 产品优势/特性 | 产品优势 | `https://cloud.tencent.com/document/product/1397/72778` | 用户问"TencentOS 有什么优势""为什么选择 TencentOS" |
| 应用场景 | 应用场景 | `https://cloud.tencent.com/document/product/1397/72779` | 用户问"TencentOS 适用于什么场景" |
| 版本信息/维护周期/EOL | 版本支持说明 | `https://cloud.tencent.com/document/product/1397/110955` | 用户问版本、维护周期、生命周期、EOL 等 |
| 镜像更新日志 (TencentOS 2/3) | 镜像更新日志 | `https://cloud.tencent.com/document/product/1397/72788` | 用户问最新版本、更新了什么 |
| 镜像更新日志 (TencentOS 3.1) | TencentOS Server 3.1 更新日志 | `https://cloud.tencent.com/document/product/1397/72791` | 用户问 TencentOS 3 的更新 |
| 镜像更新日志 (TencentOS 4) | TencentOS Server 4 更新日志 | `https://cloud.tencent.com/document/product/1397/107233` | 用户问 TencentOS 4 的更新 |
| 使用方式/安装 | 使用方式 | `https://cloud.tencent.com/document/product/1397/72781` | 用户问如何安装、使用 TencentOS |
| CentOS 迁移 | CentOS 迁移指引 | `https://cloud.tencent.com/document/product/213/70900` | 用户问 CentOS 迁移 |
| 迁移流程详细说明 | 迁移流程说明 | `https://cloud.tencent.com/document/product/1397/110996` | 用户问迁移的详细步骤、原理 |
| 常见问题 | 常见问题 | `https://cloud.tencent.com/document/product/1397/72782` | 用户问 FAQ 或其他问题在其他文档中找不到答案 |
| 安全公告/漏洞 | 安全公告 | `https://cloud.tencent.com/document/product/1397/72789` | 用户问安全公告、漏洞修复 |
| 上游停服计划 | 操作系统停止维护计划 | `https://cloud.tencent.com/document/product/1397/68519` | 用户问 CentOS/Ubuntu 等上游停服时间 |

### 查询流程（每次必须执行）

**当用户提出与 TencentOS 文档相关的问题时，按以下流程操作：**

#### 第 1 步：分析问题意图，确定需要抓取的文档

根据用户问题的关键词，从上面的"文档 URL 映射表"中选择一个或多个需要抓取的文档 URL。

**关键词 → 文档映射示例**：
- "TencentOS 版本""维护周期""EOL""生命周期""停止维护" → 版本支持说明
- "TencentOS 优势""为什么选择""和 CentOS 对比" → 产品优势
- "TencentOS 是什么""简介""概述" → 产品概述
- "最新版本""更新了什么""内核版本" → 镜像更新日志
- "CentOS 迁移""怎么迁移""迁移工具" → CentOS 迁移指引 + 迁移流程说明
- "安全公告""漏洞""安全更新" → 安全公告
- "CentOS 停服""Ubuntu 停服" → 操作系统停止维护计划
- 其他/不确定 → 常见问题 + 产品概述

#### 第 2 步：使用 web_fetch 实时抓取文档

对确定的每个文档 URL，调用 `web_fetch` 工具获取最新内容。

**调用示例**：

```
web_fetch(
  url="https://cloud.tencent.com/document/product/1397/110955",
  fetchInfo="获取 TencentOS Server 版本支持说明，包括各版本的生命周期、维护阶段、时间线"
)
```

**重要**：
- 可以**并行**抓取多个文档以提高效率
- `fetchInfo` 参数应描述需要从页面中提取的具体信息
- 如果抓取失败，告知用户并提供文档的直达链接，让用户自行查看

#### 第 3 步：基于抓取内容回答用户

将实时获取的文档内容整理后回答用户问题，并在回答末尾附上文档来源链接。

**回答格式建议**：
- 使用表格、列表等结构化形式展示信息
- 标注信息来源文档链接
- 如果涉及操作（如迁移），明确标注为"仅供参考，请用户手动执行"

## 适用场景

### 用户可能的问题表述

**版本信息查询**：
- "TencentOS 有哪些版本"、"TencentOS 4 是什么"
- "TencentOS 和 CentOS 什么关系"、"TencentOS 兼容 CentOS 吗"
- "TencentOS 内核版本是多少"、"tkernel4 是什么"

**维护周期查询**：
- "TencentOS 维护到什么时候"、"TencentOS 3 什么时候 EOL"
- "TencentOS 生命周期多长"、"版本支持说明"
- "TencentOS 2 还维护吗"、"停止维护时间"

**产品特性了解**：
- "TencentOS 有什么优势"、"为什么用 TencentOS"
- "TencentOS 云原生特性"、"热补丁是什么"
- "TencentOS 和其他 Linux 发行版有什么区别"

**CentOS 迁移**：
- "CentOS 怎么迁移到 TencentOS"、"CentOS 停服了怎么办"
- "CentOS 7 迁移"、"CentOS 8 迁移"
- "迁移有什么风险"、"迁移工具怎么用"

**安全相关**：
- "TencentOS 安全公告"、"漏洞怎么修复"
- "TencentOS 安全认证"、"安全更新"

**更新日志**：
- "TencentOS 3 最新版本是什么"、"TencentOS 4 最近更新了什么"
- "镜像更新日志"、"内核升级了吗"

## 诊断步骤（AI 可自动执行）

以下命令为只读查看命令，可由 AI 自动执行，用于识别用户当前的系统环境。

### 步骤 1：识别当前系统版本

```bash
# 查看操作系统版本
cat /etc/os-release

# 查看内核版本
uname -r

# 查看 TencentOS 版本详情
cat /etc/tlinux-release 2>/dev/null || echo "非 TencentOS 系统"

# 查看 release 包版本
rpm -q tencentos-release 2>/dev/null || rpm -q tlinux-release 2>/dev/null || echo "未安装 release 包"
```

### 步骤 2：检查系统基础信息

```bash
# 系统架构
uname -m

# 启动方式（BIOS/UEFI）
[ -d /sys/firmware/efi ] && echo "UEFI 启动" || echo "BIOS 启动"

# 已安装的内核列表
rpm -qa | grep -E "^kernel-[0-9]"

# 系统运行时间
uptime
```

### 步骤 3：查看已安装关键组件版本

```bash
# GCC 版本
gcc --version 2>/dev/null | head -1

# glibc 版本
ldd --version 2>/dev/null | head -1

# Python 版本
python3 --version 2>/dev/null

# systemd 版本
systemctl --version 2>/dev/null | head -1
```

---

## 回答示例

### 示例 1：用户问"TencentOS 3 什么时候停止维护"

**AI 应执行的操作**：

1. 调用 `web_fetch` 抓取 `https://cloud.tencent.com/document/product/1397/110955`（版本支持说明）
2. 从返回内容中提取 TencentOS Server 3 的生命周期时间线
3. 整理回答，附上文档来源链接

### 示例 2：用户问"CentOS 7 怎么迁移到 TencentOS"

**AI 应执行的操作**：

1. 并行抓取两个文档：
   - `https://cloud.tencent.com/document/product/213/70900`（CentOS 迁移指引）
   - `https://cloud.tencent.com/document/product/1397/110996`（迁移流程说明）
2. 从返回内容中整理迁移步骤
3. 标注"涉及系统变更，仅供参考"，附上文档来源链接

### 示例 3：用户问"TencentOS 4 最近更新了什么"

**AI 应执行的操作**：

1. 调用 `web_fetch` 抓取 `https://cloud.tencent.com/document/product/1397/107233`（TencentOS Server 4 更新日志）
2. 从返回内容中提取最近的更新记录
3. 整理回答，附上文档来源链接

### 示例 4：用户问"TencentOS 有什么优势"

**AI 应执行的操作**：

1. 调用 `web_fetch` 抓取 `https://cloud.tencent.com/document/product/1397/72778`（产品优势）
2. 从返回内容中整理核心优势列表
3. 整理回答，附上文档来源链接

---

## 常用文档链接汇总（供 AI 快速定位）

| 文档 | 链接 |
|------|------|
| 产品概述 | https://cloud.tencent.com/document/product/1397/72777 |
| 产品优势 | https://cloud.tencent.com/document/product/1397/72778 |
| 应用场景 | https://cloud.tencent.com/document/product/1397/72779 |
| 版本支持说明 | https://cloud.tencent.com/document/product/1397/110955 |
| 使用方式 | https://cloud.tencent.com/document/product/1397/72781 |
| 常见问题 | https://cloud.tencent.com/document/product/1397/72782 |
| 镜像更新日志（总览） | https://cloud.tencent.com/document/product/1397/72788 |
| TencentOS 3.1 更新日志 | https://cloud.tencent.com/document/product/1397/72791 |
| TencentOS 4 更新日志 | https://cloud.tencent.com/document/product/1397/107233 |
| 安全公告 | https://cloud.tencent.com/document/product/1397/72789 |
| 操作系统停止维护计划 | https://cloud.tencent.com/document/product/1397/68519 |
| CentOS 迁移指引 | https://cloud.tencent.com/document/product/213/70900 |
| 迁移流程说明 | https://cloud.tencent.com/document/product/1397/110996 |
| TencentOS 官网 | https://cloud.tencent.com/product/ts |
| 腾讯云镜像站 | https://mirrors.tencent.com/ |

## 注意事项

1. **始终实时查询**：回答任何产品信息类问题前，必须通过 `web_fetch` 获取最新文档，不要凭记忆或缓存数据回答
2. **并行抓取**：涉及多个主题的问题，应并行抓取多个文档以提高响应效率
3. **标注来源**：回答中必须附上信息来源的官方文档链接
4. **抓取失败处理**：如 `web_fetch` 失败，告知用户并直接提供文档链接供用户自行查看
5. **操作类警告**：涉及系统迁移、内核升级等操作时，明确标注为参考信息，提醒用户手动执行并备份

## 相关技能

- **repo-source**：软件源配置管理（yum/dnf/pip/npm 源配置）
- **package-version**：软件包版本查询与管理
- **cve-check**：CVE 漏洞检查与修复状态确认
