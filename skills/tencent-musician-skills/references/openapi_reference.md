# TME OpenAPI 算子通用调用（内部基础能力）

> 本文档说明 `tencent-musician-skills` Skill 中**宣推业务层**对腾讯音乐开放平台「算子」体系的通用调用规范。
>
> 算子平台是一套**动态发现 + 同步调用**的后端 API 体系：每个「算子」对应一个后端能力，配置（名称、入参、出参）存在数据库里可随时增改，因此业务层 **不得硬编码**任何 `operatorCode` 或参数结构，一律通过下方 4 个通用工具**动态发现和调用**。
>
> **数据分析业务**（`data-analysis/entry.md`）**不走算子流程**，而是走固定的 `chat-sync` 接口。只有宣推业务（`promotion/entry.md`）走本文档的算子流程。

## 接口概览

本 Skill 封装了算子平台对外的 4 个标准入口：

```
POST /musician/agent/operator/listApis       → list_apis
POST /musician/agent/operator/searchApis     → search_apis
POST /musician/agent/operator/getApiDetail   → get_api_detail
POST /musician/agent/operator/invokeApi      → invoke_api
```

所有接口：
- 域名：`https://y.tencentmusic.com/openapi`（正式环境，已硬编码）
- 方法：POST + JSON Body
- 鉴权：HTTP Header `tme-header-token: <token>`（Skill 内部自动获取，见 `references/auth.md`）
- 响应：统一 `{ success, data, error, meta }` 结构
- **调用方式：同步**——`invoke_api` 直接返回最终结果，无需轮询

## 可用 Tools

| Tool             | 作用                   | 什么时候用                                 |
| ---------------- | ---------------------- | ------------------------------------------ |
| `list_apis`      | 列出所有可用算子摘要   | 想看全貌，或不确定该搜什么关键词           |
| `search_apis`    | 按关键词模糊搜索算子   | 知道大概要什么能力（如"宣推概览"、"发行"） |
| `get_api_detail` | 获取指定算子的完整详情 | 需要精确了解参数结构再调用                 |
| `invoke_api`     | 调用指定算子           | 参数已准备好，可以执行了                   |

## 脚本一览

| Tool             | 脚本                        | 命令行用法                                                       |
| ---------------- | --------------------------- | ---------------------------------------------------------------- |
| `list_apis`      | `scripts/list_apis.py`      | `python scripts/list_apis.py`                                    |
| `search_apis`    | `scripts/search_apis.py`    | `python scripts/search_apis.py <keyword>`                        |
| `get_api_detail` | `scripts/get_api_detail.py` | `python scripts/get_api_detail.py <operatorCode>`                |
| `invoke_api`     | `scripts/invoke_api.py`     | `python scripts/invoke_api.py <operatorCode> '<arguments_json>'` |

> 这 4 个脚本仅用 Python 3 标准库（`urllib` / `json`），零额外依赖。Token 由内部模块 `_token.py` 自动管理，调用方**无需**传任何参数或设置任何环境变量。

## 标准调用流程

```
1. 发现算子
   search_apis({ keyword: "..." })  或  list_apis()
        ↓
2. 判断：search/list 返回的摘要信息够不够组装参数？
   ├── 够了 → 直接到第 3 步
   └── 不够 → get_api_detail({ name: "<operatorCode>" })
        ↓
3. 调用算子（同步）
   invoke_api({ name: "<operatorCode>", arguments: { ... } })
        ↓
4. 直接读取 output，完成
```

> 当前算子平台**仅支持同步调用**，`invoke_api` 一次请求即可拿到最终结果。

### 关于 `detailedDescription` 字段

`get_api_detail` 返回的详情中包含一个 `detailedDescription` 字段（Markdown 格式的长文本），是算子作者为该能力撰写的**详细使用说明**，通常包含：

- 该算子具体是什么、适用场景
- 参数的详细含义、约束和取值范围
- 调用注意事项和最佳实践
- 常见错误和处理建议

> **⚠️ 强烈建议**：在首次调用一个不熟悉的算子之前，先通过 `get_api_detail` 获取详情，**仔细阅读 `detailedDescription` 字段的内容**，再组装参数发起调用。这能大幅减少因参数错误导致的调用失败。

### 判断是否需要查 detail 的经验法则

**可以跳过 detail 直接 invoke** — 当以下三个条件同时满足：

1. `search/list` 返回的 `inputSchema` 信息齐全，所有 `required` 参数你都能确定值
2. 参数结构是扁平的（没有嵌套的 object/array），或者嵌套结构你已完全理解
3. 对参数含义没有任何歧义

**必须先查 detail** — 当以下任一条件成立：

1. `inputSchema` 有嵌套 object 或 array，你不确定内部结构
2. 对某个参数的含义、格式、取值范围有疑问
3. 想参考 `exampleInput` / `exampleOutput` 来确认参数怎么组装
4. 想查看 `detailedDescription` 获取该算子的详细使用指南

## 参数构造规则

- `arguments` 必须是结构化 JSON 对象（`Map<String, Object>`），严格匹配 `inputSchema`
- 所有 `required` 字段必须提供，少一个都会返回 `INVALID_ARGUMENT`
- 参数类型必须匹配 schema 声明的 type（`string` / `number` / `boolean` / `object` / `array`）
- 可选参数不确定就不传，后端会用默认值
- 登录态下**不要**传 `accountId` / `userId` 等当前用户身份参数，后端会从 Token 中自动识别
- **禁止**把自然语言拼接成字符串塞到 `arguments` 里

## 错误处理

所有响应外层结构为 `{ success, data, error, meta }`。当 `success=false` 时，读 `error` 字段：

| error.code         | 含义         | 能重试吗 | 怎么办                                                               |
| ------------------ | ------------ | -------- | -------------------------------------------------------------------- |
| `INVALID_ARGUMENT` | 参数错误     | 否       | 调 `get_api_detail` 重新确认 schema，修正参数再试                    |
| `NOT_FOUND`        | 算子不存在   | 否       | 调 `search_apis` 重新确认 `operatorCode`                             |
| `UNAUTHORIZED`     | 未认证       | 否       | 删除 `~/.tme-login/token.json` 后重跑脚本，本 Skill 会自动触发重新登录 |
| `RATE_LIMITED`     | 限流         | 是       | 等一会儿再试                                                         |
| `TIMEOUT`          | 超时         | 是       | 重试，可设更大 `timeoutMs`                                           |
| `UPSTREAM_ERROR`   | 上游服务异常 | 是       | 重试 1-2 次，仍失败则交给上层业务流程处理                             |

> 所有算子当前都是**同步返回**，`invoke_api` 的响应即为最终结果，无 `async=true` 的情况。

**关键策略**：遇到 `INVALID_ARGUMENT` 时，别用同样的参数重试——回退到 `get_api_detail` 查完整 schema 和 example，重新组装参数。

## 典型调用示例

### 示例 1：发现 + 调用算子（自动处理登录态）

```bash
# 首次会弹出 Chromium 让你扫码；之后 30 天内秒级复用
python scripts/search_apis.py 宣推概览
python scripts/invoke_api.py 宣推概览 '{"accountId":282250}'
```

### 示例 2：对参数有疑问时先查 detail

```bash
python scripts/get_api_detail.py <operatorCode>
# 查看 detailedDescription / inputSchema / exampleInput / exampleOutput
# 然后再组装 arguments 调用 invoke_api
```

### 示例 3：主动刷新登录态（Token 过期）

```bash
rm -f ~/.tme-login/token.json ~/.tme-login/storage_state.json
python scripts/login.py     # 有头扫码，重新登录
# 之后直接跑任意算子调用即可
```
