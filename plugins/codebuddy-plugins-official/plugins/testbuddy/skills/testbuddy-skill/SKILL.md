---
name: testbuddy-skill
description: 'TestBuddy 测试设计技能包。当用户想要：(1) 生成测试框架/模块/场景/测试点/用例；(2) 根据 TAPD 需求或缺陷链接生成测试内容；(3) 根据任意文本（PRD/接口文档/代码/表格/功能描述）生成测试用例；(4) 打开/跳转到脑图、测试设计、TestBuddy 页面；(5) 进行测试设计、需求分析、缺陷分析时，使用本技能。'
---

# Design Agent Skill 测试设计技能包

## 核心定位

本 skill 是一个**轻量级的意图识别和工作流调度器**。

核心职责：

1. 识别用户意图
2. 加载会话上下文
3. 路由到对应的工作流执行

**工作流负责**：

- 自己的执行清单规划
- 具体的执行逻辑（包括上下文补全、缺失数据处理等）
- 任务状态管理

## 工具能力清单

本 skill 及其工作流**只能使用以下工具**完成任务：

| 工具              | 文档路径                              | 能力说明                                                    |
| ----------------- | ------------------------------------- | ----------------------------------------------------------- |
| `get_session`     | `references/tools/get_session.md`     | 读取/写入会话上下文（token、design_uid、knowledge_uids 等） |
| `get_issue`       | `references/tools/get_issue.md`       | 通过 TAPD 链接或 workspace+issue_id 获取需求/缺陷详情       |
| `write_nodes`     | `references/tools/write_nodes.md`     | 对脑图节点进行新增、修改、删除操作                          |
| `search_nodes`    | `references/tools/search_nodes.md`    | 查询脑图节点详细信息（支持按 UID 查询或查询整个 design）    |
| `rag_search`      | `references/tools/rag_search.md`      | 知识库检索（脚本检索 + RAG_search 附件检索）                |
| `select_workflow` | `references/tools/select_workflow.md` | 根据意图关键词匹配工作流                                    |
| `select_rule`     | `references/tools/select_rule.md`     | 根据关键词匹配自定义规则                                    |
| `open_design`     | `references/tools/open_design.md`     | 打开 TestBuddy 测试设计页面                                 |

**⛔ 能力边界（严格遵守）**：

1. **禁止使用浏览器/网页获取内容**：不要尝试打开 TAPD、OA 或任何外部网页来爬取/获取需求内容
2. **获取需求/缺陷内容的正确途径**：通过 `get_issue` 工具获取 TAPD 需求/缺陷详情，或从 `get_session` 返回的会话数据中读取
3. 如果以上途径均无法获取所需信息，应**提示用户提供需求内容**（如粘贴文本、上传附件），而非自行去外部系统获取

## 执行流程【必须按步骤执行，严禁跳过任何步骤】

### ❗❗❗ 全局约束（所有步骤均适用）

**执行脚本时绝对禁止 `cd` 切换目录**：所有 Python 脚本必须在工作区根目录下执行，不要使用 `cd` 切换到任何其他目录。错误示例：`cd /path/to/skill && python3 scripts/xxx.py`，正确示例：`python3 /path/to/skill/scripts/xxx.py`。

### 步骤 1：识别用户意图

根据用户请求的关键词，识别用户想要执行的操作：

| 用户意图     | 触发关键词                                                                                                           | 意图关键词   |
| ------------ | -------------------------------------------------------------------------------------------------------------------- | ------------ |
| 生成测试框架 | `生成测试框架`、`生成框架`、`创建测试框架`                                                                           | `框架生成`   |
| 生成测试模块 | `生成测试模块`、`生成功能模块`、`识别测试模块`                                                                       | `模块生成`   |
| 生成测试场景 | `生成测试场景`、`生成场景`、`创建测试场景`                                                                           | `场景生成`   |
| 生成测试点   | `生成测试点`、`创建测试点`、`根据模块生成测试点`                                                                     | `测试点生成` |
| 生成测试用例 | `生成测试用例`、`生成用例`、`根据测试点生成用例`                                                                     | `用例生成`   |
| 生成测试设计 | `生成测试设计`、`帮我做测试设计`、`测试设计`                                                                         | `测试设计`   |
| 开启SPEC     | `生成 spec`、`开启spec工作流`、`spec`                                                                                | `SPEC`       |
| 打开网页     | `打开脑图`、`打开测试设计`、`打开 TestBuddy`、`打开 testbuddy`、`跳转到测试设计`、`打开测试设计页面`、`帮我打开脑图` | `打开网页`   |

### 步骤 2：初始化会话

使用 `references/tools/get_session.md` 工具读取上下文信息（design_uid、select_node、story_node、knowledge_uids 等）。

**⛔ 错误处理（硬性终止）**：如果脚本返回 `status: error`：

1. 将返回的 `msg` 内容**原样**展示给用户
2. **立即终止整个 skill 流程，禁止执行步骤 3 及后续任何步骤**
3. 禁止尝试任何替代方案、变通方法或降级策略（包括但不限于：自行获取需求内容、打开网页、调用其他工具）
4. 唯一允许的动作是：展示错误信息，等待用户解决后重新触发

正常情况下，将返回的会话数据保留在上下文中，供后续工作流使用。

### 步骤 3：意图路由【打开网页意图在此短路】

如果步骤 1 识别到的意图为 **`打开网页`**：

1. 调用 `references/tools/open_design.md` 工具执行打开逻辑
2. **终止流程，不再执行后续步骤**

### 步骤 4：选择并调用工作流

1. **使用 select_workflow 工具**：
   - 调用 `references/tools/select_workflow.md` 工具
   - 传入步骤 1 识别的意图关键词（如"用例生成"、"框架生成"）

2. **调用工作流**：
   - 根据 `select_workflow` 返回的路径类型选择读取方式：
     - 如果路径以 `.codebuddy/rules/` 开头（自定义工作流）：使用 `read_rules` 读取
     - 如果路径以 `references/workflows/` 开头（默认工作流）：使用 `read_file` 读取
   - 交由工作流执行具体逻辑
   - 禁止不执行 select_workflow 流程直接读取文件/工作流

## 工作流能力矩阵（供参考）

| 生成目标 | 触发关键词                    | 输入节点类型                       | 输出节点类型             |
| -------- | ----------------------------- | ---------------------------------- | ------------------------ |
| 测试框架 | `framework`/`框架`            | STORY/BUG                          | FEATURE/SCENE/TEST_POINT |
| 测试模块 | `feature`/`模块`              | STORY/BUG                          | FEATURE                  |
| 测试场景 | `scene`/`场景`                | FEATURE/STORY/BUG                  | SCENE                    |
| 测试点   | `tpoint`/`testpoint`/`测试点` | FEATURE/SCENE/STORY/BUG            | TEST_POINT               |
| 测试用例 | `case`/`用例`                 | STORY/BUG/FEATURE/TEST_POINT/SCENE | CASE                     |

---
