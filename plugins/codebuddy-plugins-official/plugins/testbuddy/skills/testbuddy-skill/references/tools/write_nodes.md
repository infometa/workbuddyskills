# write_nodes

节点保存工具，通过 Python 脚本对脑图节点进行**新增、修改、删除**操作。所有操作均通过执行 `write_node.py` 脚本完成。

**⚠️ 重要**：执行脚本前**不要切换目录（不要 cd）**，确保在工作区根目录执行。
**⚠️ 重要**：已经生成用例的文件的话，直接复用已生成的文件目录即可。

---

## 支持的操作类型

| action   | 说明     | 命令格式                                                                                    |
| -------- | -------- | ------------------------------------------------------------------------------------------- |
| `add`    | 新增节点 | `python3 <script_dir>/scripts/write_node.py add <file_path> [--design_uid <design_uid>]`    |
| `update` | 修改节点 | `python3 <script_dir>/scripts/write_node.py update <file_path> [--design_uid <design_uid>]` |
| `delete` | 删除节点 | `python3 <script_dir>/scripts/write_node.py delete <file_path> [--design_uid <design_uid>]` |

> 脚本在执行 `add`/`update`/`delete` 时会**自动校验**节点格式，校验失败直接报错，无需手动执行 validate。
> `design_uid` 为可选参数，不传则由服务端自动创建。

---

## 支持的文件格式

脚本支持以下三种格式：

### 1. JSON 格式 (.json)

标准的 JSON 数组格式。

### 2. YAML 格式 (.yaml/.yml)

标准的 YAML 数组格式。

### 3. Markdown 格式 (.md)

直接使用 Markdown 标题层级表示节点结构：

- `## 模块名称` → FEATURE 节点
- `### 场景名称` → SCENE 节点
- `#### 测试点名称` → TEST_POINT 节点
- `##### 用例名称` → CASE 节点

**说明**：Markdown 文件可以直接使用，脚本会自动解析结构中的 `PARENT_UID`、`UID`、`优先级`、`执行步骤` 等字段。

Markdown 中也支持使用 `` `json `` 或 `` `yaml `` 代码块包裹节点数据。

---

## 操作流程

#### 新增节点（add）

```shell
python3 <script_dir>/scripts/write_node.py add <file_path> [--design_uid <design_uid>]
```

**示例**：

```shell
# 指定 design_uid
python3 <script_dir>/scripts/write_node.py add /tmp/nodes_batch.json --design_uid design-Az7SsiL3Ui
# 不指定 design_uid（服务端自动创建）
python3 <script_dir>/scripts/write_node.py add /tmp/nodes_batch.json
```

#### 修改节点（update）

```shell
python3 <script_dir>/scripts/write_node.py update <file_path> [--design_uid <design_uid>]
```

**示例**：

```shell
python3 <script_dir>/scripts/write_node.py update /tmp/nodes_update.json --design_uid design-Az7SsiL3Ui
```

#### 删除节点（delete）

```shell
python3 <script_dir>/scripts/write_node.py delete <file_path> [--design_uid <design_uid>]
```

**示例**：

```shell
python3 <script_dir>/scripts/write_node.py delete /tmp/nodes_delete.json --design_uid design-Az7SsiL3Ui
```

**参数说明**：

- `<script_dir>`：脚本目录的绝对路径（通常为 `.codebuddy/skills/testbuddy-skill`）
- `<file_path>`：包含节点数据的文件完整路径
- `<design_uid>`：设计文件的唯一标识（可选，如：`design-Az7SsiL3Ui`，不传则由服务端自动创建）

---

## 命令执行输出

### 成功输出示例（add）

```json
{
  "status": "success",
  "action": "add",
  "design_uid": "design-Az7SsiL3Ui",
  "file_path": "/tmp/nodes_batch.json",
  "stats": {
    "added": 2,
    "total_added": 2,
    "total_updated": 0,
    "total_deleted": 0
  }
}
```

### 成功输出示例（update）

```json
{
  "status": "success",
  "action": "update",
  "design_uid": "design-Az7SsiL3Ui",
  "file_path": "/tmp/nodes_update.json",
  "stats": {
    "updated": 1,
    "total_added": 0,
    "total_updated": 1,
    "total_deleted": 0
  }
}
```

### 成功输出示例（delete）

```json
{
  "status": "success",
  "action": "delete",
  "design_uid": "design-Az7SsiL3Ui",
  "file_path": "/tmp/nodes_delete.json",
  "stats": {
    "deleted": 1,
    "total_added": 0,
    "total_updated": 0,
    "total_deleted": 1
  }
}
```

### 失败输出示例

```json
{
  "status": "error",
  "msg": "节点校验失败: 节点[0]: 缺少必填字段 'uid'"
}
```

---

## 节点数据格式

### 节点类型枚举

| Kind         | 说明     |
| ------------ | -------- |
| `STORY`      | 需求节点 |
| `BUG`        | 缺陷节点 |
| `FEATURE`    | 功能模块 |
| `SCENE`      | 测试场景 |
| `TEST_POINT` | 测试点   |
| `CASE`       | 测试用例 |

### 用例（CASE）节点

```json
{
  "uid": "case-cf89EaXfQ2",
  "name": "用户正常登录测试",
  "description": "验证用户使用有效凭据成功登录",
  "kind": "CASE",
  "parent_uid": "父节点uid",
  "instance": {
    "preconditions": "用户已注册且账号状态正常",
    "priority": "P0",
    "steps": [
      {
        "action": "执行动作",
        "expected": "预期结果"
      }
    ]
  }
}
```

### 需求或缺陷（STORY/BUG）节点

```json
{
  "uid": "story-DeFgHiJkLm",
  "name": "名称",
  "description": "描述",
  "kind": "STORY",
  "parent_uid": "父节点uid",
  "instance": {
    "workspace": "工作空间",
    "issue_id": "需求或缺陷ID",
    "issue_name": "名称",
    "issue_source": "TAPD",
    "issue_url": "需求链接"
  }
}
```

### 其他类型（FEATURE/SCENE/TEST_POINT）节点

```json
{
  "uid": "test_point-Kx9Yz8Wv7U",
  "name": "节点名称",
  "description": "节点描述",
  "kind": "TEST_POINT",
  "parent_uid": "父节点uid",
  "instance": null
}
```

---

## 使用示例

```shell
# 新增节点（指定 design_uid）
python3 <script_dir>/scripts/write_node.py add /path/to/nodes.json --design_uid <design_uid>

# 新增节点（不指定 design_uid，服务端自动创建）
python3 <script_dir>/scripts/write_node.py add /path/to/nodes.json

# 修改节点
python3 <script_dir>/scripts/write_node.py update /path/to/nodes.json --design_uid <design_uid>

# 删除节点
python3 <script_dir>/scripts/write_node.py delete /path/to/nodes.json --design_uid <design_uid>
```

---

## 注意事项

0. **节点格式校验（自动）**：
   - ✅ 脚本在执行 `add`/`update`/`delete` 时会自动校验节点格式，无需手动执行 validate
   - ❌ 校验失败时，根据错误信息修正文件后重新执行（修正文件禁止新建脚本，使用 `write_file` 工具即可）
   - 📋 支持 JSON、YAML、Markdown 三种格式

1.
1. **使用文件方式**：
   - ✅ 必须使用 `python3 <script_dir>/scripts/write_node.py <action> <design_uid> <file_path>`
   - ✅ 支持 JSON、YAML、Markdown 多种格式
   - ✅ 无命令行长度限制，适合批量操作

1. **设计标识**：`design_uid` 为可选参数，传入时使用完整的 `design_uid`（如：`design-Az7SsiL3Ui`，不是缩写）；不传则由服务端自动创建

1. **必填字段**：
   - `add`：必须包含 uid、name、kind、parent_uid 字段
   - `update`：必须包含 uid、name、description、kind、parent_uid 字段
   - `delete`：必须包含 uid 字段

1. **instance 字段**：
   - CASE 类型：包含 preconditions、priority、steps
   - STORY/BUG 类型：包含 workspace、issue_id 等
   - 其他类型：设为 null

1. **错误处理**：脚本会返回详细的错误信息，指出具体哪个字段有问题

1. **🚫 禁止创建新脚本**：
   - 如果执行脚本时遇到错误，根据错误信息修正文件后重新校验（修正文件禁止新建脚本，使用 `write_file` 工具即可）
   - **严禁创建新的辅助脚本、wrapper 脚本或临时脚本来处理错误**
   - 应通过以下方式解决：
     - 检查并修正节点数据格式
     - 调整命令参数
     - 修复文件路径或 design_uid
     - 补充缺失的必填字段
   - 始终使用现有的标准脚本 `write_node.py`

---

## 优先级说明

- `P0` - 最高优先级（核心功能、阻塞性问题）
- `P1` - 高优先级（重要功能）
- `P2` - 中优先级（一般功能）
- `P3` - 低优先级（边缘场景）
