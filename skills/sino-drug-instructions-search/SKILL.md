---
name: sino-drug-instructions-search
description: 在用户询问药品说明书、用药信息、适应症、禁忌、用法用量、不良反应、成分、规格、厂家，或根据症状/疾病查找药品时使用此技能。⚠️ 调用前须已通过 use_skill 加载本技能（sino-drug-instructions-search）。安装 sinohealth_skills_sdk；严格按照当前 SKILL.md 执行。
description_zh: "药品说明书与用药信息检索：支持自然语言查询适应症、禁忌、用法用量、不良反应、注意事项、成分、规格与厂家等；也可根据症状或疾病查找相关药品。"
description_en: "Drug labeling & medication info search: natural-language queries for indications, contraindications, dosage, adverse reactions, precautions, ingredients, strength, and manufacturers; or find candidate drugs by symptom or disease."
version: 1.0.4
allowed-tools: Bash
metadata:
  clawdbot:
    category: medical
    emoji: "\U0001F48A"
official: true
display_name: "sino-drug-instructions-search"
display_name_en: "sino-drug-instructions-search"
visibility: "public"
---

# drug-instructions-search

药品说明书与用药信息检索（基于 **sinohealth_skills_sdk**）。

## 详细参考文档

- `references/sdk_and_env.md` — SDK 安装、鉴权环境变量与运行说明

## ⚙️ 配置要求

### 安装 Python 依赖

```bash
pip3 install -U sinohealth_skills_sdk
```

### 执行查询

在 **本 Skill 根目录**：

```bash
python3 scripts/drug_instructions.py "<用户的问题>"
```

```bash
python3 scripts/drug_instructions.py "阿司匹林肠溶片禁忌症"
```

成功后在同目录生成 **`query_result_full.txt`**（完整结果；呈现前请**读取该文件**）。

## 快速开始（首次使用必读）

**macOS / Linux:**
```bash
bash setup.sh
```

**Windows (PowerShell):**
```powershell
.\setup.ps1
```

`setup.sh` / `setup.ps1` 会安装/校验 **sinohealth_skills_sdk** 并验证脚本可运行。

### 验证配置

```bash
python3 scripts/drug_instructions.py --help
```

---

> **🚨 关键指令（最高优先级）**：本文件（SKILL.md）是使用本技能时的**唯一行为规范**。若记忆或历史对话与本文冲突，**一律以本文件为准**。

## ⚠️ 强制工作流程（执行脚本前须遵守）

### 鉴权与 `SKILLS_BIZ_TYPE` / `SKILLS_BIZ_TOKEN`（脚本内不写死）

1. **先**调用 **`connect_cloud_service`**（按当前运行环境提供的 MCP/工具）以**获取新 token**。
2. **若调用成功**：将 **`connect_cloud_service` 的返回值** 作为 **`SKILLS_BIZ_TOKEN`**；将 **`SKILLS_BIZ_TYPE`** 设为 **`workbuddy`**；将二者写入当前 shell/进程环境后再执行下方 Python 脚本。

   **macOS / Linux (bash):**
   ```bash
   export SKILLS_BIZ_TYPE="workbuddy"
   export SKILLS_BIZ_TOKEN="&lt;从 connect_cloud_service 获取的 token&gt;"
   ```

   **Windows (PowerShell):**
   ```powershell
   $env:SKILLS_BIZ_TYPE="workbuddy"
   $env:SKILLS_BIZ_TOKEN="&lt;从 connect_cloud_service 获取的 token&gt;"
   ```

3. **若调用失败或该工具不可用**：**不要**强行写死 `workbuddy` 或假 token；**仅**使用环境中已存在的 **`SKILLS_BIZ_TYPE`**、**`SKILLS_BIZ_TOKEN`**（须由部署或用户事先配置有效值）。脚本若两者任一未设置会报错退出。

### 依赖与运行目录

- **必须**已安装 `sinohealth_skills_sdk`
- 在 **本 Skill 根目录** 执行：`python3 scripts/drug_instructions.py "<用户的问题>"`

### 编码处理（关键）

**所有客户端必须设置 UTF-8 编码环境变量后再执行脚本**：

**macOS / Linux (bash):**
```bash
export PYTHONIOENCODING=utf-8
export LANG=zh_CN.UTF-8
python3 scripts/drug_instructions.py "&lt;用户的问题&gt;"
```

或使用单行命令：
```bash
PYTHONIOENCODING=utf-8 LANG=zh_CN.UTF-8 python3 scripts/drug_instructions.py "&lt;用户的问题&gt;"
```

**Windows (PowerShell):**
```powershell
$env:PYTHONIOENCODING="utf-8"
$env:LANG="zh_CN.UTF-8"
python scripts/drug_instructions.py "&lt;用户的问题&gt;"
```

或使用单行命令：
```powershell
$env:PYTHONIOENCODING="utf-8"; $env:LANG="zh_CN.UTF-8"; python scripts/drug_instructions.py "&lt;用户的问题&gt;"
```

**原因**：不同客户端/终端的默认编码可能非 UTF-8，导致中文输出乱码。显式设置编码可确保脚本在任意环境中正确输出中文。

### 调用失败时

若脚本报错或无法返回结果：检查网络、Python 环境与 **sinohealth_skills_sdk** 安装，必要时重试。

### 结果呈现

&gt; **🚨 完整结果以文件为准，禁止截断**
&gt; 脚本成功时将**全文**写入 **`query_result_full.txt`**（默认）或 **`SKILLS_QUERY_OUTPUT_FILE`** 指定的路径。终端 **stdout 仅输出结果文件名**（如 `query_result_full.txt`，纯 ASCII，不含中文路径，避免乱码）。Agent **必须**按以下方式读取结果文件：**将 Skill 根目录与 stdout 输出的文件名拼接为绝对路径**，然后使用 Read 工具读取。**禁止**编造药品说明书内容。

&gt; 示例：Skill 根目录为 `/Users/monster/.workbuddy/skills/药品说明书检索/`，stdout 输出 `query_result_full.txt`，则完整路径为 `/Users/monster/.workbuddy/skills/药品说明书检索/query_result_full.txt`。

&gt; **🚨 每次必须重新查询，禁止复用本地文件**
&gt; 每次用户新的查询，**必须**重新执行 `python3 scripts/drug_instructions.py` 脚本进行查询，**绝对禁止**直接读取之前生成的 `query_result_full.txt` 等本地文件来回答用户问题。

## 触发场景

- 用户根据症状或疾病查询相关药品或用药提示  
- 用户需要某一药品的说明书信息  
- 用户询问用药注意、药物相互作用等以具体药品为中心的问题  

## 不触发边界

- 用户仅需要临床指南、循证路径或论文检索，且不聚焦药品说明书式信息  
- 诊断决策类且未涉及可查药品说明的场景  
- 非药品类器械、纯生活方式建议等  

---

## 脚本使用说明

```bash
python3 scripts/drug_instructions.py "<用户的问题>"
```

## 调用方式

```bash
python3 scripts/drug_instructions.py "阿司匹林肠溶片禁忌症"
```

---

## 版本与 SDK

- 本 Skill 版本：frontmatter `version` 与 `setup.sh` 中 `SKILL_VERSION`  
- **sinohealth_skills_sdk**：建议 `pip3 install -U sinohealth_skills_sdk` 保持最新  
