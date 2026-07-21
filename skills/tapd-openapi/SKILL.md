---
name: tapd-openapi
version: 1.0.3
description: "TAPD OpenAPI skill，用于需求、缺陷、任务、迭代、Wiki、评论、工时、附件等 TAPD 平台操作。当用户提到「TAPD」「需求」「story」「缺陷」「bug」「任务」「task」「迭代」「iteration」「sprint」「工时」「timesheet」「Wiki」「评论」「comment」「附件」或需要在 TAPD 中查询、创建、更新、统计相关内容时，使用此 skill。支持需求管理、缺陷管理、任务管理、迭代管理、Wiki 管理（含全文搜索）、评论管理、工时花费管理、附件管理及用户信息查询等功能。"
description_zh: "TAPD 项目管理平台操作（需求、缺陷、任务、迭代、Wiki）"
description_en: "TAPD project management (stories, bugs, tasks, iterations, wiki)"
allowed-tools: Bash,Read,Glob,Grep
display_name: "tapd-openapi"
display_name_en: "tapd-openapi"
visibility: "public"
---

# TAPD OpenAPI

## 环境变量（已预置）

- `TAPD_API_ENDPOINT` - API 地址, 如果 `TAPD_API_ENDPOINT` 已配置，则优先使用 `TAPD_API_ENDPOINT` 的替换文档中的 `${TAPD_API_ENDPOINT}`
- `TAPD_WORKSPACE_IDS` - 项目 ID 列表，逗号分隔，**优先级高于** `TAPD_WORKSPACE_ID`
- `TAPD_WORKSPACE_ID` - 单个项目 ID（兼容旧配置）
- `TAPD_TOKEN` - 认证 Token（Bearer 方式）

## Workspace 处理规则

**调用前必须先确定实际使用的 workspace 列表：**

```bash
# 优先取 TAPD_WORKSPACE_IDS，回退到 TAPD_WORKSPACE_ID
if [ -n "$TAPD_WORKSPACE_IDS" ]; then
  WS_LIST=$(echo "$TAPD_WORKSPACE_IDS" | tr ',' ' ')
else
  WS_LIST="$TAPD_WORKSPACE_ID"
fi
```

- 若 `WS_LIST` 只有一个 ID，按单 workspace 正常请求即可
- 若有多个 ID，需对每个 ID 分别调用 API，再汇总结果（求和、合并列表等，根据用户意图决定）
- 注意 curl 的时候 workspace_id 用逗号分隔后的，例如 $TAPD_WORKSPACE_IDS 是 "31372104,68119668"，则 curl 的时候需要分别调用 `workspace_id=31372104` 和 `workspace_id=68119668`

## 请求模板

```bash
# GET
curl -s -H "Authorization: Bearer $TAPD_TOKEN" \
  "${TAPD_API_ENDPOINT}/${path}?workspace_id=${ws_id}"

# POST
curl -s -X POST -H "Authorization: Bearer $TAPD_TOKEN" \
  -H "Content-Type: application/json" \
  "${TAPD_API_ENDPOINT}/${path}" \
  -d '{"workspace_id":"'"${ws_id}"'","key":"value"}'
```

## 查询 API 文档

API 文档位于 `~/.codebuddy/skills/tapd-openapi/references/` 目录。

**1. 列出所有服务**：
```bash
ls ~/.codebuddy/skills/tapd-openapi/references/
```

**2. 列出服务下的 API**：
```bash
ls ~/.codebuddy/skills/tapd-openapi/references/stories/
```

**3. 查看 API 详情**：
```bash
cat ~/.codebuddy/skills/tapd-openapi/references/stories/liststories.md
```

## 常用服务

| 服务 | 说明 | 常用 API 文件 |
|------|------|---------------|
| stories | 需求管理 | liststories, countstories, addstory, updatestory, getrelatedbugs, getstoryfieldsinfo |
| bugs | 缺陷管理 | listbugs, countbugs, addbug, updatebug, getbugfieldsinfo |
| iterations | 迭代管理 | listiterations |
| tasks | 任务管理 | listtasks, counttasks, addtask, updatetask |
| comments | 评论管理 | listcomments, countcomments, addcomment |
| wikis | Wiki 管理 | listwikis, countwikis, addwiki, updatewiki, **searchwiki**（见下方） |
| timesheets | 工时花费 | listtimesheets, counttimesheets, addtimesheet, updatetimesheet |
| attachments | 附件管理 | listattachments, downloadattachment, getimage, downloaddocument |
| users | 用户信息 | getuserinfo, listworkspaces |

## 调用流程

1. **确定服务**：根据需求从常用服务中选择，或用 `ls` 查看全部
2. **查找 API**：用 `ls ~/.codebuddy/skills/tapd-openapi/references/{服务}/` 找到具体操作
3. **获取详情**：用 `cat` 读取 API 文档，获取请求方法、路径、参数
4. **执行请求**：按模板构造 curl 命令，`workspace_id` 必传

## Wiki 搜索

TAPD API 不支持 Wiki 全文搜索，通过本地脚本实现。详见：

```bash
cat ~/.codebuddy/skills/tapd-openapi/references/wikis/searchwiki.md
```
