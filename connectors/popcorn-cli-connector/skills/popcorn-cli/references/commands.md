# 秒针爆米花 CLI 0.3.0 命令参考

本参考使用 npm 正式包 `@baomihuatop/popcorn-cli@0.3.0`，认证和业务服务均为 `https://baomihua.top`。调用前按 Skill 指引核对生产地址与 OAuth；实际权限和计费以生产服务为准。旧包返回 BUSINESS_OAUTH_NOT_READY 时核对实际 CLI 路径与版本，不绑定 Key 或绕过 CLI。

## 五、命令详情

### 5.1 查询模型

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image models
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image models --detail <MODEL_ID>
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video models
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video models --detail <MODEL_ID>
```

返回结构（`models`）：

```jsonc
{
  "type": "image",
  "total": 2,
  "models": [
    {
      "model_id": "...",          // 模型唯一标识，submit 时用
      "name": "...",              // 展示名
      "description": "...",       // 简介
      "model_limit": { },         // 单模型使用限制（时长、分辨率等）
      "price_config": { },        // 计费配置
      "has_model_usage_guidance": true
    }
  ],
  "model_usage_guidance": "...",  // 公共调用建议
  "params_schema": { }            // 该场景 submit --params 的字段结构（JSON Schema 风格）
}
```

`--detail` 返回单模型的完整信息，含 **完整入参规范** 与 **调用建议**。构造 `--params` 前应先读它。

### 5.2 提交任务

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli <image|video> submit -n <NAME> -d <DESCRIPTION> -p <JSON> [-s <SESSION_ID>] [-f <FOLDER_ID>]
```

| 参数 | 缩写 | 必填 | 说明 |
|---|---|---|---|
| `--name` | `-n` | **是** | 产物名称，便于后续检索复用 |
| `--description` | `-d` | **是** | 产物描述，说明内容与用途 |
| `--params` | `-p` | **是** | 任务参数，**必须是 JSON 对象字符串**（建议用单引号包裹） |
| `--sid` | `-s` | 否 | 会话 ID，把同一业务上下文的任务关联起来 |
| `--folder-id` | `-f` | 否 | 归属目录 ID，**仅支持 `cli_generate` 目录**；不传则归入默认（未归类） |

示例：

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli image submit -n "陈渊-正面半身" -d "《吞天葫芦》主角参考图，纯色背景" \
  -p '{"model":"<MODEL_ID>","prompt":"...","aspect_ratio":"3:4"}' -s "tuntianhulu-ep01"

POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli video submit -n "S01-01" -d "第1场第1镜，镜头缓慢推进" \
  -p '{"model":"<MODEL_ID>","prompt":"画面动作及相符环境声，原有对白按剧本","duration":4,"generate_audio":true}' -s "tuntianhulu-ep01" -f 12
```

视频示例适用于详情已确认支持布尔 generate_audio 的模型；该字段默认显式 true。其他模型先核对音频能力与真实字段，不能硬套参数或静默改为无声。用户明确要求静音才设 false 并记录原因；字幕与音频独立处理。实际产物需要检查音轨并回听。

返回（**受理成功，任务已入队，不含结果**）：

```jsonc
{
  "task_id": "...",        // 用于 task list --tid
  "session_id": "...",     // 未传则为 null
  "task_type": "image",    // image / video
  "folder_id": 12,         // 未指定则为 null
  "created_at": "..."
}
```

> **`submit` 是异步接口。** 返回里**没有**生成结果。必须用 `task list` 轮询到终态后再读 `result`。

### 5.3 查询任务

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli task list -t <TASK_ID>       # 单个任务（推荐用于轮询）
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli task list -s <SESSION_ID>    # 整个会话下的全部任务
```

`-s` 与 `-t` 必须提供其一。

```jsonc
{
  "total": 1,
  "tasks": [
    {
      "task_id": "...",
      "session_id": "...",
      "task_type": "image",
      "created_at": "...",
      "finished_at": "...",
      "status": "succeed",        // queued / running / succeed / failed
      "result": "...",            // 成功时的资源地址（URL）；未完成或失败时可能为空
      "error_message": ""         // 失败原因；成功时通常为空
    }
  ]
}
```

**`result` 通常是远程 URL**，需下载到本地项目目录后再回填路径；不要把带鉴权的临时 URL 直接当作交付物给用户。

### 5.4 上传与检索素材

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli resource upload <FILE> -n <NAME> -d <DESCRIPTION> [-f <FOLDER_ID>]
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli resource list [-n <KEYWORD>] [--created-from <DATETIME>] [--created-to <DATETIME>] [--page <N>] [--page-size <N>]
```

| 参数 | 缩写 | 必填 | 说明 |
|---|---|---|---|
| `<file>` | - | **是** | 本地文件路径（位置参数） |
| `--name` | `-n` | **是** | 资源名称 |
| `--description` | `-d` | **是** | 资源描述 |
| `--folder-id` | `-f` | 否 | 归属目录，**仅支持 `cli_upload`（上传资源）目录** |

- **资源类型（图片 / 视频 / 音频）不由命令行指定**，由后端按文件推断。
- `resource list` 支持 `--name` 模糊搜索、`--created-from` / `--created-to` 时间范围、`--page` / `--page-size` 分页（默认 1 / 20，最大 100）。
- 上传成功后记录返回的资源标识，写回项目 `assets.json`，后续复用优先用标识而不是重复上传。

### 5.5 文件夹管理

```bash
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli folder list -t <TYPE>
POPCORN_REQUIRED_AUTH_METHOD=oauth POPCORN_OAUTH_CLIENT_ID=popcorn-workbuddy popcorn-cli folder create -n <NAME> -t <TYPE> [-p <PARENT_ID>]
```

两类目录是**独立业务域、互不影响**：

| 对用户说法 | 命令参数 `--type` | 用途 |
|---|---|---|
| AI 生成产物 | `cli_generate` | 归档生图 / 生视频结果；`image/video submit -f` **只能挂这类** |
| 上传资源 | `cli_upload` | 整理上传的参考图、素材；`resource upload -f` **只能挂这类** |

约束：

- `folder list` 返回**扁平列表**，用 `id` / `parent_id` 自行组树；建子目录前先 `folder list` 拿父目录 `id`。
- `parent_id` 必须存在，且与新目录同类型、同用户。
- `--folder-id` 必须是正整数（不能为 0）。
