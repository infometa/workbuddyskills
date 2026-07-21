# 用例生成工作流

**触发关键词**：`生成测试用例`、`生成用例`、`根据测试点生成用例`、`根据需求生成用例`

**工作流简介**：基于需求分析和参考节点，生成全面的测试用例（包括正常、异常、边界等场景）

## 执行清单规划

在开始执行前，工作流需要：

1. 使用 `todo_write` 工具创建执行清单，将下述执行步骤转化为 TODO 列表
2. 执行应该按照列表的顺序进行执行，禁止跳过步骤
3. 每完成一个步骤后，需检查步骤是否执行，检查通过后更新对应 TODO 的状态为 `completed`
4. 开始新步骤时，将对应 TODO 状态更新为 `in_progress`

**标准 TODO 清单模板**：

Demo:

```json
[
  {"id":"1", "status":"pending", "content":"step1"},
  {"id":"2", "status":"pending", "content":"step2"},
  ...
]
```

## 执行流程

**步骤 1：确认参考节点列表**
需根据实际用户的意图选择合适的方式

- **方式一**：从对话上下文中读取（SKILL加载时已执行 get_session，结果在上下文中）
- **方式二**：使用 `get_session` 工具（位于 `references/tools/get_session.md`）读取会话信息
- **方式三**：使用 `search_nodes` 工具（位于 `references/tools/search_nodes.md`）从脑图节点中查询
- 节点信息包含：uid, name, kind, instance
- 如未找到节点信息或信息不完整，提示用户并终止流程
- 参考节点可能是单个、也可能是多个
- **禁止**：从其他文件中获取参考节点列表

**步骤 2：查找关联需求**
需根据实际用户的意图选择合适的方式

- **方式一**：从对话上下文中读取（SKILL加载时已执行 get_session，结果在上下文中）
- **方式二**：使用 `get_session` 工具（位于 `references/tools/get_session.md`）读取会话信息
- **方式三**：使用 `search_nodes` 工具（位于 `references/tools/search_nodes.md`）从脑图查询 STORY 或 BUG 类型节点
- 节点信息包含：uid, name, kind, instance（包含 IssueUid, IssueName 等需求详情）
- 如未找到需求节点信息，提示用户并终止
- **禁止**：从其他文件中获取需求信息

**步骤 3：检索需求知识库**

- **使用工具**：`rag_search`（位于 `references/tools/rag_search.md`）
- **前置条件**：通过 `get_session.py` 获取 `knowledge_uids`，如果没有则跳过策略1（脚本检索），仅在上下文包含 `<attached_files>` 时执行策略2（RAG_search）
- **检索目标**：从需求分析结果中提取关键词进行检索
  - **关键词提取方法**：
    - 从步骤3的需求分析结果中识别核心功能模块（如"用户登录"、"权限管理"、"数据导出"）
    - 提取关键业务术语和专业词汇（如"鉴权"、"加密"、"回滚"）
    - 识别技术要点（如"API接口"、"数据库事务"、"缓存策略"）
    - 建议提取 3-5 个最具代表性的关键词
  - **检索策略**：
    - **优先策略**：使用 2-3 个核心关键词组合检索（如"用户登录 密码验证"），获取高相关性内容
    - **补充策略**：如组合检索结果不足，可针对单个重要关键词补充检索
    - 检索与需求相关的技术规范、业务规则、实现方案
  - **结果合并**：将检索到的知识库内容与步骤3的需求分析结果合并
    - 在需求分析文档末尾追加 "## 知识库参考信息" 章节
    - 整理检索内容，标注来源和关联性
    - 合并后的完整文档作为后续用例生成的输入

**步骤 4：需求分析**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"需求分析"
- **根据返回结果**：
  - 如果返回自定义规则路径（`.codebuddy/rules/xxx`）：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径（`references/generators/xxx`）：使用 `read_file` 读取 Generator 内容
- **执行方式**：按获取到的规则/Generator定义执行需求分析
- **标准输入参数**
  ```python
  {
    "issue_uid": "{需求节点的uid}",
    "issue_kind": "STORY 或 BUG",
    "raw_issue": "{需求详情内容或文件路径 @file:xxx}"
  }
  ```
- **输出**：需求分析文档结果
- **复用逻辑**：如该需求已分析过，直接使用历史分析文档

**步骤 5：生成测试用例**

- **使用工具**：`select_rule`（位于 `references/tools/select_rule`），传入关键词"用例生成"
- **根据返回结果**：
  - 如果返回自定义规则路径（`.codebuddy/rules/xxx`）：使用 `read_rules` 读取规则内容
  - 如果返回默认Generator路径（`references/generators/xxx`）：使用 `read_file` 读取 Generator 内容
- **执行方式**：按获取到的规则/Generator定义执行用例生成
- **标准输入参数**:
  ```python
  {
    "ref_nodes": [  # YAML格式的参考节点数组
      {
        "uid": "node_123",
        "name": "登录功能测试点",
        "kind": "TEST_POINT"
      }
    ],
    "issue_analysis": "{步骤3生成的需求分析文档完整内容（已包含步骤4合并的知识库参考信息，如有）}",
    "knowledge_context": "{步骤5检索到的历史用例参考（如有）}"
  }
  ```
- **输出要求**：
  - ✅ **必须输出标准JSON数组格式**（参考 `references/generators/case-generator.md`）
  - ✅ 每个用例节点必须包含完整字段：`uid`, `name`, `description`, `kind`, `parent_uid`, `instance`
  - ✅ 所有字符串必须正确转义特殊字符（引号、换行符等）
  - ❌ 禁止使用YAML格式
  - ❌ 禁止在JSON中添加注释

**步骤 6：添加节点到脑图**

- **使用工具**：`write_nodes`（位于 `references/tools/write_nodes.md`）的 `add` 操作
- **⚠️ 必须先读取** `references/tools/write_nodes.md` 工具定义，了解命令格式和参数要求
- **执行方式**：
  1. 将步骤 5 生成的节点数据写入临时文件（JSON 格式）
  2. 按照 `write_nodes.md` 中的命令格式，执行 `write_node.py add <file_path>` 命令（如果 session 中有 `design_uid` 则通过 `--design_uid` 传入，没有则不传）
  3. 检查命令输出，确认节点添加成功
- **禁止跳过此步骤**：无论任何模式，只要前面步骤生成了节点数据，就必须执行此步骤将节点写入脑图
