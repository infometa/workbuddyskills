---
name: beisen-service-portal
version: 2.2.0
description: "北森办事入口。本 Skill 用于根据用户自然语言输入，检索系统菜单并按意图匹配推荐功能入口，引导员工或管理者进入对应的业务办理页面。基于 `beisen-cli staffservice employeeWork menuSearch` 搜索菜单，以可点击 Markdown 链接形式输出菜单入口。当用户询问办事、办事入口、办理、业务入口、菜单、去哪办、功能入口位置、导航路径，或输入疑似功能/页面/报表/菜单的名称或描述时触发。本 Skill 涉及业务操作引导，非纯数据查询。员工和管理者均可使用。"
category: 人力资源/办事入口
author: beisen
agent_created: false
allowed-tools: Bash, Read
---

# 办事入口

**CRITICAL — 开始前 MUST 读取 [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)**

## 任务目标
- 本 Skill 用于：根据用户自然语言输入，检索系统菜单并按意图匹配推荐功能入口
- 触发条件：用户询问功能入口位置、导航路径，表达业务操作意图，或输入疑似功能/菜单名称的文本（含 Agent 弱信号仲裁后的探测式路由）

> 说明：权限校验、阈值过滤、终端适配均由后端 `menuSearch` 自动处理，返回结果均已过滤。`menuSearch` 检索的是租户实时菜单库（含自定义视图/鲁班页/ocean 菜单），因此**不预设句式、不枚举关键词**，能否命中由检索证据决定。

## 路由优先级

本 Skill 处理：搜索并唤起 HR 业务操作菜单、引导用户进入业务办理页面

不归本 Skill 处理：
- 企业知识制度搜索 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 具体业务数据的查询 → 各对应业务域 Skill / [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)
- 审批查询 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)

## 命令速查

| 场景 | CLI 命令 | 说明 |
|------|---------|------|
| 搜索菜单 | `beisen-cli staffservice employeeWork menuSearch --data '{"query":"<用户问题>","minScore":0.3}'` | 按语义匹配检索租户菜单库 |

> `minScore` 固定传 `0.3`，仅返回匹配分数严格大于该值的菜单。`query` 传用户原始问题（可参考同义词表改写，提升命中率）。

## 操作步骤

### 步骤零：意图预分类

在调用检索工具前，先判断用户意图类型：

| 意图类型 | 识别特征 | 处理方式 |
|---------|---------|---------|
| 导航意图 | "在哪看XX"、"XX在哪"、"打开XX"、"XX菜单" | 进入步骤一，入场方式记为**明确找入口** |
| 功能名意图 | 裸名词、短语、疑似功能/页面/报表/菜单的名称或描述性文本（如"我的目标""日报""周报"，及任意自定义菜单名/描述） | 进入步骤一，入场方式记为**探测式** |
| 操作意图 | "帮我请假"、"我要请假"、"请假申请"、"我要出差"、"我要休假"、"申请加班"、"提交报销"、"修改银行卡"等，即用户表达要**执行某项业务操作**的意图 | 进入步骤一，入场方式记为**明确找入口** |
| 咨询意图 | "XX流程是什么"、"年假怎么算"、"离职政策" | 进入步骤一，有相关菜单则一并推荐；无则按入场方式退出（见步骤三） |

> 入场方式决定无命中时的退出行为：**明确找入口** → 输出兜底文案；**探测式** → 零输出静默退回（见步骤三）。若 Agent 已在弱信号仲裁中完成 `menuSearch` 探测并确认菜单强命中后才路由进来，同样按探测式处理。

### 步骤一：调用菜单检索工具

执行 CLI 命令搜索菜单：

```bash
beisen-cli staffservice employeeWork menuSearch --data '{"query":"<用户原始问题>","minScore":0.3}'
```

**参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 用户原始问题（可参考同义词表改写，提升命中率） |
| minScore | number | 是 | 固定传 `0.3` |

**同义词参考**（仅作检索改写的辅助手段，不承担路由职责；未列入的表达直接用原文检索）：
- "打卡" / "签到" → "考勤"
- "工资" / "薪水" → "薪资"
- "请假" / "休假" → "假期"
- "打开日程菜单" → "日程"

**返回结构**：

CLI 返回的外层包装：

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "code": "200",
    "data": {
      "itemsCount": 6,
      "items": [
        {
          "menuId": "d594f7c9-153f-4ea0-9527-7a8f4b4740f3",
          "menuName": "日程",
          "menuDescription": "用于预定日程，员工也可查看自己和他人的日程",
          "menuLink": "https://xxxx/xxx/oR352Sn1"
        }
      ]
    },
    "message": null
  }
}
```

**关键路径**：`data.data.items`（注意双层 `data` 嵌套）。

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| menuId | string | 菜单唯一标识 |
| menuName | string | 菜单名称（用于展示） |
| menuDescription | string | 菜单描述（可能为空） |
| menuLink | string | 菜单跳转链接（完整 URL，用于生成可点击链接） |

- `data.code == "200"` → 业务成功，结果在 `data.data`：
  - `itemsCount > 0` → 进入步骤二判断意图是否命中
  - `itemsCount == 0` 或 `items` 为空 → 按步骤三的无命中分支处理
- `data.code != "200"` → 业务失败，原因在 `data.message`，按步骤四异常处理

### 步骤二：判断用户意图是否命中

返回菜单是语义相近的候选，需逐一判断是否真正符合用户意图：
- 结合用户问题和 `menuName`、`menuDescription` 判断
- 根据意图精度动态控制输出数量，上限 4 个：
  - 精确意图（单一功能）：1-2 个
  - 中等意图（一类功能）：2-3 个
  - 宽泛意图（一个领域）：最多 4 个
- 若无菜单命中意图，按步骤三的无命中分支处理

### 步骤三：输出结果

- **有命中** → 回复引导文案：`你可能需要操作：`，然后以 Markdown 链接列表输出命中的菜单。Agent 自主从返回数据中提取 `menuName` 和 `menuLink`，生成可点击链接：

  ```markdown
  - [菜单名称1](菜单链接1)
  - [菜单名称2](菜单链接2)
  ```

  **输出规则**：
  - 链接文本使用 `menuName`（菜单名称），URL 使用 `menuLink`（完整跳转地址）
  - 若 `menuDescription` 非空，可在链接后用括号补充简要描述，帮助用户判断
  - 示例：`- [日程](https://xxxx/xxx/oR352Sn1)（用于预定日程，员工也可查看自己和他人的日程）`

- **无命中**（检索为空或返回菜单均不符合意图），按入场方式分支：
  - **明确找入口**（用户明确询问入口/导航/操作）→ 输出兜底文案：`没找到这个入口，换个说法我再帮你看看？`
  - **探测式**（功能名意图/咨询意图/Agent 弱信号仲裁转入）→ **零输出静默退回**：不输出任何文案、解释或兜底语，由 Agent 按失败兜底链继续处理（知识查询/兜底）

### 步骤四：异常处理

若 `menuSearch` 调用失败（`code != "200"` 业务失败、超时、异常、返回格式错误等）：
1. 检测当前会话中是否有其他可用 Skill（如 [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md) 知识库检索、[../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md) 数据查询等）
2. 若有可用 Skill → 将用户原始问题转交对应 Skill 处理
3. 若无可替代 Skill → 输出兜底文案：`没找到这个入口，换个说法我再帮你看看？`

## 多轮对话

当用户首次检索无命中后继续追问时，结合上下文补全 query：
- 用户追问中省略主语或宾语时，从上一轮对话中提取并拼接
- 示例：用户先问"在哪看我的工资" → 无命中 → 追问"那出勤呢？" → query 补全为"在哪看我的出勤"

## 使用示例

### 示例 1：导航意图命中
- 输入：用户问"在哪里看工资条"
- 处理：执行 `beisen-cli staffservice employeeWork menuSearch --data '{"query":"在哪里看工资条","minScore":0.3}'` → 判断返回菜单命中意图
- 输出：
  ```
  你可能需要操作：
  - [工资条](https://xxxx/xxx/xxxxxx)
  ```

### 示例 2：操作意图命中（多菜单）
- 输入：用户说"我想打开文化激励"
- 处理：执行 `beisen-cli staffservice employeeWork menuSearch --data '{"query":"文化激励","minScore":0.3}'` → 返回多个候选 → 判断多个菜单命中意图
- 输出：
  ```
  你可能需要操作：
  - [文化激励](https://xxxx/xxx/xxxxxx)
  - [文化激励管理](https://xxxx/xxx/yyyyyy)
  ```

### 示例 3：操作意图命中（请假/出差/休假）
- 输入：用户说"帮我请个假" / "我要出差" / "我要休假"
- 处理：意图分类为操作意图 → 执行 `beisen-cli staffservice employeeWork menuSearch --data '{"query":"帮我请个假","minScore":0.3}'` → 判断返回菜单命中意图
- 输出：
  ```
  你可能需要操作：
  - [请假申请](https://xxxx/xxx/xxxxxx)
  ```

### 示例 4：功能名意图（裸名词）命中
- 输入：用户说"我的目标"（或"日报""周报"，或某自定义菜单的名称/描述文本）
- 处理：功能名意图 → 执行 `beisen-cli staffservice employeeWork menuSearch --data '{"query":"我的目标","minScore":0.3}'` → 返回菜单与输入语义一致，命中
- 输出：
  ```
  你可能需要操作：
  - [我的目标](https://xxxx/xxx/xxxxxx)
  ```

### 示例 5：咨询意图有相关菜单
- 输入：用户问"年假怎么算"
- 处理：执行 `beisen-cli staffservice employeeWork menuSearch --data '{"query":"年假怎么算","minScore":0.3}'` → 返回"假期余额"和"请假记录"菜单 → 与咨询内容相关，一并推荐
- 输出：
  ```
  你可能需要操作：
  - [假期余额](https://xxxx/xxx/xxxxxx)
  - [请假记录](https://xxxx/xxx/yyyyyy)
  ```

### 示例 6：明确找入口但无返回
- 输入：用户问"怎么修改银行卡信息"，`menuSearch` 返回 `itemsCount=0`
- 输出：`没找到这个入口，换个说法我再帮你看看？`

### 示例 7：探测式入场无命中 → 静默退回
- 输入：用户说"月度总结"（功能名意图），`menuSearch` 返回 `itemsCount=0`
- 处理：探测式入场 → 零输出静默退回，由 Agent 继续走知识查询/兜底；不输出"没找到入口"等任何文案

### 示例 8：多轮对话接续
- 第一轮：用户问"在哪看我的工资"（明确找入口）→ 无命中 → 输出`没找到这个入口，换个说法我再帮你看看？`
- 第二轮：用户追问"那出勤呢？" → query 补全为"在哪看我的出勤" → 执行 CLI 命令检索

### 示例 9：路由判断 — 数据查询非本 Skill 范围
- 输入：用户问"我的年假还有多少？"
- 处理：此为业务数据查询（非办事入口），应路由到 [../beisen-attendance-leave/SKILL.md](../beisen-attendance-leave/SKILL.md) / [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)，而非本 Skill

## 禁止事项
- 不得跳过 `menuSearch` 直接编造 menuId 或 menuLink
- 不得修改后端返回的 `menuId` 或 `menuLink`
- 不得在无命中时输出菜单链接列表
- 不得强制输出菜单：意图不匹配时按入场方式输出兜底文案或静默退回
- 不得在探测式入场无命中时输出任何文案（必须零输出静默退回）
- 不得输出冗余的思考过程
- `menuLink` 必须从 CLI 返回中提取，严禁编造 URL

## 详细参考

- [references/service-menu.md](references/service-menu.md)：菜单命令详细参数与返回格式
- [../beisen-shared/SKILL.md](../beisen-shared/SKILL.md)：CLI 安装检查、SSO 认证、错误处理通用策略

## 不在本 Skill 范围

- 企业知识制度搜索 → [../beisen-knowledge/SKILL.md](../beisen-knowledge/SKILL.md)
- 具体业务数据的查询 → 各对应业务域 Skill / [../beisen-data-query/SKILL.md](../beisen-data-query/SKILL.md)
- 审批查询 → [../beisen-approval/SKILL.md](../beisen-approval/SKILL.md)
