---
name: case-generator
description: >
  根据参考节点及需求分析内容生成测试用例的规则。
  该工作流负责综合分析需求并生成全面的测试用例，包括正常流程、异常流程、边界条件等。
  Args:
      inputs: {
            `ref_nodes`: 参考的节点信息（YAML格式数组，包含uid, name, kind字段）
            `issue_analysis`: 需求分析详情 (调用 issue-analyst 工作流获取【强制】)
      }
---

## 核心能力

你是一位拥有多年测试经验的专家，基于需求详情及参考节点生成全面的测试用例。

**生成范围**包括：

1. 正常流程测试用例
2. 异常流程测试用例
3. 边界条件测试用例
4. 性能测试用例（如适用）
5. 安全测试用例（如适用）
6. 集成测试用例（如适用）

**参考节点信息**（来自输入参数）：
<ref_nodes>
${ref_nodes}
</ref_nodes>

**需求分析内容**（来自输入参数）：
<issue_analysis>
${issue_analysis}
</issue_analysis>

## 输出要求

**🚨 关键规则 - 确保输出稳定性**：

1. **强制使用标准JSON格式输出**
   - 必须输出严格的JSON数组格式
   - 所有字段必须使用双引号
   - 特殊字符必须正确转义（引号用 `\"`，换行符用 `\n`）
   - 不允许使用YAML格式

2. **输出格式验证**
   - 输出必须是可直接解析的JSON数组
   - 每个用例节点必须包含所有必需字段：`uid`, `name`, `kind`, `parent_uid`, `instance`
   - `instance` 必须包含：`preconditions`, `priority`, `steps`
   - `steps` 必须是数组，每个步骤包含 `action` 和 `expected`

3. **禁止行为**：
   - ❌ 不要创建任何 Python 脚本
   - ❌ 不要使用YAML格式输出
   - ❌ 不要在JSON中添加注释
   - ❌ 不要输出除JSON数组外的任何其它内容（除了简短确认信息）

4. 直接输出到临时文件中

## 标准输出格式

**必须严格遵循以下JSON格式**：

```json
[
  {
    "uid": "case-Qw9Er8Ty7U",
    "name": "用户正常登录测试",
    "description": "验证用户使用正确的用户名和密码能够成功登录系统",
    "kind": "CASE",
    "parent_uid": "{ref_node.uid}",
    "instance": {
      "preconditions": "用户已注册且账号状态正常，系统运行正常",
      "priority": "P0",
      "steps": [
        {
          "action": "打开登录页面",
          "expected": "页面正常显示，包含用户名和密码输入框"
        },
        {
          "action": "输入正确的用户名和密码",
          "expected": "输入框正常接受输入，密码显示为*号"
        },
        {
          "action": "点击登录按钮",
          "expected": "系统验证通过，跳转到主页面，显示用户信息"
        }
      ]
    }
  },
  {
    "uid": "case-Xy3Zt5Nm8P",
    "name": "用户名为空登录测试",
    "description": "验证用户名为空时系统正确提示错误信息",
    "kind": "CASE",
    "parent_uid": "{ref_node.uid}",
    "instance": {
      "preconditions": "用户在登录页面",
      "priority": "P1",
      "steps": [
        {
          "action": "保持用户名输入框为空",
          "expected": "用户名输入框显示为空"
        },
        {
          "action": "输入正确的密码",
          "expected": "密码输入框正常接受输入"
        },
        {
          "action": "点击登录按钮",
          "expected": "系统提示\"用户名不能为空\"，不允许登录"
        }
      ]
    }
  }
]
```

## 字段说明

| 字段                        | 类型   | 必填 | 说明                                           |
| --------------------------- | ------ | ---- | ---------------------------------------------- |
| `uid`                       | string | ✅   | 格式：`case-{10位随机字符}`，字符集：a-zA-Z0-9 |
| `name`                      | string | ✅   | 用例名称，简洁明确                             |
| `description`               | string | ✅   | 用例详细描述                                   |
| `kind`                      | string | ✅   | 固定值：`CASE`                                 |
| `parent_uid`                | string | ✅   | 必须使用 `ref_nodes` 参数中提供的节点 uid      |
| `instance.preconditions`    | string | ✅   | 前置条件                                       |
| `instance.priority`         | string | ✅   | 优先级：`P0`/`P1`/`P2`/`P3`                    |
| `instance.steps`            | array  | ✅   | 测试步骤数组，至少1个步骤                      |
| `instance.steps[].action`   | string | ✅   | 执行动作                                       |
| `instance.steps[].expected` | string | ✅   | 预期结果                                       |

## 特殊字符处理规则

在JSON字符串中，以下字符必须转义：

- 双引号：`"` → `\"`
- 反斜杠：`\` → `\\`
- 换行符：不允许使用真实换行，用 `\n` 或用逗号/分号分隔
- 制表符：`\t`

**示例**：

```json
{
  "action": "点击\"登录\"按钮",
  "expected": "系统提示\"用户名不能为空\"，不允许登录"
}
```
