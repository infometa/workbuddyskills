# rag_search

知识库检索工具，提供两种检索策略**同时执行**以获取更全面的结果。所有操作均通过执行 `retrieve_knowledge.py` 脚本或调用系统内置 `RAG_search` 完成。

**⚠️ 重要**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。

---

## 检索策略（同时执行）

### 策略 1: 脚本检索知识库

通过 `retrieve_knowledge.py` 脚本检索当前会话相关的知识内容。

```shell
python3 <script_dir>/scripts/retrieve_knowledge.py --query <query> --knowledge_uids <uid1> [uid2 ...] [--top_k 5] [--score_threshold 0.6]
```

**参数说明**：

| 参数                | 是否必填 | 说明                                                              |
| ------------------- | -------- | ----------------------------------------------------------------- |
| `--query`           | 必填     | 检索关键词（**每次只能传一个关键词**，多关键词需分批调用脚本）    |
| `--knowledge_uids`  | 必填     | 知识库 UID 列表，支持多个，空格分隔（通过 `get_session.py` 获取） |
| `--top_k`           | 可选     | 返回结果数量（默认 5）                                            |
| `--score_threshold` | 可选     | 相似度阈值（默认 0.6）                                            |

- `<script_dir>`：脚本目录的绝对路径（通常为 `.codebuddy/skills/testbuddy-skill`）
- `knowledge_uids` 通过 `get_session.py` 获取，**如果没有则不调用策略 1**

### 策略 2: RAG_search 检索附加文件

**触发条件**：当上下文中包含 `<attached_files>` 区域时执行。

- 使用系统内置 `RAG_search` 函数
- **作用范围**：只检索 `<attached_files>` 区域中的文件内容
- 参数：`queryString`（搜索关键词）

---

## 命令执行输出

### 成功输出示例

```json
{
  "status": "success",
  "query": "登录功能",
  "knowledge_uids": ["kb-abc123"],
  "results_count": 3,
  "results": [...]
}
```

### 失败输出示例

```json
{
  "status": "error",
  "msg": "缺少 --query 参数"
}
```

---

## 使用示例

```shell
# 单关键词检索
python3 <script_dir>/scripts/retrieve_knowledge.py --query "登录功能" --knowledge_uids kb-abc123

# 多知识库检索
python3 <script_dir>/scripts/retrieve_knowledge.py --query "支付流程" --knowledge_uids kb-abc123 kb-def456 --top_k 10

# 多关键词需分批调用（每次一个关键词）
python3 <script_dir>/scripts/retrieve_knowledge.py --query "登录功能" --knowledge_uids kb-abc123
python3 <script_dir>/scripts/retrieve_knowledge.py --query "密码验证" --knowledge_uids kb-abc123
```

---

## 执行流程

1. **策略 1**：先通过 `get_session.py` 获取 `knowledge_uids`，如果存在则调用 `retrieve_knowledge.py` 脚本检索，**没有则跳过策略 1**
2. **同时检查策略 2**：如果上下文包含 `<attached_files>`，同时执行 `RAG_search`
3. **结果合并**：将两种策略的结果合并展示

---

## 注意事项

1. **不要创建脚本**：直接执行 `retrieve_knowledge.py`，不要创建任何辅助脚本
2. **每次一个关键词**：`--query` 参数每次只能传一个关键词，多关键词需分批调用
3. **knowledge_uids 来源**：通过 `get_session.py` 获取，没有则不调用策略 1
4. **策略独立**：两种策略相互独立，任一成功都会返回有效结果
5. **策略 2 条件**：仅当上下文包含 `<attached_files>` 时才执行
