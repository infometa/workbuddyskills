---
name: adc-sandbox-usage
description: >
  How to use the ADC zone runtime-domain connector correctly. It is the execution face shared by the
  environment-setup, zone-ops and data-management work modes: the ADC job workflow (template -> task ->
  Argo log) for training, QC and labeling jobs, data files, collect plans, mining and multimodal retrieval,
  host and TKE evidence collection, cloud resource queries, and image build/push to the zone registry.
  Covers call order, the write gate (two-phase confirmation; show the summary to the user, then send back
  the exact confirm_text, idempotent), what the guardrails reject, and how to read a failed job.
  Use when a task needs this connector capability inside the ADC zone. Boundary: this skill only
  explains tool usage, it performs no actions itself.
description_zh: >
  智驾沙箱连接器（运行侧）的正确用法。它是环境搭建 / 智能运维 / 数据管理三个工作模式共用的执行面：
  作业动线（模板 → 任务 → Argo 日志，覆盖训练 / 质检 / 标注 / 挖掘编排）、数据文件与采集计划、
  多模态检索、主机与 TKE 取证排障、云资源查询、镜像构建推送（把代码 / 镜像推到专区仓库），
  以及会被拒绝的操作与失败怎么读。触发词：需要该连接器能力的智驾专区任务。
  边界：本技能只讲用法，不执行任何动作；工具面一律以运行时 `tools/list` 为准。
  写操作（建任务 / 下发 / 重试 / 复制模板、跳板机执行命令、提交或取消镜像构建）一律两段式确认
  （把 summary 念给用户，同意后带原样 `confirm_text` 再调），服务端有幂等键。
  审批与工单的能力在同一连接器上，用法见 `adc-approval-usage`。
description_en: >
  How to use the ADC sandbox connector (runtime side) correctly: the execution face shared by the
  environment-setup, zone-ops and data-management work modes, including the job workflow, host and TKE
  triage, cloud resource queries (read actions by verb prefix; write actions only via the server-side
  allowlist) and image build/push to the zone registry; call order, guardrails and how to read failures.
  Every write is gated by a two-phase confirmation and is idempotent.
  Approval and tickets live on the same connector — see `adc-approval-usage`.
display_name: 运行域连接器用法
display_name_en: ADC Sandbox Connector Usage
version: 0.4.14
author: ADC Copilot Team
---


# 智驾沙箱连接器 · 运行侧 使用说明

## 工具面（**一律以运行时为准**）

工具**按配置注册**：宿主只注册已配置的上游 —— 未配置的上游不会出现在你的工具列表里。

**所以这里不列工具清单**：它是"当前事实"，随上游增减而变，写进文档第二天就可能过期。
工具名与参数一律以**运行时**看到的为准（`tools/list`，或先搜一次把工具找出来）；
**不要凭印象"补"出一个工具名，也不要编造结果**。

本连接器按上游分这几组能力（审批与工单那两组见 `adc-approval-usage`）：

| 上游 | 能做什么 | 写侧 |
|---|---|---|
| **作业域（DMS 直连）** | 作业模板、作业任务与 Argo 日志（训练 / 质检 / 标注 / 挖掘编排）、数据文件与采集计划、多模态检索、本层动作自查 | 有 |
| **主机排障（跳板机）** | 连通性探测、白名单只读命令（⚠️ 见下方「`>` 字符陷阱」）、**经确认的**写命令与脚本 | 有 |
| **TKE 排障** | kubectl **只读**工具（对象 / 描述 / 事件 / 日志 / 资源用量） | 无（写操作经主机排障那组）|
| **云资源查询** | 任意**只读**云 API 动作（Describe / Get / List / Search / Check / Query / Inquire）；写动作只放行**服务端白名单**里的那几个，未列入的一律拒 | 有（**经确认的**白名单写动作，须两段式确认 + 幂等）|
| **镜像构建推送** | 服务状态、提交构建、轮询与取消、常驻运行时直发代码 | 有 |
| **库存与客户资源（ADCM）** | 可用区机型余量、趋势、告警、预扣、客户已用量（按服务端配置注册）| 无 |
| **反馈采集** | 用户评价/异议的回执采集；只回执、不落库（契约如此，不随上游配置变化） | 有（提交回执，不需要两段式确认）|
| **CLS 日志 / 网络诊断** | **没有专用工具** —— 查询面经云 API 的只读动作可达 | 无 |

> ⚠️ **TKE 没有自己的写工具**：`kubectl apply` / `delete` / `scale` / `rollout restart` 这类写操作，
> 只能经**主机排障那组的写工具**在**同一台跳板机**上执行（就是跑 kubectl 的那台）——
> 所以"工具面里没有 TKE 写工具"**不等于**"集群动不了"。

> ⚠️ **`>` 字符陷阱（主机排障的只读命令）**：命令里**只要出现 `>` 就会被当成重定向拒掉** ——
> 连 `struct.unpack(">I")`、`if v>m` 这种**比较 / 格式符**也会命中 ✗。判据不改，改写法：
> 用 `int.from_bytes(b, "big")` 代替 `">I"`，用 `if m<v` 代替 `if v>m`。

> ⚠️ **写工具出现在工具面里时**：作业域、跳板机、镜像构建三组的写操作，
> **每一次写都必须两段式确认 + 幂等**（见下节「写操作」）—— 缺 `confirm_text` 会被拒，且**不会触达上游**。
> 跳板机的写命令还受**两道硬拦**（都拦在两段式确认**之前**）：**A 档** = 服务/启动项类命令直接拒；
> **E 档** = **不可逆操作类**（`rm -r /`、`mkfs`、`dd of=/dev/…`、清空防火墙 / 关网卡这类会切断
> 自己链路的动作）**本地直接拒、连确认都不给** —— 这类动作**不存在"确认一下就放行"的路径**，
> 别换措辞重试，改成可回退的做法（只删自己那部分、先备份）。

> ⚠️ **工具面里看不到写工具时，先分清三种原因**（**别一律说"写侧不开放"**）：
> ① **上游没配** —— 真的没有这个能力；② **令牌缺 `mcp.write` scope**（只有 OAuth 模式有 scope 概念）
> —— 能力在，但那把令牌被 scope 挡了（写工具不出现在工具面里，调用会得 `1005`/403）：
> **让用户换一把带 `mcp.write` 的授权**（重新授权时加上该 scope，或改用静态令牌）；
> ③ **平台侧的工具索引没带上它** —— 云端 Runtime 出现过"连接器 ready 但工具进不了模型的可用列表"，
> 这时谁都调不到，**如实说明即可，不要重试、不要编结果**。

### 库存与客户资源（ADCM，只读）

**判断「部署到哪个可用区」的顺序**（具体工具名以运行时为准）：
先看**资源告警**（总量够、但某机型告警时仍会排不上）→ 再看**该区该机型的可用量** → 看**趋势**
（照这个速度还能撑多久）→ 别忘了**预扣会占用可用量** → 最后对**客户已用量**。

⚠️ 这一族**只有只读**（上游第三、五章没有写接口，也没有要确认的写操作）。
报「凭据被拒 / 不可达」时，先调那一族的**用户信息**工具，把**链路问题**与**参数问题**分开。

### 镜像构建推送（宿主直连构建机，不经窄桥）

把代码 / 镜像地址变成**推到上海侧仓库的容器镜像**（专区靠仓库的实例同步分发）。

动线（工具名以运行时为准）：

1. **先看服务状态** —— 仓库凭据配没配、docker 与对象存储依赖在不在。
2. **提交构建** —— `source` 四类：`git`（代码地址，monorepo 要给 `subdir`）· `object`（交接桶里的
   代码包，**大包走这条**）· `image`（既有镜像，拉—重打—推）· `upload`（宿主侧先流式上传）。
   **立即返回 `job_id`**。私有来源（`git` / 私有 registry）还要带**凭据引用**：引用名由管理员在
   服务侧登记，凭据值不经过对话；不确定登记过没有，先按 `tools/list` 找那一族的查询工具看一眼。
3. **轮询与拉日志** —— 构建是**分钟级**，**别同步等**；日志要增量拉。
4. **需要时取消** —— 只能取消尚未结束的任务。
5. **调试期免重建** —— **常驻运行时**里同一 `session_id` 复用同一个容器，改代码直接跑
   （文件落在 `/work/code/` 下；容器工作目录是 `/work`，所以命令要写**全路径**）；
   跑通之后再用第 2 步固化成镜像。

> ⚠️ **代码包不要塞进工具参数**（工具参数由模型生成，服务侧 JSON 上限默认 1 MB）：
> 大包先在宿主侧流式上传或放进交接桶，再以 `source.kind=object` 提交。
> **只要"代码进专区"、不出镜像**时（专区作业按对象键读代码）：上传后走那一族的**对象推送**，
> 落到**专区对象桶**的指定对象键上 —— 桶由服务端配置（你只给键）；把返回的 `bucket` + 键报给用户，
> 作业侧按它读 ✓。
> **宿主侧上传里，包大了还要再分片**（开会话 → 按 `offset` 逐片追加 → 提交收尾）：一次性吐几十 KB 的
> base64 本身就不可靠 ✗；单片 / 合计上限与会话有效期按工具面自述取，超上限改走交接桶 ✓。
>
> ⚠️ **对象推送会"自动加一段前缀"**：你请求时给的键**不等于**最终落点，服务侧会加上自己那一段 ——
> **以推送回执里的完整键为准**，作业侧按**它**写挂载前缀，别按你请求时写的那个 ✗。
> **文件名**只允许字母数字与 `.` `_` `-`，且**首位必须是字母数字**（`_keep` 这类会被拒）。
> **推完要三方核对**（本地 / 挂载点 / 回执）：COS 客户端有**本地缓存**，"脚本说写入成功"
> **不等于**对象已落桶 —— 在**另一台机器**的挂载点上 `ls` 到才算数 ✓。

## 写操作：两段式确认 + 幂等（**人工复核就在这一步**）

**写工具都是两段式**，照这个顺序用，别跳：

1. **先不带 `confirm_text` 调一次** —— 返回 `summary`（这一步要做什么）与**应原样回传**的 `confirm_text`。
2. **把 `summary` 念给用户**（带对象与影响范围），等他明确同意。
3. **带原样的 `confirm_text` 再调一次** —— 参数必须与第一次**完全一致**；同参数只会执行一次（幂等键在服务端）。

- **术语统一**：确认串（`confirm_text`）+ 幂等键 —— 不要叫"令牌"。
- **参数变了就重新确认**：中途补参数（补 `cluster_name`、补 `params`）会换一个新确认串 ⇒ 回到第 1 步。
- **不要猜 `confirm_text`**；也不要因为第二次调用"没反应"就反复重试（幂等键会保持同一次执行，重试只污染判断）。
- ⚠️ **跳板机写命令另有两道前置**：**A 档**（服务 / 启动项类：`systemctl restart/stop/reload`、
  `reboot`、`crontab`）与 **E 档**（不可逆操作类：`rm -r /`、`mkfs`、`dd of=/dev/…`、
  清空防火墙 / 关网卡），拦在两段式确认**之前** —— 命中时连 `summary` 都不会生成；
  **别换措辞重试**（这类动作没有"确认一下就放行"的路径）。

## 作业动线（DMS 语义）

排查从"结果"往回走，别从猜开始：

1. `dms_task_list` 筛出目标作业（关注状态码）。
2. `dms_task_get(id)` 看 `status`、`argoWorkflowName` 与各节点配置。
3. `dms_task_log(id)` 取 Argo 工作流日志 —— 失败原因基本都在这里。

**状态码是固定取值，不要自己编**：`0` 待调度 / `1` 已下发 / `2` 执行中 / `3` 成功 / `4` 失败 / `7` 下发失败。

要新建作业时的顺序：先 `dms_data_file_list` 拿 `file_id`，
再 `dms_template_list` 选 `template_id`，然后 `dms_task_create` → `dms_task_execute`（**建完不会自动执行**，
这是 DMS 的接口形状）。

> ⚠️ 模板里的 `memoryLimit` / `memoryRequest` **必须带 `Gi` 单位**（如 `"4Gi"`）；
> 模板更新只影响**之后**创建的任务，不追溯已建任务。

> ⚠️ **下发是异步受理：`status=0` 不等于"没生效"**。刚下发（或重试）后编排器拉起有延迟，
> 立即回读大概率还停在 `0`（待调度）—— 判读要**等 1～2 分钟**再看 `status` 是否离开 `0`，
> 或用只读 kubectl 看任务 Pod 是否被拉起。**不要**回读一次 `status=0` 就下"未生效"的结论。

## 运维细节

- **端点级的注意事项与读错误判读，问 `adc_capabilities`**（只读、不联网）—— 它回答：
  本层替注入了什么、上游路径里的历史拼写、哪一族是 REST 形状、哪些接口本层不持有 schema，
  以及失败时怎么区分「**没查到**」（上游业务的正常回执，带原文 `code`/`msg`）与
  「**查不了**」（本层失败：上游超时 / 配置缺失 / 动作不在白名单）。
  ⚠️ 这些是**代码级事实**，所以只在服务端回答、不进包（进包就得跟着升版重发，且很容易过期）；
  包内文本只留**判据**：两类失败下一步完全不同，**都别编一个结果出来**。
  ⚠️ **工具面里没有 `adc_capabilities` 时**（本地形态的包**不在本仓库**）—— 按上面这条判据判读。

## 失败定位

先 `dms_task_get` 看状态与节点 → `dms_task_log` 取日志 → 按现象定位环节：

| 现象 | 最可能原因 |
|---|---|
| 显存不足 / OOM | 批次过大或资源与节点不匹配 |
| 数据路径不存在 | 挂载路径与模板配置不一致 |
| 依赖版本冲突 | 镜像基线与代码要求不一致 |
| 启动即退出 | 入口命令错误或缺环境变量 |
| 超时被回收 | 资源不足或存在死循环 |
| 状态停在 `7` 下发失败 | 调度侧问题，不是作业自身失败 |

**区分「没跑成」与「跑了但结果不好」** —— 两类问题的下一步完全不同。

## 硬约束

- **不静默重试**：失败先定位，再由用户决定是否重跑（`dms_task_retry` **可用**，但不等于可以替你决定重跑）。
- **别凭印象编 Id**：模板 Id、任务 Id、`file_id` 都要从查询工具拿到。
- **引用日志只取必要片段**：日志可能很长、可能含内部路径 —— **长度本层不裁剪**。
- **凭据类字段会被自动剥掉**：模板配置、返回值与命令输出在返回给你之前，已按「键名 / `name`-`value` 配对 /
  高置信模式」剥掉凭据（`AKID…`、`sk-…`、JWT、PEM 私钥、`password=…` 这类）。所以**某字段拿不到不等于它不存在**
  —— 先考虑是被裁剪了，**别据此猜值，也别反复重试**。
- **写操作必须用户确认**：**所有**写工具都会改真实状态（作业的建 / 下发 / 重试、模板复制、
  主机命令与脚本、镜像构建与取消、常驻运行时跑代码）—— 缺 `confirm_text` 不得调用，
  也不得替用户"先做了再说"。

## 风险（如实告知，别淡化）

⚠️ DMS 的写接口**没有鉴权**（文档原话是"内网可达即可调用"）。写侧是否可用**只看工具面**：
`tools/list` 里有写工具，门槛就是**工具层的两段式确认 + 幂等**（跳板机另叠危险动词黑名单 / A/E 档硬拦）。
在 DMS 侧补上鉴权之前，**不要把写能力当作用户已授权**；用户没说清对象与影响范围时，也不要替他确认。
