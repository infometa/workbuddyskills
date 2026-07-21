# update_logic 工具参考

## 概述

更新问卷的自定义逻辑设置（DSL 代码）。可通过 `get_survey` 返回的 `survey_dsl` 字段获取当前逻辑代码，修改后整体传入。传入空字符串可清空所有逻辑。

## 参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `survey_id` | number | **是** | 问卷 ID |
| `dsl` | string | **是** | 问卷自定义逻辑代码（DSL 脚本语法） |

> **重要**：`dsl` 中引用题目和选项时需使用反引号包裹的 ID 格式（如 `` `q-1-abcd::o-100-ABCD` ``），ID 可从 `get_survey` 返回的题目和选项信息中获取。

## 返回值

### 成功响应

```json
{
  "survey_id": 716128,
  "result": "success"
}
```

### 失败响应

```json
{
  "survey_id": 716128,
  "result": "failed",
  "error": "invalid_dsl_syntax: ..."
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `survey_id` | number | 问卷 ID |
| `result` | string | `"success"` 表示成功，`"failed"` 表示失败 |
| `error` | string | 仅失败时返回，错误描述信息 |

## DSL 语法说明

自定义逻辑使用 DSL（Domain-Specific Language）脚本语法。多条规则用换行分隔。

> 📖 完整语法文档：https://wj.qq.com/docs/dsl/grammar

### 引用格式

在通过 MCP 工具编写 DSL 时，题目和选项 ID 需要使用**反引号包裹**：

| 元素 | 格式 | 示例 |
|------|------|------|
| 题目 | `` `q-1-xxxx` `` | `` `q-1-abcd` `` |
| 选项 | `` `q-1-xxxx::o-100-ABCD` `` | `` `q-1-abcd::o-100-EFGH` `` |
| 矩阵子问题 | `` `q-1-xxxx::s-200-IJKL` `` | `` `q-1-abcd::s-200-IJKL` `` |
| 填空项 | `` `q-1-xxxx::b-300-MNOP` `` | `` `q-1-abcd::b-300-MNOP` `` |

> **注意**：ID 值必须从 `get_survey` 返回的数据中获取，不能自行构造。

### 条件操作符

| 操作符 | 说明 | 示例 |
|--------|------|------|
| `and` | 逻辑与 | `if Q1A1 and Q2A2 then show Q3` |
| `or` | 逻辑或 | `if Q1A1 or Q1A2 then show Q2` |
| `not` | 逻辑非 | `if Q1 and not Q1A3 then show Q2` |
| `()` | 分组 | `if (Q1A1 or Q1A2) and Q2A1 then show Q3` |
| `>` `>=` `==` `<` `<=` | 比较 | `if Q1 > 5 then show Q2` |
| `+` `-` `*` `/` | 算数运算 | `if Q1 + Q2 > 10 then show Q3` |

### 行为控制语句

| 语句类型 | 语法格式 | 说明 |
|---------|---------|------|
| **条件显示** | `if <条件> then show <目标>` | 满足条件时显示题目或选项 |
| **条件隐藏** | `if <条件> then hide <目标>` | 满足条件时隐藏题目或选项 |
| **直接隐藏** | `hide <目标>` | 直接隐藏题目或选项（无条件） |
| **连线跳转** | `if <条件> then branch from <题目> to <目标>` | 满足条件时从某题跳转到指定题目或 `END` |
| **内容替换** | `replace "<文本>" in <题目> title with <来源>` | 将题目标题中的指定文本替换为另一题的回答 |
| **随机排序** | `shuffle <范围>` | 对题目或选项进行随机排序 |
| **随机抽取** | `random show <数量> from <范围>` | 从题目或选项中随机抽取指定数量显示 |
| **自动圈选** | `set <选项>` | 自动选中指定选项 |
| **自动填充** | `set <题目> = <来源>` | 自动填充文本题内容 |

### 特殊关键字

| 关键字 | 说明 | 示例 |
|--------|------|------|
| `END` | 结束页，用于跳转到问卷结尾 | `branch from Q1 to END` |
| `len` | 答案个数 | `if len Q1 > 2 then show Q3` |
| `index` | 答案排在第几位 | `if index Q1A1 == 1 then show Q2` |
| `RANDBETWEEN(min, max)` | 随机生成整数 | `if RANDBETWEEN(1, 10) > 5 then show Q2` |
| `LANG()` | 获取答题者语言 | `if LANG() == "zhs" then show Q1` |
| `PARAMS("key")` | 获取自定义参数 | `if PARAMS("source") == "wechat" then show Q2` |
| `#` | 注释 | `# 这是注释，不会被执行` |

### 范围表示

| 格式 | 说明 | 示例 |
|------|------|------|
| `Q1~3` | 题目 Q1 到 Q3 | `shuffle Q1~3` |
| `Q1A1~4` | 题目 Q1 的选项 A1 到 A4 | `shuffle Q1A1~4` |
| `Q1,Q3,Q5` | 不连续的题目 | `random show 1 from Q1,Q3,Q5` |

> 当连续 3 个以上序号时，系统会自动合并为 `~` 格式。

### weight 权重

`random show` 支持设置权重：

```
random show 1 from Q1~3 weight by 1:1:2
```

表示 Q3 被抽取的概率是 Q1、Q2 的两倍。

## 调用示例

### 典型工作流

```
# 1. 先获取问卷详情，确认题目和选项 ID
get_survey(survey_id=716128)
# 返回中查看 survey_dsl.code 获取当前逻辑代码
# 从 pages → questions → options 中获取题目和选项的 ID

# 2. 编写并更新逻辑
update_logic(survey_id=716128, dsl="if `q-1-abcd::o-100-EFGH` then show `q-1-ijkl`")
```

### 条件显示逻辑

```
# 选择了第1题的第1个选项时，显示第2题
update_logic(survey_id=716128, dsl="if `q-1-abcd::o-100-EFGH` then show `q-1-ijkl`")
```

### 多条件组合

```
# 第1题选了A 且 第2题选了B 时，显示第3题
update_logic(survey_id=716128, dsl="if `q-1-abcd::o-100-EFGH` and `q-1-ijkl::o-200-MNOP` then show `q-1-qrst`")
```

### 连线跳转（甄别题）

```
# 选择了第1题某选项时，跳转到问卷结束
update_logic(survey_id=716128, dsl="if `q-1-abcd::o-100-EFGH` then branch from `q-1-abcd` to END")
```

### 内容替换

```
# 将第3题标题中的"XXX"替换为第1题的回答
update_logic(survey_id=716128, dsl="replace \"XXX\" in `q-1-qrst` title with `q-1-abcd`")
```

### 随机排序与随机抽取

```
# 随机排序第1题的选项1~4
update_logic(survey_id=716128, dsl="shuffle `q-1-abcd::o-100-A`~`q-1-abcd::o-100-D`")

# 从题目1~3中随机抽取1道显示
update_logic(survey_id=716128, dsl="random show 1 from `q-1-abcd`~`q-1-qrst`")
```

### 多条规则组合

```
# 多条规则用换行分隔
update_logic(survey_id=716128, dsl="if `q-1-abcd::o-100-EFGH` then show `q-1-ijkl`\nif `q-1-abcd::o-100-MNOP` then show `q-1-qrst`\nreplace \"XXX\" in `q-1-uvwx` title with `q-1-abcd`")
```

### 清空所有逻辑

```
update_logic(survey_id=716128, dsl="")
```

### mcporter 调用

```bash
# 设置条件显示逻辑
mcporter call tencent-survey.update_logic --args '{"survey_id": 716128, "dsl": "if `q-1-abcd::o-100-EFGH` then show `q-1-ijkl`"}'

# 清空所有逻辑
mcporter call tencent-survey.update_logic --args '{"survey_id": 716128, "dsl": ""}'
```

## 权限要求

调用此接口需要满足以下权限条件（逐级校验）：

| 校验层 | 说明 |
|--------|------|
| `WithSurveyClaims` | 问卷归属校验：问卷必须属于当前 Token 绑定的团队 |
| `WithSurveyEditorClaims` | 编辑权限校验：当前用户需具有该问卷的编辑权限 |
| `WithSurveyEditableClaims` | 可编辑状态校验：问卷必须处于可编辑状态（如草稿状态） |

## 错误码

| error.type | 错误描述 | 解决方案 |
|------------|---------|---------|
| `invalid_dsl_syntax` | DSL 语法错误 | 检查 DSL 代码语法是否正确，参考语法文档 |
| `invalid_reference` | 引用的题目/选项 ID 不存在 | 确认 ID 从 get_survey 返回数据中获取 |
| `claim_error` | 权限校验错误 | 问卷不属于当前 Token 绑定的团队，或无编辑权限 |
| `survey_not_editable` | 问卷不可编辑 | 问卷可能正在回收中，需先暂停回收 |
| `invalid_argument` | 参数校验不通过 | 检查 survey_id、dsl 是否正确 |

## 注意事项

1. **先获取再更新**：必须先调用 `get_survey` 获取问卷详情，从返回数据中获取正确的题目 ID 和选项 ID
2. **整体覆盖**：`dsl` 参数为问卷的完整逻辑代码，每次调用会覆盖所有已有逻辑。如需追加规则，需先获取当前 `survey_dsl.code`，在其基础上修改后整体传入
3. **非幂等操作**：每次调用都会覆盖原有逻辑配置
4. **ID 使用反引号**：通过 MCP 工具编写 DSL 时，题目和选项 ID 需使用反引号包裹（如 `` `q-1-abcd::o-100-EFGH` ``）
5. **多条规则换行分隔**：在 JSON 参数中，多条规则之间使用 `\n` 分隔
6. **清空逻辑**：传入空字符串（`""`）可清空所有自定义逻辑
7. **问卷状态要求**：问卷必须处于可编辑状态，正在回收中的问卷需先暂停才能编辑
8. **与基础逻辑共存**：自定义逻辑与基础逻辑可同时设置，执行顺序为先执行基础逻辑、再执行自定义逻辑
9. **付费功能**：自定义逻辑为付费高级功能。如调用时返回 `paid_function_trial_no_permission` 错误，说明当前团队未购买该功能权限，需引导用户前往[腾讯问卷购买页](https://wj.qq.com/pricing)进行付费升级（升级为付费版本）后再使用

## Annotations（工具注解）

| 注解 | 值 | 说明 |
|------|---|------|
| `readOnlyHint` | false | 非只读操作，会修改问卷逻辑配置 |
| `destructiveHint` | false | 非破坏性操作（更新而非删除） |
| `idempotentHint` | false | **非幂等**，每次调用都覆盖逻辑配置 |
| `openWorldHint` | false | 内部调用 |
