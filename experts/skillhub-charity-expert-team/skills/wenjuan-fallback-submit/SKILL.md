---
name: wenjuan-fallback-submit
description: |
  SkillHub 运维专家的腾讯问卷提交通道：自动打开指定的腾讯问卷链接，
  把技能包（Skill）、材料包（Material）、meta.json 打包后的 Meta 三个 zip 字段依次
  上传并提交。本技能是运维专家 MCP 直传（首选）失败后的**次选降级通道**，仅在
  `request_upload`/上传/`get_submission_status` 判定失败时才被调用。
  触发词：问卷提交、问卷兜底提交、腾讯问卷自动提交、wenjuan fallback、
  技能包上传、MCP backup。
  ⚠️ 不适用于：与 SkillHub 无关的其他问卷填报需求、需要人工登录/
  验证码交互才能完成的场景（此时应转人工，见「失败降级」）。
category: productivity
allowed-tools: Bash,Read,Write
version: 1.0.0
author: Tencent_SSV_Tech4Good
---

# 腾讯问卷自动提交（MCP Backup 通道）

## 概述

本技能是《SkillHub 公益专家团》运维专家（J）的腾讯问卷提交通道。它通过浏览器自动化打开指定的腾讯问卷链接，把 `Meta`（meta.json 打包为 zip）、`Material`（材料包 zip）、`Skill`（技能包 zip）三个必填的文件上传字段依次填好并提交，替代人工手动打开问卷上传，尽量保留"全自动"体验。设计背景与决策见 `charity/skillhub.md` 第 3.9 节。

本技能是 **MCP 直传失败后的次选降级通道**（触发条件：`skillhub-ops-expert.md` 步骤 5 的 `request_upload`/上传 curl/`get_submission_status` 判定为不可自动重试的失败），不作为默认主路径调用。

> ⚠️ **实测结论（2026-07-08）**：该问卷虽在后台配置了"仅允许指定手机号提交"，但**实测填答与提交全程未触发短信验证码或登录环节**，纯浏览器自动化即可无人值守完成提交。若后续问卷配置发生变化导致提交时出现验证提示，脚本会自动识别并返回 `manual_required` 状态（见「失败降级」），不会静默失败。

## 🎯 能力边界

### ✅ 能做什么
- 把 `meta.json` 打包为 `meta.zip`，连同已有的技能包/材料包 zip 依次上传到指定腾讯问卷的三个字段（Meta/Material/Skill）并点击提交
- 校验三个文件均存在、非空、且单文件不超过问卷限制的 10MB
- 提交前后自动截图留证（成功/失败/异常均截图），便于人工核查
- 识别"字段结构被改动"（字段数不为 3）、"意外出现手机验证/验证码"等异常场景，并明确分类返回，不伪装成功

### ❌ 不做什么（越界即拒绝）
- ❌ 不作为 MCP 的常规替代通道，**仅在 MCP 提交失败后才由运维专家调用**
- ❌ 不负责打包技能包/材料包本身（那是 `pack_and_hash.sh` 的职责），只负责 meta.json → zip 的打包
- ❌ 不处理需要人工登录 / 输入短信验证码才能继续的场景——遇到即返回 `manual_required`，交还人工，不代替用户接收验证码
- ❌ 不修改、不重试上传逻辑之外的问卷内容（如问卷标题、题目结构），也不用于与 SkillHub 无关的其他问卷填报任务
- ❌ 不在脚本内部做失败重试（遵循 U5：单次失败即降级，重试策略由调用方/运维专家决定）

**越界拒绝标准**：当请求超出上述范围时，明确告知："本技能专注 SkillHub MCP 提交失败后的腾讯问卷应急填报，你的需求不在能力范围内。"

## 🛠️ 工具能力声明

`allowed-tools: Bash,Read,Write`（最小权限原则）

| 工具 | 可用范围 | 禁止用途 |
|------|---------|---------|
| Bash | 执行 `scripts/submit_via_wenjuan.py`（首次使用需 `pip install -r requirements.txt` + `playwright install chromium`） | 不用于任何与本流程无关的系统命令 |
| Read | 读取待上传的 meta.json / 技能包 / 材料包路径是否存在 | 不读取与本任务无关的文件 |
| Write | 脚本内部把 meta.json 打包写出 `meta.zip`，以及写出截图证据文件 | 不覆盖用户其它文件 |

> 本技能不声明 `execute_command`/浏览器自动化专用工具，浏览器交互全部封装在 `scripts/submit_via_wenjuan.py` 内部（Playwright Python），调用方只需通过 `Bash` 运行该脚本一次，无需自己逐步操作浏览器。

## ✅ 执行前置校验（U4）

调用前必须确认（脚本内部也会做同样校验，失败会给出中文报错）：

1. `--skill-zip`、`--material-zip` 指向的 zip 文件确实存在、非空、单文件 ≤ 10MB（问卷限制）
2. `--meta-json` 指向的 `meta.json` 文件存在（脚本会自动打包为 `meta.zip`，无需提前手动打包）
3. 首次使用时已执行依赖安装：`pip install -r requirements.txt && python3 -m playwright install chromium`（Windows 上 `python3` 命令可能不可用，改用 `python -m playwright install chromium`）
4. 确认本次调用确实是 MCP（`request_upload`/上传/`get_submission_status`）已判定失败后触发，而非默认主路径

## 工作流程

### 步骤 1：准备 meta.json

运维专家在调用本技能前，先准备好一份结构化的 `meta.json`（作为后续人工从问卷补录到正式后端时的机器可读依据），建议字段：

```json
{
  "submission_channel": "wenjuan_fallback",
  "submission_batch_id": "{UUID，用于去重与追溯}",
  "submitted_at": "{ISO8601 时间}",
  "skill_name": "{技能名}",
  "version": "{版本号}",
  "skill_md5": "{pack_and_hash.sh 算出的技能包 MD5}",
  "material_md5": "{pack_and_hash.sh 算出的材料包 MD5}",
  "wb_user_id": "{读取到的 WorkBuddy 本地用户标识}",
  "author": { "org_name": "{机构名称}", "contact_name": "{姓名}", "phone": "{手机号，未提供则为空字符串}" }
}
```

### 步骤 2：调用脚本自动提交

```bash
python3 {baseDir}/scripts/submit_via_wenjuan.py \
  --skill-zip <技能包.zip 路径> \
  --material-zip <材料包.zip 路径> \
  --meta-json <meta.json 路径> \
  --output-dir ~/.workbuddy/skillhub-outputs/wenjuan
```

> 💡 **跨平台命令兼容性**：Windows 上 Python 启动器通常只注册 `python`（无 `3` 后缀），执行 `python3` 若报"command not found"，改用 `python {baseDir}/scripts/submit_via_wenjuan.py ...`（不带 3）重试；macOS/Linux 按 `python3` 执行即可。

脚本自动完成：meta.json 打包为 zip → 依次上传 Meta/Material/Skill 三个字段 → 点击提交 → 校验"问卷到此结束"确认文案 → 截图留证 → 输出单行 JSON 结果到 stdout。

### 步骤 3：解析结果并回报

| 返回 `status` | 含义 | 运维专家应对方式 |
|---|---|---|
| `success` | 已成功提交到问卷 | 向主理人回报"已通过腾讯问卷通道提交成功"+ 截图路径 + 明确告知用户"当前为过渡期通道，处理时效可能变长" |
| `manual_required` | 提交时意外出现手机验证/验证码环节 | 回报主理人：无法自动完成，需人工打开问卷链接手动验证提交，附截图证据 |
| `failed` | 文件校验失败 / 页面结构异常 / 其它异常 | 回报主理人具体 `error` 信息，按「失败降级」处理，不重试 |

## 🛡️ 失败降级策略（U5）

| 失败类型 | 触发条件 | 降级/处置 |
|---|---|---|
| 依赖缺失 | 未安装 playwright / 浏览器 | 返回 `failed` + 安装指引，不静默失败 |
| 文件校验失败 | zip 不存在/为空/超 10MB | 返回 `failed` + 具体文件与原因，terminate，不尝试压缩或截断文件 |
| 问卷结构变化 | 上传字段数 ≠ 3 | 返回 `failed`，提示"问卷可能已被修改，需人工核实" |
| 页面渲染超时 | 15s 内上传字段未出现 | 返回 `failed`，截图留证，判定为网络或页面异常 |
| 意外验证环节 | 提交后出现"验证码"/"手机号验证"关键词 | 返回 `manual_required`，转人工，**不代替用户接收/输入验证码** |
| 提交后无成功文案 | 15s 内未出现"问卷到此结束" | 返回 `failed`，截图留证 |

**🚫 严禁行为**：
- ❌ 脚本内部反复重试提交（单次失败即返回，遵循 U5：≥ 2 次同类失败视为缺陷）
- ❌ 把 `manual_required` 误判为 `failed` 或 `success`——三种状态必须清晰区分并如实回报
- ❌ 在未确认三个源文件真实存在的情况下臆造上传结果

## 🚫 数据真实性约束（U6）

- 提交结果的 `status`/`screenshot`/`submitted_at` 必须来自脚本对页面真实状态的判定，**禁止在未实际运行脚本的情况下描述提交成功**
- meta.json 中的 `skill_md5`/`material_md5` 必须来自 `pack_and_hash.sh` 的真实输出，**禁止 AI 编造或估算**

## 依赖

- Python 3.9+
- `pip install -r {baseDir}/requirements.txt`（即 `playwright`）
- `python3 -m playwright install chromium`（Windows 上 `python3` 命令可能不可用，改用 `python -m playwright install chromium`；首次使用需下载浏览器内核，约 100MB）
- 网络可访问 `wj.qq.com`

## 与 MCP 主通道的关系

```
运维专家提交 MCP（request_upload → 上传 → get_submission_status，首选）
   ↓ 失败（不可自动重试的错误码，或重试后仍失败）
本技能：腾讯问卷自动填报提交（次选，本技能职责范围）
   ↓ manual_required（触发意外验证）/ failed
引导用户/人工手动打开问卷完成提交，或本地导出兜底（最终兜底）
```

> 是否降级到本技能、以及本技能失败后如何处理，由 `skillhub-ops-expert` 按上述降级链路决定，不在本技能内部自行判断是否该被调用。
