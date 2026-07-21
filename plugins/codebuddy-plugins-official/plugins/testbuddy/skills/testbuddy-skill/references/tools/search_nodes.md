# search_nodes

查询脑图节点的详细信息。支持按 UID 列表查询指定节点，或不传 uids 查询整个 design 下所有节点。通过执行 `search_node.py` 脚本完成查询，指定 uids 时优先从本地脑图文件查询，本地文件不存在或未指定 uids 时自动调用远程接口。

**⚠️ 重要**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。
**⚠️ 重要**：**操作过程中不要创建任何临时脚本或代码文件。**

---

## 命令格式

```shell
python3 <script_dir>/scripts/search_node.py --design_uid <design_uid> [--namespace <namespace>] [--uids <uid1> [uid2 ...]] [--ancestor] [--no-descendant] [--kind <KIND>]
```

**参数说明**：

| 参数              | 是否必填 | 说明                                                                  |
| ----------------- | -------- | --------------------------------------------------------------------- |
| `--namespace`     | 可选     | 命名空间（不填时后端从 token 中获取）                                 |
| `--design_uid`    | 必填     | 设计文件的唯一标识（如：`design-Az7SsiL3Ui`）                         |
| `--uids`          | 可选     | 节点 UID 列表，支持多个，空格分隔（不填时查询整个 design 下所有节点） |
| `--ancestor`      | 可选     | 加上此标志，同时返回目标节点的所有祖先节点                            |
| `--no-descendant` | 可选     | 加上此标志，不返回后代节点（**默认返回后代节点**）                    |
| `--kind`          | 可选     | 节点类型过滤，如 `CASE`、`FEATURE`、`STORY`、`TEST_POINT` 等          |

- `<script_dir>`：脚本目录的绝对路径（通常为 `.codebuddy/skills/testbuddy-skill`）

---

## 查询策略

1. **mindmap 模式优先本地查询**：指定 uids 时，从 `.testbuddy/assets/{design_uid}.json` 读取脑图文件，按 uid 精确匹配，速度快
2. **chat 模式或本地不存在时走远程**：chat 模式直接调用远程接口，mindmap 模式本地文件不存在时也自动降级到远程接口（需要 token）

---

## 支持的节点类型（--kind）

| Kind         | 说明     |
| ------------ | -------- |
| `STORY`      | 需求节点 |
| `BUG`        | 缺陷节点 |
| `FEATURE`    | 功能模块 |
| `SCENE`      | 测试场景 |
| `TEST_POINT` | 测试点   |
| `CASE`       | 测试用例 |

---

## 命令执行输出

### 成功输出示例

```json
{
  "status": "success",
  "source": "local",
  "design_uid": "design-Az7SsiL3Ui",
  "total": 2,
  "data": [
    {
      "uid": "case-cf89EaXfQ2",
      "name": "用户正常登录测试",
      "description": "验证用户使用有效凭据成功登录",
      "kind": "CASE",
      "parent_uid": "test_point-Kx9Yz8Wv7U"
    },
    {
      "uid": "test_point-Kx9Yz8Wv7U",
      "name": "登录测试点",
      "kind": "TEST_POINT",
      "parent_uid": "feature-Abc123"
    }
  ]
}
```

### 失败输出示例

```json
{
  "status": "error",
  "msg": "缺少 --uids 参数"
}
```

---

## 使用示例

```shell
# 查询整个 design 下所有节点（不传 uids）
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui

# 查询单个节点及其所有后代节点（默认行为）
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2

# 批量查询多个节点及其后代
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui --uids uid1 uid2 uid3

# 查询节点及其所有祖先节点（了解节点所在层级结构）
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2 --ancestor

# 只查询节点本身，不返回后代
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2 --no-descendant

# 查询后代节点中只返回测试用例类型
python3 <script_dir>/scripts/search_node.py --design_uid design-Az7SsiL3Ui --uids feature-Kx9Yz8Wv7U --kind CASE

# 指定 namespace（通常不需要，后端会从 token 自动获取）
python3 <script_dir>/scripts/search_node.py --namespace my_ns --design_uid design-Az7SsiL3Ui --uids case-cf89EaXfQ2
```

---

## 注意事项

1. **不要创建脚本**：直接执行 `search_node.py`，不要创建任何辅助脚本
2. **uid 精确匹配**：`--uids` 参数按 uid 精确查找，不支持模糊匹配；不传 `--uids` 时查询整个 design
3. **kind 精确匹配**：`--kind` 参数值需大写（如 `CASE`、`FEATURE`）
4. **token 要求**：远程查询需要 token，token 从 `session.json` 或环境变量 `TESTBUDDY_TOKEN` 读取
5. **错误处理**：脚本会返回详细的错误信息，根据提示修正参数后重新执行
