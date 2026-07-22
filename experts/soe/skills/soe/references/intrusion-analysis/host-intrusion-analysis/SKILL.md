---
name: host-intrusion-analysis
version: 4.3.0-external
triggers:
  - 入侵检测
  - 后门
  - webshell
  - 异常进程
  - 入侵排查
description: 入侵分析 Skill。由主机上的日志数据生成结构化的入侵分析报告。当用户说"入侵分析"、"日志分析"、"安全排查"时触发。
allowed-tools: python3, search_content, run_command, read_file
---

# 入侵分析 Skill

## 调用约定（适配说明）

本 Skill 文档使用 `run_command(...)` 作为**通用占位符**，表示"在 skill 根目录下执行一条 shell 命令并取回 stdout"。请将其映射到你的 AI Agent 框架对应的 shell 执行 API（例如 `Bash` / `shell_exec` / 自定义 tool）。映射时需保证：

1. **工作目录（cwd）**自动设置为本 skill 根目录，使相对路径（如 `scripts/analysis/preanalyze.py`、`templates/...`）可直接使用；
2. **stdout** 完整回传给 AI Agent 用于后续分析；
3. **超时**默认建议 ≥ 120 秒（预分析单主机日志通常 < 60s，多主机 ZIP 可能更长）。

## 唯一正确的调用方式

本 Skill 为**可执行工具型**，通过 shell 命令调用预分析脚本（详见上方"调用约定"），然后 AI 基于预分析输出撰写报告。

## 正确用法

```python
# 步骤 1：运行预分析脚本（路径必须是绝对路径）
# 任意类型日志文件/文件夹均可，脚本会自识别，传入用户提供的绝对路径。
# 压缩包无需解压，原样传入即可。同理，无论用户提供何种格式，均直接传入预分析脚本即可。
run_command('python3 scripts/analysis/preanalyze.py "/absolute/path/to/log.xxx"')

# 步骤 2：基于预分析输出，按需精准回查原始日志

# 步骤 3：读取模板 → 生成报告
run_command("cat templates/analysis_report_template.md")
```

## 核心规则

0. **禁止直接读取原始日志和脚本**。为减少上下文负担，禁止 `read_file` 原始日志或脚本源码。
1. **证据驱动**。每个结论必须有预分析数据支撑，无证据则标注"无法判定"。宁可误报不可漏报。
2. **交叉验证**。单源发现只是线索，多源交叉（同 IP/时间窗口出现在多个数据源）才是证据。
3. **零信任 + 数据缺失 ≠ 安全**。不假设任何操作合法。日志段为空可能是攻击者清除痕迹，标注"数据不可用，无法排除"。
4. **时间线必需（Mermaid 流程图）**。无论风险高低不可省略。从所有数据源合并统一时间线，以 Mermaid `graph LR`（左到右）流程图输出，用 classDef 颜色区分正常（绿）/可疑（橙）/高危（红）事件，≤8 个节点。禁止使用 `graph TD`。无攻击时呈现运维时间线。**⚠️ 关键：节点标签和边标注中的文本必须用双引号包裹**，如 `A["04-02 15:55 暴力破解"]`
5. **报告是独立文档且必须落盘**。禁止对话式语言，可直接交付安全团队。报告必须写入工作空间的 `.md` 文件并通过 `present_files` 展示给用户，禁止仅在对话中输出而不落盘。唯一提问场景：输入不是日志报告。
6. **严格遵循模板结构**。禁止新增模板未定义的顶级章节。补充信息内嵌到对应的模板章节中。
7. **预分析脚本是唯一脚本**。只存在 `scripts/analysis/preanalyze.py` 唯一脚本，不存在其他任何脚本，报告的编写需要由 AI+模板 完成，不存在报告编写脚本。
8. **采集脚本位于专家包内**。`scripts/linux/` 和 `scripts/windows/` 直接位于本 skill 的 scripts 目录，AI 运行时通过 `find ~/.workbuddy/plugins -name "get_log_all_in_one.*"` 定位实际绝对路径，并通过 `present_files` 工具把脚本文件本身展示给用户下载。

## 步骤 0：确认日志来源（用户未提供日志文件时触发）

当用户触发入侵分析但**尚未提供日志文件**时，用专家包内源路径在第一句话中主动引导，并调用 `present_files` 展示脚本文件本体供用户下载：

> 检测到您需要进行入侵分析。请在目标服务器上运行采集脚本生成日志文件：
>
> **Windows 服务器：**
> - 采集脚本：`references/intrusion-analysis/host-intrusion-analysis/scripts/windows/get_log_all_in_one.ps1`
> - 以管理员身份打开 PowerShell，运行：
>   ```
>   powershell -ExecutionPolicy Bypass -File get_log_all_in_one.ps1
>   ```
>
> **Linux 服务器：**
> - 采集脚本：`references/intrusion-analysis/host-intrusion-analysis/scripts/linux/get_log_all_in_one.sh`
> - 以 root 权限运行：
>   ```
>   sudo bash get_log_all_in_one.sh
>   ```
>
> 采集完成后，将生成的 `log_*.txt` 文件路径告诉我即可。

> 🚫 **门控检查**：用户是否提供了日志文件路径？
> - ✅ 提供了文件路径 → 进入步骤 1
> - ❌ 用户表示无法采集 → 告知"无日志文件无法进行分析"，终止流程

## 步骤 1：运行预分析脚本

使用 `run_command` 执行预分析脚本（cwd 已自动设置为 skill 根目录，脚本路径用 `scripts/analysis/preanalyze.py`，**日志路径必须是绝对路径**）。

```
run_command('python3 scripts/analysis/preanalyze.py "<绝对路径>"', timeout=120)
```

> 🚫 **门控检查**：预分析脚本是否成功返回了结构化数据？
> - ✅ 返回了 `## 摘要` + 各章节数据 → 继续步骤 2
> - ❌ 返回错误/异常 → 检查日志路径是否正确（必须是绝对路径），修正后重试一次。两次失败则告知用户并终止
> - ❌ 返回数据但所有章节均为 `not_found` → 告知用户"日志文件可能格式不匹配或为空"，终止流程，**禁止生成空报告**

## 步骤 1.5：日志来源校验（预分析成功后执行）

预分析脚本成功返回后，检查日志是否由标准采集脚本生成。**同时检查两项**：

**检查 A — 文件名模式：**
标准采集脚本生成的文件名匹配 `log_*.txt` 模式。

**检查 B — 预分析输出头部标记：**
预分析输出头部包含 `platform:` 行。若日志来自标准采集脚本，头部不含 `data_source: raw_var_log_folder` 或 `LinuxCheck.sh` 等非标准来源标识。

**判断规则：** 文件名不匹配 `log_*.txt` **或** 预分析头部含非标准来源标识 → 判定为"非标准采集脚本日志"。

**若判定为非标准日志**，在最终分析报告**最开头**插入以下提醒块，然后继续输出完整分析报告：

```markdown
> ⚠️ **日志来源提醒**
>
> 当前分析的日志并非由标准采集脚本生成，部分分析维度可能数据不完整。
>
> 建议下次使用标准采集脚本以获得更全面的入侵分析覆盖（9 大维度）：
>
> | 平台 | 脚本路径（专家包内源路径） | 运行方式 |
> |------|---------|---------|
> | Windows | `references/intrusion-analysis/host-intrusion-analysis/scripts/windows/get_log_all_in_one.ps1` | 管理员 PowerShell 运行 |
> | Linux | `references/intrusion-analysis/host-intrusion-analysis/scripts/linux/get_log_all_in_one.sh` | `sudo bash` 运行 |
>
> ---
>
```

提醒块之后**不要中断**，继续按步骤 2、步骤 3 完成完整分析报告。

## 步骤 2：基于预分析输出进行按需精准回查

基于预分析输出，**按需**精准回查：仅当数据状态为 `error` 或预分析数据不足以支撑研判时，用 `search_content` 按关键词搜索原始日志补充证据。

**Token 安全限制**：
- ❌ 禁止 `read_file` 整个原始日志
- ✅ 仅用 `search_content` 搜索特定关键词，单次回查结果控制在 50 行以内
- ✅ 如需更多上下文，缩小搜索范围（加时间戳/IP 过滤），不要放大

> 🚫 **门控检查**：是否已获得足够的入侵攻击时间线数据（用于生成 Mermaid 流程图）？
> - ✅ 已完成 → 继续步骤 3

## 步骤 3：报告生成

## 3a. 读取模板（必须在生成报告前执行）：

通过 `run_command` + `cat` 读取模板文件（cwd 已自动设置为 skill 根目录）：

```
run_command("cat templates/analysis_report_template.md")
```

> ⚠️ **禁止用 `read_file` 读取模板文件**——模板没有固定的绝对路径，`read_file` 会失败。
## 3b. 撰写报告、落盘并展示

严格以模板结构为骨架填充数据，不得自行改变章节顺序或标题格式。

**报告必须落盘**，按以下流程执行（禁止仅在对话中输出而不写文件）：

1. **写入文件**：将完整报告写入当前工作空间的 `reports/` 目录（若不存在则先创建）。
   - 文件命名规则：`入侵分析报告_<主机名或事件名>_<YYYYMMDD-HHmmss>.md`
   - 单主机示例：`入侵分析报告_lavm-xile9vly1p_20260721-1445.md`
   - 多主机示例：`入侵分析报告_2000-00入侵事件_20260721-1445.md`
   - 时间戳通过 shell 命令 `date +%Y%m%d-%H%M%S` 获取，禁止硬编码。

2. **展示文件**：落盘后**必须**调用 `present_files` 工具把报告文件展示给用户，让用户可直接查看/下载/转发。

3. **对话回复**：在对话中给出简要结论（风险等级 + 最关键 2-3 条发现 + 报告文件路径），不要把整份报告内容复制到对话中（用户已通过 `present_files` 看到完整报告）。

## 边缘情况处理

| 场景 | 处理方式 |
|------|---------|
| 预分析返回错误 | 检查路径后重试一次，两次失败则告知用户并终止 |
| 预分析所有章节 `not_found` | 告知用户"日志格式不匹配或为空"，终止，**禁止生成空报告** |
| 精准回查找不到数据 | 标注"数据不可用，无法排除"，不要编造 |
| 报告生成中断/截断 | 标注"⚠️ 报告不完整：以下章节因上下文限制未能生成" |

## 质量检查清单

- [ ] 预分析脚本是否实际执行过（非编造数据）
- [ ] 报告中每个结论是否有预分析数据对应的证据
- [ ] 模板所有顶级章节是否齐全
- [ ] 攻击时间线是否存在且为 Mermaid `graph LR` 流程图格式（即使无攻击也需呈现运维时间线）
- [ ] **报告是否已落盘到 `reports/` 目录并通过 `present_files` 展示给用户**（禁止仅在对话中输出）
