---
name: cnb-skill
description: "Interact with CNB (Cloud Native Build) platform via OpenAPI. Manage organizations, repositories, issues, PRs, merge requests, pipelines, releases, artifacts, workspaces, members, and more. Use `cnb` CLI for CRUD operations. Trigger when user mentions CNB, 云原生构建, or needs to manage CNB resources like repos, issues, PRs, pipelines, releases, or artifact registries."
description_zh: "CNB 平台全功能操作（仓库、Issue、PR、流水线、制品库）"
description_en: "CNB platform operations (repos, issues, PRs, pipelines, artifacts)"
version: 1.0.0
homepage: https://cnb.cool
allowed-tools: Read,Bash
---

# cnb-skill

## 概括

本Skill提供完整的CNB的Openapi完整交互能力，用户可以使用此skills对CNB上的资源进行操作。

## 适用场景

当用户描述对CNB上的资源进行操作时，应该使用此skills进行操作。例如：
- 查询cnb上某个仓库的Issue列表
- 对cnb上的某个仓库的Issue或者pr进行评论。
- ...

## 核心原则

### 准确性原则
- **CRITICAL**: 必须先执行 `cnb --help` 获取最新的使用方式
- **CRITICAL**: 必须通过使用 `cnb`命令行工具，按照帮助信息执行操作
- **CRITICAL**: 禁止推测或臆断使用方式，严格基于脚本返回的帮助信息进行操作
- **CRITICAL**: 不要询问用户"是否需要我执行"，直接根据帮助信息执行脚本，并返回结果

## 脚本使用指南

### 第一步：获取帮助信息
在执行任何任务前，必须先运行以下命令获取最新的使用方式：

```bash
cnb --help
```

这将显示所有可用的模块及其工具列表。

### 第二步：查看具体模块帮助
使用 `--module` 参数查看特定模块的详细帮助：

```bash
cnb --module <模块名> -help
```

### 第三步：查看工具详细使用
使用 `--module` 和 `--tool` 参数查看工具的详细参数说明：

```bash
cnb --module <模块名> --tool <工具名> --help
```

### 第四步：执行工具
根据第三步获取的参数说明，执行工具：

```bash
cnb --module <模块名> --tool <工具名> --path '{"参数": "值"}' --query '{"参数": "值"}' --data '{"参数": "值"}'
```

**参数说明：**
- `--module`: 必须参数，模块名称
- `--tool`: 必须参数，工具名称
- `--path`: 可选参数，路径参数，JSON字符串格式
- `--query`: 可选参数，查询参数，JSON字符串格式
- `--data`: 可选参数，数据参数，JSON字符串格式
- `--help`: 可选参数，显示帮助文档

### 第五步：处理结果

每一个工具调用都会返回一个标准的JSON结构:
- status: 一个http状态码
- trace: 本次调用的traceID
- header: 本次调用的header
- data: 本次调用的openapi返回的实体内容

#### header说明
当请求列表时，会在header中包含以下字段说明列表的情况：
- `x-cnb-page`: 当前页数
- `x-cnb-page-size`: 每页条数
- `x-cnb-total`: 总条数

从中可以获取到列表的总条数，以及当前页数和每页条数，避免循环请求。

#### status说明
API 返回标准的 JSON 格式响应。请根据 HTTP 状态码判断请求是否成功：

- 200: 请求成功
- 400: 请求参数错误
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 500: 服务器内部错误

当本地调用返回的 `status` 在 200 ~ 299 之间，只需要返回 `data` 内容给用户。只有当 `status >= 300` 时，才将 `status` 和 `trace` 返回给用户。

#### 资源处理

当尝试下载图片进行图片分析时，遇到图片下载异常时，请使用以下工具进行图片下载！
  ```bash
  node scripts/core/index.js assets get-imgs --help
```