---
name: framework-generator
description: >
  测试框架生成工作流定义，根据参考节点及需求分析文件生成测试框架。同时只支持处理一个issue，处理多个时，需要调用多次
   Args:
      inputs: {
            `ref_nodes`: 参考的节点信息（YAML格式数组，包含uid, name, kind字段）
            `issue_analysis`: 需求分析详情 (调用 issue-analyst 工作流获取【强制】)
      }
tools: write_file
---

## 目标

参考需求分析文档，生成测试框架，以yaml结构返回，需要体现父子层级关系，结构类似思维导图。

**参考节点**
<ref_node>
${ref_nodes}
</ref_node>

**需求详情**
<issue_detail>

```
${issue_analysis}
```

</issue_detail>

## 约束

1. 参考节点必须有效，否则，直接报错。
2. 需求分析文档必须有效，否则，直接报错。
3. 层级结构规则
   - 模块（FEATURE）的子节点可以是：模块、场景、测试点
   - 场景（SCENE）的子节点可以是：场景、测试点

## 输出要求

**🚨 关键规则 - 确保输出稳定性**：

1. **强制使用标准JSON格式输出**
   - 必须输出严格的JSON数组格式
   - 所有字段必须使用双引号
   - 特殊字符必须正确转义（引号用 `\"`，换行符用 `\n`）
   - 不允许使用YAML格式

2. **输出格式验证**
   - 输出必须是可直接解析的JSON数组
   - 每个节点必须包含所有必需字段：`uid`, `name`, `description`, `kind`
   - 根节点必须包含 `parent_uid`，子节点通过 `children` 数组体现层级关系
   - 必须为每个节点生成唯一的 `uid` 字段

3. **禁止行为**：
   - ❌ 不要创建任何 Python 脚本
   - ❌ 不要使用YAML格式输出
   - ❌ 不要在JSON中添加注释
   - ❌ 不要输出除JSON数组外的任何其它内容（除了简短确认信息）
   - ❌ 严格禁止重复输出生成框架内容

4. 直接输出到临时文件中

## 框架格式说明

**重要说明**

1. **uid字段生成**：每个节点都必须包含唯一的uid字段，格式为 `{kind}-{随机字符串}`，例如：`feature-abc123`、`scene-def456`、`test_point-ghi789`
2. **parent_uid引用**：
   - **仅根节点**需要parent_uid，`{ref_node.uid}` 需要替换成实际节点的uid
   - **子节点不需要parent_uid**，系统会根据children层级关系自动建立父子关系
3. **层级结构**：通过children数组体现父子关系，支持多层嵌套
4. **节点类型**：严格按照FEATURE → SCENE → TEST_POINT的层级关系
5. **描述完整性**：每个节点都包含清晰的功能描述，便于理解测试范围

## 标准输出格式

**必须严格遵循以下JSON格式**：

基于用户登录功能需求分析，生成的测试框架示例：

```json
[
  {
    "uid": "feature-abc123",
    "name": "用户认证模块",
    "description": "负责用户登录、注册、密码管理等认证相关功能的测试",
    "kind": "FEATURE",
    "parent_uid": "{ref_node.uid}",
    "children": [
      {
        "uid": "scene-def456",
        "name": "用户登录场景",
        "description": "验证用户登录功能的各种场景",
        "kind": "SCENE",
        "children": [
          {
            "uid": "test_point-ghi789",
            "name": "正常登录验证",
            "description": "验证用户使用正确凭据登录的功能",
            "kind": "TEST_POINT"
          },
          {
            "uid": "test_point-jkl012",
            "name": "登录失败处理",
            "description": "验证各种登录失败情况的处理",
            "kind": "TEST_POINT"
          },
          {
            "uid": "test_point-mno345",
            "name": "登录安全控制",
            "description": "验证登录过程中的安全控制机制",
            "kind": "TEST_POINT"
          }
        ]
      },
      {
        "uid": "scene-pqr678",
        "name": "密码管理场景",
        "description": "验证密码重置、修改等密码管理功能",
        "kind": "SCENE",
        "children": [
          {
            "uid": "test_point-stu901",
            "name": "密码重置功能",
            "description": "验证用户密码重置流程",
            "kind": "TEST_POINT"
          },
          {
            "uid": "test_point-vwx234",
            "name": "密码强度验证",
            "description": "验证密码复杂度要求",
            "kind": "TEST_POINT"
          }
        ]
      }
    ]
  },
  {
    "uid": "feature-yza567",
    "name": "会话管理模块",
    "description": "负责用户会话创建、维护、销毁等功能的测试",
    "kind": "FEATURE",
    "parent_uid": "{ref_node.uid}",
    "children": [
      {
        "uid": "scene-bcd890",
        "name": "会话生命周期",
        "description": "验证用户会话的完整生命周期管理",
        "kind": "SCENE",
        "children": [
          {
            "uid": "test_point-efg123",
            "name": "会话创建验证",
            "description": "验证用户登录后会话的正确创建",
            "kind": "TEST_POINT"
          },
          {
            "uid": "test_point-hij456",
            "name": "会话超时处理",
            "description": "验证会话超时后的处理机制",
            "kind": "TEST_POINT"
          },
          {
            "uid": "test_point-klm789",
            "name": "会话安全控制",
            "description": "验证会话劫持防护等安全机制",
            "kind": "TEST_POINT"
          }
        ]
      }
    ]
  }
]
```

## 字段说明

| 字段          | 类型   | 必填 | 说明                                     |
| ------------- | ------ | ---- | ---------------------------------------- |
| `uid`         | string | ✅   | 节点唯一标识，格式：`{kind}-{随机字符}`  |
| `name`        | string | ✅   | 节点名称，简洁明确                       |
| `description` | string | ✅   | 节点详细描述                             |
| `kind`        | string | ✅   | 节点类型：`FEATURE`/`SCENE`/`TEST_POINT` |
| `parent_uid`  | string | ✅   | 仅根节点需要，使用 `ref_nodes` 中的 uid  |
| `children`    | array  | ❌   | 子节点数组，可选                         |

## 特殊字符处理规则

在JSON字符串中，以下字符必须转义：

- 双引号：`"` → `\"`
- 反斜杠：`\` → `\\`
- 换行符：不允许使用真实换行，用 `\n` 或用逗号/分号分隔
- 制表符：`\t`

**示例**：

```json
{
  "name": "用户\"认证\"模块",
  "description": "负责用户登录、注册、密码管理等认证相关功能的测试"
}
```
