# AI PPT（aippt）工具完整参考文档

本文件包含金山文档 Skill 中 **AI PPT** 相关工具的 MCP API 调用方法、脚本模板和中间文件约定。

**适用范围**：`aippt.theme_*`（主题生成 PPT）与 `aippt.doc_*`（文档生成 PPT）两类场景。

---

## 推荐调用链路

### 主题生成 PPT

```
aippt.theme_questions → aippt.theme_deep_research → aippt.theme_outline → 本地格式转换 → aippt.theme_generate_html_pptx → upload_file
```

详细工作流见 `references/workflows/topic-ppt.md`

### 文档生成 PPT

```
aippt.doc_create_session → aippt.doc_outline_options → aippt.doc_outline → aippt.doc_beautify → 本地格式转换 → aippt.doc_generate_ppt → upload_file
```

详细工作流见 `references/workflows/doc-ppt.md`

### 使用建议

| 场景 | 建议 |
|------|------|
| 用户只给一句主题 | 先 `aippt.theme_questions`，补齐受众、场景、风格、重点 |
| 用户已经给出文档 | 使用 `aippt.doc_create_session` → `aippt.doc_outline_options` → `aippt.doc_outline` |
| 需要更可靠的事实资料 | 衔接 `aippt.theme_deep_research` |
| 先看结构再决定生成 | 先停在 `aippt.theme_outline` 或 `aippt.doc_outline` |
| 需要文档直出最终演示文件 | `aippt.doc_beautify` → 本地格式转换 → `aippt.doc_generate_ppt` |
| 需要最终演示文件 | 两条链路最终都需要 `{topic, outlines[]}`，主题链路用 `aippt.theme_generate_html_pptx`，文档链路用 `aippt.doc_generate_ppt` |

---

## MCP 调用规则

### 注意事项

- 通过 `mcporter` 调用本流程中的步骤时，请为每一步单独设置超时时间为 **3000 秒**
- `aippt.theme_deep_research` 的完整研究内容主要通过流式通知产生，最终 tool result 只保留摘要
- `aippt.theme_outline` 返回的 `outline` 结构可能因上游模板而变化，传给 `aippt.theme_generate_html_pptx` 时应优先使用其中正式的 `outlines` 数组
- `aippt.doc_outline` 返回的 `markdown_outline` 可能包含重复内容（大纲出现两次），建议从 `assistant_messages` 中提取最长的含 `{.topic}` 和 `{.end}` 的消息作为清洁版大纲
- `aippt.doc_outline` 的 `resume_info` 必须是**数组**，格式为 `[{type:"follow_up", id:<interrupt_id>, data:{items:[...]}}]`
- **文档链路同样需要本地格式转换**：将 `03_outline.md` + `04_beautify.json` 合并为 `{topic, outlines[]}` 后再传入 `aippt.doc_generate_ppt`
- `aippt.doc_generate_ppt` 接收 `{topic, outlines[]}` 格式，与 `aippt.theme_generate_html_pptx` 底层接口一致
- 生成速度约每页 20-30 秒，11 页以上的 PPT 生成可能耗时 4-8 分钟，请确保超时设置足够（建议 3000 秒）
- `aippt.theme_generate_html_pptx` 返回的下载链接通常带时效性，建议尽快消费
- `deep_research` 的 `references`、`outline` 结果、Markdown 大纲、格式转换后的 `outlines` 等内容可能很长，**必须先写入本地文件**，后续步骤再读取文件内容，避免命令行参数超过长度限制

### 短参数直接调用

当参数 JSON 较短（< 2000 字符）时可直接命令行调用：

```bash
mcporter call kdocs aippt.theme_questions --args '{"input":"长颈鹿科普PPT"}' --output json --timeout 3000000
```

### 长参数脚本调用

当参数 JSON 超过 2000 字符，或包含 `references`、`outlines`、`content_base64` 等长字段时，**必须使用脚本方式调用**。

#### 脚本生成与调用流程

1. 将工具参数写入 JSON 文件（UTF-8），如 `$AIPPT_WORK_DIR/03_outline_args.json`
2. 在会话临时目录生成调用脚本 `$AIPPT_WORK_DIR/_call_mcp.js`（首次生成后复用）
3. 执行：`node $AIPPT_WORK_DIR/_call_mcp.js <toolName> <argsFile> [outputFile] [timeoutMs] [serverName]`

#### 脚本模板 `_call_mcp.js`

```javascript
const { spawnSync, execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const toolName = process.argv[2];
const argsFile = process.argv[3];
const outputFile = process.argv[4] || '';
const timeoutMs = parseInt(process.argv[5] || '300000', 10);
const serverName = process.argv[6] || 'kdocs';
const STDOUT_LIMIT = 8000;
const TIMEOUT_BUFFER = 3000000;

if (!toolName || !argsFile) {
  console.error('用法: node _call_mcp.js <toolName> <argsFile> [outputFile] [timeoutMs] [serverName]');
  process.exit(1);
}

function findMcporterCli() {
  const candidates = [];
  if (process.env.MCPORTER_CLI) candidates.push(process.env.MCPORTER_CLI);
  const nodeDir = path.dirname(process.execPath);
  candidates.push(path.join(nodeDir, 'node_modules', 'mcporter', 'dist', 'cli.js'));
  const nvmDir = process.env.NVM_SYMLINK || path.join(os.homedir(), 'AppData', 'Roaming', 'nvm');
  if (process.platform === 'win32' && fs.existsSync(nvmDir)) {
    try {
      fs.readdirSync(nvmDir).filter(d => d.startsWith('v')).forEach(d => {
        candidates.push(path.join(nvmDir, d, 'node_modules', 'mcporter', 'dist', 'cli.js'));
      });
    } catch (_) {}
  }
  try {
    const g = execSync('npm root -g', { encoding: 'utf-8', timeout: 5000 }).trim();
    candidates.push(path.join(g, 'mcporter', 'dist', 'cli.js'));
  } catch (_) {}
  if (process.platform === 'win32') {
    candidates.push('C:\\Program Files\\nodejs\\node_modules\\mcporter\\dist\\cli.js');
  } else {
    candidates.push('/usr/local/lib/node_modules/mcporter/dist/cli.js');
    candidates.push('/usr/lib/node_modules/mcporter/dist/cli.js');
  }
  for (const p of candidates) { if (p && fs.existsSync(p)) return p; }
  return null;
}

const argsPath = path.resolve(argsFile);
if (!fs.existsSync(argsPath)) { console.error('[ERROR] 参数文件不存在:', argsPath); process.exit(1); }
const argsContent = fs.readFileSync(argsPath, 'utf-8').trim();
try { JSON.parse(argsContent); } catch (e) { console.error('[ERROR] JSON 不合法:', e.message); process.exit(1); }

const mcporterCli = findMcporterCli();
let result;
if (mcporterCli) {
  console.error('[INFO] mcporter cli:', mcporterCli);
  result = spawnSync(process.execPath, [
    mcporterCli, 'call', serverName, toolName,
    '--args', argsContent, '--output', 'json', '--timeout', String(timeoutMs)
  ], { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024, timeout: timeoutMs + TIMEOUT_BUFFER });
} else {
  console.error('[INFO] 尝试通过 PATH 调用 mcporter');
  result = spawnSync('mcporter', [
    'call', serverName, toolName,
    '--args', argsContent, '--output', 'json', '--timeout', String(timeoutMs)
  ], { encoding: 'utf-8', maxBuffer: 50 * 1024 * 1024, timeout: timeoutMs + TIMEOUT_BUFFER, shell: process.platform === 'win32' });
}

console.error('[INFO] Exit code:', result.status);
if (result.error) { console.error('[ERROR]', result.error.message); process.exit(1); }
const output = result.stdout || '';
if (outputFile && output.length > 0) {
  const outPath = path.resolve(outputFile);
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, output, 'utf-8');
  console.error('[INFO] 结果已写入:', outPath, '(' + output.length + ' bytes)');
}
if (output) {
  if (output.length > STDOUT_LIMIT) {
    process.stdout.write(output.substring(0, STDOUT_LIMIT));
    console.error('[INFO] stdout 已截断 (' + output.length + ' -> ' + STDOUT_LIMIT + ')');
  } else { process.stdout.write(output); }
}
if (result.stderr) {
  const cleaned = result.stderr.split('\n')
    .filter(l => !l.includes('ExperimentalWarning') && !l.includes('--experimental'))
    .join('\n').trim();
  if (cleaned) console.error(cleaned);
}
process.exit(result.status || 0);
```

#### 调用示例

```bash
# 调用 aippt.theme_outline（参数含长 references）
node $AIPPT_WORK_DIR/_call_mcp.js aippt.theme_outline $AIPPT_WORK_DIR/03_outline_args.json $AIPPT_WORK_DIR/03_outline.json 3000000

# 调用 aippt.theme_generate_html_pptx（参数含长 outlines）
node $AIPPT_WORK_DIR/_call_mcp.js aippt.theme_generate_html_pptx $AIPPT_WORK_DIR/04_config.json $AIPPT_WORK_DIR/05_ppt_result.json 2000000

# 调用 aippt.doc_outline（参数含长 resume_info）
node $AIPPT_WORK_DIR/_call_mcp.js aippt.doc_outline $AIPPT_WORK_DIR/03_doc_outline_args.json $AIPPT_WORK_DIR/03_outline.md 3000000
```

#### 关键设计要点

| 要点 | 说明 |
| --- | --- |
| 参数从文件读取 | 绕过 OS 命令行长度限制（Windows ~8191 字符） |
| `spawnSync` + `process.execPath` | 直接运行 `cli.js`，避免 PATH 查找失败 |
| 自动探测 mcporter 路径 | 按优先级搜索：环境变量 → Node 同级 → nvm → npm root -g → 默认路径 |
| `maxBuffer: 50MB` | 防止大输出被截断 |
| 超时缓冲 +30 秒 | mcporter 内部超时与外层进程超时之间留有余量 |
| stdout 截断 8000 字符 | 避免终端刷屏，完整内容写入输出文件 |
| 过滤 ExperimentalWarning | 清除 Node.js 实验性功能噪声日志 |
| 兜底 PATH 调用 | cli.js 未找到时，退化为通过 `mcporter` 命令名调用 |

### upload_file 编程 API 调用

> **`upload_file` 无法通过 `mcporter call` 命令行调用。**
> PPTX 文件转 Base64 后 `content_base64` 字段通常有几十万字符，超出 OS 命令行长度限制。
> **唯一可行方式**：在 Node.js 脚本中直接调用 mcporter 的编程 API `callOnce()`。

#### 下载脚本 `_download_pptx.js`

```javascript
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const workDir = process.argv[2];
const resultFile = path.join(workDir, '05_ppt_result.json');
const result = JSON.parse(fs.readFileSync(resultFile, 'utf-8'));
const mergedUrl = result.data
  ? result.data.merged_url
  : JSON.parse(result.content[0].text).data.merged_url;

const pptxFile = path.join(workDir, 'downloaded.pptx');
const driveId = process.argv[3];
const pptName = process.argv[4] || '演示文稿.pptx';

function download(url, dest) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    const file = fs.createWriteStream(dest);
    mod.get(url, { timeout: 60000 }, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        file.close();
        fs.unlinkSync(dest);
        return download(res.headers.location, dest).then(resolve).catch(reject);
      }
      if (res.statusCode !== 200) { file.close(); return reject(new Error('HTTP ' + res.statusCode)); }
      res.pipe(file);
      file.on('finish', () => { file.close(); resolve(); });
    }).on('error', reject);
  });
}

async function main() {
  await download(mergedUrl, pptxFile);
  const base64 = fs.readFileSync(pptxFile).toString('base64');
  const uploadArgs = {
    drive_id: driveId,
    parent_id: '0',
    name: pptName,
    content_base64: base64
  };
  fs.writeFileSync(path.join(workDir, '06_upload_args.json'), JSON.stringify(uploadArgs), 'utf-8');
  console.log('OK');
}
main().catch(e => { console.error(e); process.exit(1); });
```

调用：`node $AIPPT_WORK_DIR/_download_pptx.js $AIPPT_WORK_DIR <drive_id> "<主题>.pptx"`

#### 上传脚本 `_upload_cloud.js`

```javascript
const fs = require('fs');
const path = require('path');
const os = require('os');

const argsFile = process.argv[2];
const outputFile = process.argv[3] || '';

async function findMcporterModule() {
  const candidates = [];
  const nodeDir = path.dirname(process.execPath);
  candidates.push(path.join(nodeDir, 'node_modules', 'mcporter', 'dist', 'index.js'));
  const nvmDir = process.env.NVM_SYMLINK || path.join(os.homedir(), 'AppData', 'Roaming', 'nvm');
  if (process.platform === 'win32' && fs.existsSync(nvmDir)) {
    try {
      fs.readdirSync(nvmDir).filter(d => d.startsWith('v')).forEach(d => {
        candidates.push(path.join(nvmDir, d, 'node_modules', 'mcporter', 'dist', 'index.js'));
      });
    } catch (_) {}
  }
  if (process.platform === 'win32') {
    candidates.push('C:\\Program Files\\nodejs\\node_modules\\mcporter\\dist\\index.js');
  } else {
    candidates.push('/usr/local/lib/node_modules/mcporter/dist/index.js');
    candidates.push('/usr/lib/node_modules/mcporter/dist/index.js');
  }
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      return await import('file:///' + p.replace(/\\/g, '/'));
    }
  }
  throw new Error('mcporter module not found');
}

async function main() {
  const args = JSON.parse(fs.readFileSync(path.resolve(argsFile), 'utf-8'));
  const mcporter = await findMcporterModule();

  const result = await mcporter.callOnce({
    server: 'kdocs',
    toolName: 'upload_file',
    args: args
  });

  const output = JSON.stringify(result, null, 2);
  if (outputFile) {
    fs.writeFileSync(path.resolve(outputFile), output, 'utf-8');
  }
  const limit = 8000;
  process.stdout.write(output.length > limit ? output.substring(0, limit) : output);
}

main().catch(e => { console.error('[ERROR]', e.message); process.exit(1); });
```

调用：`node $AIPPT_WORK_DIR/_upload_cloud.js $AIPPT_WORK_DIR/06_upload_args.json $AIPPT_WORK_DIR/06_upload_result.json`

### 各调用方式适用范围

| 工具 / 步骤 | `mcporter call` 命令行 | `_call_mcp.js` 脚本 | `callOnce()` 编程 API |
| --- | --- | --- | --- |
| `aippt.theme_questions` | 可以（参数短） | 可以 | 可以 |
| `aippt.theme_deep_research` | 可以（参数短） | 可以 | 可以 |
| `aippt.theme_outline` | **不推荐**（`references` 可能很长） | **推荐** | 可以 |
| `aippt.theme_generate_html_pptx` | **不推荐**（`outlines` 可能很长） | **推荐** | 可以 |
| `aippt.doc_create_session` | 可以（参数短） | 可以 | 可以 |
| `aippt.doc_outline_options` | 可以（参数短） | 可以 | 可以 |
| `aippt.doc_outline` | **不推荐**（`resume_info` 可能较长） | **推荐** | 可以 |
| `aippt.doc_beautify` | **不推荐**（`outline` 可能很长） | **推荐** | 可以 |
| `aippt.doc_generate_ppt` | **不推荐**（`outline`+`beautify` 很长） | **推荐** | 可以 |
| `upload_file`（含 `content_base64`） | **不可用**（超出 OS 命令行限制） | **不可用**（`spawnSync` 同样超限） | **必须使用** |
| `get_file_link` / `search_files` 等 | 可以（参数短） | 可以 | 可以 |

---

## 临时文件管理

所有中间产物必须格式规范，使用 UTF-8 格式，写入基于当前 Agent **conversation ID**（对话标识）的独立临时目录，避免污染工作区或多会话并行干扰。

> ⚠️ 此处 conversation ID 是指 Agent 当前对话的唯一标识，**不是** `aippt.doc_create_session` 返回的 API `session_id`。获取方式见工作流文档步骤 0。**禁止**使用自定义名称、缩写或硬编码字符串。

### 目录规则

| 项目 | 说明 |
|------|------|
| 根目录 | 系统临时目录，即 `os.tmpdir()`（Windows: `%TEMP%`，macOS/Linux: `/tmp`） |
| 会话子目录 | `<系统临时目录>/kdocs_aippt_<conversation_id>/` |
| 命名示例 | `/tmp/kdocs_aippt_a1b2c3d4-e5f6-7890-abcd-ef1234567890/` |

### 中间文件约定

#### 主题生成 PPT

| 步骤 | 推荐文件路径 |
|------|-------------|
| Step 01 用户选择 | `$AIPPT_WORK_DIR/01_selections.json` |
| Step 02 研究结果 | `$AIPPT_WORK_DIR/02_research.json` |
| Step 03 大纲结果 | `$AIPPT_WORK_DIR/03_outline.json` |
| Step 04 转换结果 | `$AIPPT_WORK_DIR/04_config.json` |
| Step 05 PPT 结果 | `$AIPPT_WORK_DIR/05_ppt_result.json` |
| Step 06 云文档结果 | `$AIPPT_WORK_DIR/06_cloud_result.json` |

#### 文档生成 PPT

| 步骤 | 推荐文件路径 |
|------|-------------|
| Step 01 会话信息 | `$AIPPT_WORK_DIR/01_session.json` |
| Step 02 选项确认（含 checkpoint_id, interrupt_id） | `$AIPPT_WORK_DIR/02_options.json` |
| Step 03 大纲结果 | `$AIPPT_WORK_DIR/03_outline.md` + `$AIPPT_WORK_DIR/03_extra.json` |
| Step 04 美化结果 | `$AIPPT_WORK_DIR/04_beautify.json` |
| Step 05 本地格式转换结果 | `$AIPPT_WORK_DIR/05_config.json`（`{topic, outlines[]}` 结构） |
| Step 06 PPT 结果 | `$AIPPT_WORK_DIR/06_ppt_result.json` |
| Step 07 云文档结果 | `$AIPPT_WORK_DIR/07_cloud_result.json` |

### 清理方式

流程结束时递归删除整个会话目录：

```javascript
const fs = require('fs');
fs.rmSync(sessionDir, { recursive: true, force: true });
```

```python
import shutil
shutil.rmtree(session_dir, ignore_errors=True)
```

```bash
# Linux / macOS
rm -rf "${TMPDIR}/aippt_${SESSION_ID}"

# Windows PowerShell
Remove-Item -Recurse -Force "$env:TEMP\aippt_${SESSION_ID}"
```

> 清理操作应放在 `try...finally` 中执行，无论流程成功或失败都必须尝试清理。

### JSON 格式约束

中间 JSON 文件必须通过编程语言的标准 JSON 序列化函数生成（**禁止手动拼接**）：

```javascript
// ✅ 正确
fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
// 写入后验证
JSON.parse(fs.readFileSync(filePath, 'utf-8'));
```

```python
# ✅ 正确
import json
with open(file_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

编码要求：UTF-8 无 BOM，不要在 JSON 前后添加非 JSON 内容。

---

---

## 一、主题生成 PPT API

### 1. aippt.theme_questions

#### 功能说明

根据用户输入的 PPT 主题或需求描述，生成一组可继续追问用户偏好的问卷题目。

**适用于**：用户只给了一个较宽泛的主题，还需要澄清受众、场景、风格、内容重点等信息时。

- 服务端会固定以 `stream=true` 调用上游接口，但最终工具返回为一次性 JSON 结果
- 建议将返回的问卷继续转成 `question_and_answers`，供 `aippt.theme_deep_research` 与 `aippt.theme_outline` 使用


#### 调用示例

生成儿童科普主题问卷：

```json
{
  "input": "帮我做一份长颈鹿主题的儿童科普 PPT，用于小学课堂讲解"
}
```


#### 参数说明

- `input` (string, 必填): 用户输入的 PPT 主题、目标或需求描述

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "input": "帮我做一份长颈鹿主题的儿童科普 PPT",
    "questionnaire": [
      {
        "key": "properties1",
        "title": "这份长颈鹿主题的PPT主要用于什么场景？",
        "type": "radio",
        "enum": ["A", "B", "C", "D"],
        "enumNames": ["儿童科普教学", "幼儿园活动展示", "生日派对主题分享", "文创产品提案"],
        "required": false,
        "default_answer": ["儿童科普教学"]
      },
      {
        "key": "properties4",
        "title": "如果目标受众是低龄儿童，您是否希望在PPT大纲中规划互动环节模块？",
        "type": "input",
        "required": false,
        "default_answer": "是"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `message` | string | 成功时通常为“成功” |
| `data.input` | string | 原始主题描述 |
| `data.questionnaire` | array | 生成的问卷列表 |
| `data.questionnaire[].key` | string | 问题唯一键 |
| `data.questionnaire[].title` | string | 问题标题 |
| `data.questionnaire[].type` | string | 题型，如 `radio` / `checkbox` / `input` |
| `data.questionnaire[].enum` | array[string] | 选项编码列表，题型为选择题时可能返回 |
| `data.questionnaire[].enumNames` | array[string] | 选项文案列表，顺序与 `enum` 对齐 |
| `data.questionnaire[].required` | boolean | 是否必答 |
| `data.questionnaire[].default_answer` | any | 默认答案，可能为字符串或字符串数组 |

> 如果主题已经足够明确、无需继续澄清，可跳过本工具，直接组织 `question_and_answers`
---

### 2. aippt.theme_deep_research

#### 功能说明

根据用户主题和补充问答执行 AI PPT 联网研究，提炼研究目标完成情况与研究资料。

**适用于**：需要先补充事实资料、案例、背景知识，再继续生成 PPT 大纲时。

- 服务端固定以 `stream=true` 调用上游接口
- 最终工具结果只返回完成摘要，不直接返回完整研究资料文本
- 若调用端传入 MCP `_meta.progressToken`，服务会通过 `notifications/progress` 回传进度
- 若同时传入 `_meta.partialResults=true`，`notifications/progress` 中会追加逐段 partial result chunk
- 服务端还会兼容透传 `notifications/aippt/deep_research` 结构化事件


#### 调用示例

对儿童科普主题做研究：

```json
{
  "input": "帮我做一份长颈鹿主题的儿童科普 PPT",
  "question_and_answers": [
    {
      "question": "这份 PPT 主要用于什么场景？",
      "answer": "小学科学课课堂讲解"
    },
    {
      "question": "希望突出哪些内容模块？",
      "answer": "外形特征、生活习性、趣味冷知识"
    }
  ]
}
```


#### 参数说明

- `input` (string, 必填): 用户输入的 PPT 主题或需求描述
- `question_and_answers` (array[object], 必填): 问答列表，不能为空。每项含 `question`（string，必填）与 `answer`（string，必填）。


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "streamed": true,
    "done": true,
    "goal_count": 3,
    "goals_done": 3,
    "learning_count": 6
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `message` | string | 成功时通常为“成功” |
| `data.streamed` | boolean | 固定为 true，表示研究过程通过流式事件执行 |
| `data.done` | boolean | 是否已完成 |
| `data.goal_count` | integer | 研究目标总数 |
| `data.goals_done` | integer | 已完成的研究目标数 |
| `data.learning_count` | integer | 已提取的研究资料条数 |

> 若后续要调用 `aippt.theme_outline`，应从流式通知中消费研究资料文本，并将其作为 `references` 传入
> 最终 tool result 不包含完整 `references`，不要仅依赖最终返回体获取研究内容
---

### 3. aippt.theme_outline

#### 功能说明

根据主题描述、补充问答以及研究资料，生成用于 AI PPT 的结构化大纲结果。

**适用于**：已经明确主题方向，并且希望先拿到可审阅的大纲，再决定是否继续生成 HTML PPTX。

- 服务端会固定以 `stream=true` 调用上游 `image_to_slide/outline` 接口
- `references` 建议直接传入 `aippt.theme_deep_research` 流式阶段产出的研究资料文本
- `question_and_answers` 不能为空，否则服务端会直接报参数错误


#### 调用示例

生成儿童科普主题大纲：

```json
{
  "input": "帮我做一份长颈鹿主题的儿童科普 PPT",
  "question_and_answers": [
    {
      "question": "这份 PPT 主要用于什么场景？",
      "answer": "小学科学课课堂讲解"
    },
    {
      "question": "希望整体风格更偏向哪种？",
      "answer": "插画风、适合儿童"
    }
  ],
  "references": "长颈鹿是现存最高的陆生动物，舌头很长，常以树叶为食。"
}
```


#### 参数说明

- `input` (string, 必填): 用户输入的 PPT 主题或需求描述
- `question_and_answers` (array[object], 必填): 问答列表，不能为空。每项含 `question`（string，必填）与 `answer`（string，必填）。

- `references` (string, 可选): 研究资料文本，建议直接传入 `aippt.theme_deep_research` 产出的研究内容

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "input": "帮我做一份长颈鹿主题的儿童科普 PPT",
    "question_and_answers": [
      {
        "question": "这份 PPT 主要用于什么场景？",
        "answer": "小学科学课课堂讲解"
      }
    ],
    "references": "长颈鹿是现存最高的陆生动物，主要生活在非洲稀树草原。",
    "outline": {
      "type": "outline",
      "title": "长颈鹿主题演示",
      "slides": [
        { "title": "封面" },
        { "title": "习性介绍" }
      ]
    }
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `message` | string | 成功时通常为“成功” |
| `data.input` | string | 原始主题描述 |
| `data.question_and_answers` | array | 原样回传的问答列表 |
| `data.references` | string | 原样回传的研究资料文本 |
| `data.outline` | object | 上游返回的结构化大纲对象；字段会随模板与场景变化 |

> outline 的具体内部结构由上游模型决定，后续若要生成 HTML PPTX，建议优先从其中提取正式的 outlines 数组再传给 aippt.theme_generate_html_pptx
---

### 4. aippt.theme_generate_html_pptx

#### 功能说明

根据主题与 `outlines` 调用 structppt 接口，生成逐页 HTML PPTX，并返回合并后的演示文件地址。

**适用于**：已经拿到稳定的大纲结构，希望进一步生成可下载的演示文稿结果。

- 服务端固定使用 `json2ppt-banana` 场景
- `outlines` 只做“非空对象数组”校验，推荐直接传入上游生成的标准大纲数组
- 返回值同时包含逐页结果和合并后的完整 PPTX 链接


#### 调用示例

生成儿童科普主题 HTML PPTX：

```json
{
  "topic": "长颈鹿主题演示",
  "outlines": [
    {
      "title": "封面",
      "type": "cover"
    },
    {
      "title": "长颈鹿的生活习性",
      "type": "content"
    },
    {
      "title": "探索永无止境",
      "type": "ending"
    }
  ]
}
```


#### 参数说明

- `topic` (string, 必填): 演示文稿标题
- `outlines` (array[object], 必填): PPT 大纲数组，建议直接传入标准 outlines 结果。每项为 object，至少需为非空对象。


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "topic": "长颈鹿主题演示",
    "merged_url": "https://meihua-service.ks3-cn-beijing.ksyuncs.com/file/20260401/pptx/b74af503-ef35-445f-8106-2c1deac0dcb3.pptx?Expires=1775027041&AWSAccessKeyId=xxx&Signature=xxx",
    "total_pages": 4,
    "pages": [
      {
        "slide_index": 3,
        "file_url": "https://meihua-service.ks3-cn-beijing.ksyuncs.com/temp/20260401/pptx/3097fecf-bf39-454a-92eb-700b49e0e773.pptx?Expires=1775199540&AWSAccessKeyId=xxx&Signature=xxx",
        "title": "探索永无止境",
        "type": "ending"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `message` | string | 成功时通常为“成功” |
| `data.topic` | string | 演示文稿标题 |
| `data.merged_url` | string | 合并后的完整 PPTX 下载地址 |
| `data.total_pages` | integer | 总页数 |
| `data.pages` | array | 逐页生成结果 |
| `data.pages[].slide_index` | integer | 幻灯片序号 |
| `data.pages[].file_url` | string | 单页 PPTX 文件地址 |
| `data.pages[].title` | string | 对应大纲标题 |
| `data.pages[].type` | string | 对应大纲类型，如 `cover` / `content` / `ending` |

> 返回的 `merged_url` 和 `pages[].file_url` 一般为临时链接，调用后应尽快消费
---

## 二、文档生成 PPT API

### 5. aippt.doc_create_session

#### 功能说明

为“文档生成 PPT”链路创建服务端 AI 会话，返回后续 `aippt.doc_outline_options` / `aippt.doc_outline` 需要使用的 `session_id`。

**适用于**：已经确定要基于某份文档生成 PPT，准备进入文档解析和大纲生成流程时。


#### 调用示例

创建文档生成会话：

```json
{}
```


#### 参数说明


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | number | 0 表示成功 |
| `message` | string | 成功时通常为“成功” |
| `data.session_id` | string | 文档生成链路会话 ID |

---

### 6. aippt.doc_outline_options

#### 功能说明

基于文档引用和会话 ID 调用文档 Agent，对文档做初步解析，并返回一组需要与用户确认的意图问题（questions）。

**适用于**：用户已经给出文档，但还需要补充“制作目标 / 受众 / 重点”等选项时。


#### 调用示例

获取文档大纲选项：

```json
{
  "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5",
  "input": [
    {
      "type": "text",
      "content": "生成PPT"
    },
    {
      "type": "file_id",
      "content": "100239253236"
    }
  ]
}
```


#### 参数说明

- `session_id` (string, 必填): AI 会话 ID，来自 `aippt.doc_create_session`
- `input` (array[object], 必填): 输入内容数组。通常包含一条 `{type:"text", content:"生成PPT"}` 和一条文档引用（如 `{type:"file_id", content:"100239253236"}`）。


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5",
    "checkpoint_id": "419e8c77-5442-459e-87eb-2637ba53e132",
    "interrupt_id": "45caf5dc-2dd4-48a7-9ba3-8ba2edc67cdd",
    "user_input": "生成PPT",
    "questions": [
      {
        "type": "choice",
        "field": "制作目标",
        "label": "制作目标",
        "options": ["内部技术培训宣讲", "新功能发布介绍"]
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.session_id` | string | 当前 AI 会话 ID |
| `data.checkpoint_id` | string | 继续生成完整大纲时需要的 checkpoint |
| `data.interrupt_id` | string | follow_up 中断 ID |
| `data.user_input` | string | 从 input 中提取的文本输入摘要 |
| `data.questions` | array | 需要向用户确认的问题列表 |
| `data.assistant_messages` | array[string] | 过程中的可见提示文案，可能为空 |

> 拿到 `questions` 后，应先与用户交互收集选择，再整理成 `resume_info`
---

### 7. aippt.doc_outline

#### 功能说明

基于 `session_id`、`checkpoint_id`、原始文档输入和 `resume_info`，继续文档 Agent 流程，生成完整 Markdown 大纲。

**适用于**：用户已经完成大纲选项确认，需要拿到可继续做风格美化的正式大纲时。


#### 调用示例

生成文档完整大纲：

```json
{
  "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5",
  "checkpoint_id": "419e8c77-5442-459e-87eb-2637ba53e132",
  "input": "[与 `aippt.doc_outline_options` 保持一致的输入数组]",
  "resume_info": "[根据 questions 和 interrupt_id 整理得到的 follow_up 数组]"
}
```


#### 参数说明

- `session_id` (string, 必填): AI 会话 ID
- `checkpoint_id` (string, 必填): 检查点 ID，来自 `aippt.doc_outline_options`
- `input` (array[object], 必填): 与获取大纲选项时一致的输入内容数组
- `resume_info` (array[object], 必填): 恢复信息数组，通常包含 `follow_up` 类型对象及用户选择结果。


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "session_id": "9dbea4d8-b9f7-419c-a4ad-208d4515b8d5",
    "checkpoint_id": "419e8c77-5442-459e-87eb-2637ba53e132",
    "user_input": "生成PPT",
    "user_intention": {
      "items": [
        {
          "field": "制作目标",
          "options": ["内部技术培训宣讲"]
        }
      ]
    },
    "markdown_outline": "# 示例主题 {.topic}\n\n## 封面 {.title}\n- 副标题"
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.session_id` | string | 当前 AI 会话 ID |
| `data.checkpoint_id` | string | 本次流程对应 checkpoint |
| `data.user_input` | string | 从 input 中提取的文本输入摘要 |
| `data.user_intention` | object | 规范化后的用户意图对象，可直接传给 `aippt.doc_beautify` |
| `data.markdown_outline` | string | 完整 Markdown 大纲 |
| `data.assistant_messages` | array[string] | 过程中的可见提示文案，可能为空 |

---

### 8. aippt.doc_beautify

#### 功能说明

根据完整 Markdown 大纲和用户意图，生成全局风格和逐页排版设计描述。

**适用于**：已经拿到正式大纲，准备进入最终 PPT 渲染前的风格美化阶段。


#### 调用示例

生成文档大纲风格：

```json
{
  "topic": "航空业碳中和监管与合规应对",
  "outline": "# 航空业碳中和监管与合规应对 {.topic}\n\n## 封面 {.title}\n- 汇报主题",
  "user_intention": "{items:[...]}"
}
```


#### 参数说明

- `topic` (string, 必填): 演示文稿主题
- `outline` (string, 必填): 完整 Markdown 大纲
- `user_intention` (object, 必填): 用户意图对象，建议直接传入 `aippt.doc_outline` 返回的 `user_intention`
- `user_input` (string, 可选): 用户原始输入文本；已知时建议传入
- `model` (string, 可选): 风格模型，默认 `IMAGE_V2`

#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "topic": "航空业碳中和监管与合规应对",
    "theme": "航空业碳中和监管与合规应对",
    "global_style": "全局风格描述",
    "slides": [
      {
        "index": 0,
        "page_type": "title",
        "design_style": "封面页风格描述"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.topic` | string | 演示主题 |
| `data.theme` | string | 上游生成的主题名 |
| `data.global_style` | string | 全局设计风格说明 |
| `data.slides` | array | 逐页风格数组 |
| `data.slides[].index` | integer | 页序号（从 0 开始） |
| `data.slides[].design_style` | string | 对应页面的风格描述 |

---

### 9. aippt.doc_generate_ppt

#### 功能说明

根据主题与 `outlines` 调用 structppt 接口，生成逐页 HTML PPTX，并返回合并后的演示文件地址。

**适用于**：已经拿到稳定的大纲结构，希望进一步生成可下载的演示文稿结果。


#### 调用示例

生成文档 PPT：

```json
{
  "topic": "航空业碳中和监管与合规应对",
  "outlines": [
    {
      "type": "title",
      "title": "封面",
      "page_type": "pt_title",
      "contents": "",
      "design_style": "封面页风格描述"
    }
  ]
}
```


#### 参数说明

- `topic` (string, 必填): 演示文稿主题
- `outlines` (array[object], 必填): PPT 大纲数组，建议直接传入标准 outlines 结果。每项为 object，至少需为非空对象。


#### 返回值说明

```json
{
  "code": 0,
  "message": "成功",
  "data": {
    "topic": "航空业碳中和监管与合规应对",
    "config": {
      "topic": "航空业碳中和监管与合规应对",
      "outlines": [
        {
          "type": "title",
          "title": "封面",
          "page_type": "pt_title",
          "contents": "",
          "design_style": "封面页风格描述"
        }
      ]
    },
    "merged_url": "https://example.com/final.pptx",
    "total_pages": 12,
    "pages": [
      {
        "slide_index": 0,
        "file_url": "https://example.com/0.pptx",
        "title": "封面",
        "type": "title"
      }
    ]
  }
}

```

| 字段 | 类型 | 说明 |
|------|------|------|
| `data.config` | object | 透传的标准配置对象（topic + outlines） |
| `data.config.outlines[]` | array | 传给 structppt 的标准页面数组 |
| `data.merged_url` | string | 合并后的完整 PPT 地址 |
| `data.total_pages` | integer | 总页数 |
| `data.pages` | array | 逐页生成结果 |

---


## 工具速查表

| # | 工具名 | 分类 | 功能 | 必填参数 |
|---|--------|------|------|----------|
| 1 | `aippt.theme_questions` | 主题生成 PPT API | 根据主题描述生成补充问卷 | `input` |
| 2 | `aippt.doc_create_session` | 文档生成 PPT API | 创建文档转 PPT 的 AI 会话 |  |
| 3 | `aippt.doc_outline_options` | 文档生成 PPT API | 解析文档并返回大纲选项问题 | `session_id`, `input` |
| 4 | `aippt.theme_deep_research` | 主题生成 PPT API | 围绕主题与问答执行联网深度研究 | `input`, `question_and_answers` |
| 5 | `aippt.theme_outline` | 主题生成 PPT API | 根据主题、问答和资料生成 PPT 大纲 | `input`, `question_and_answers` |
| 6 | `aippt.doc_outline` | 文档生成 PPT API | 生成完整 Markdown 大纲 | `session_id`, `checkpoint_id`, `input`, `resume_info` |
| 7 | `aippt.theme_generate_html_pptx` | 主题生成 PPT API | 根据主题与大纲生成 HTML PPTX | `topic`, `outlines` |
| 8 | `aippt.doc_beautify` | 文档生成 PPT API | 为 Markdown 大纲生成整套风格描述 | `topic`, `outline`, `user_intention` |
| 9 | `aippt.doc_generate_ppt` | 文档生成 PPT API | 根据主题与大纲生成最终 PPT | `topic`, `outlines` |
