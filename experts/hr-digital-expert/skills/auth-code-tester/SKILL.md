---
name: auth-code-tester
description: >
  权限中台鉴权测试 SKILL。负责对开发者集成的鉴权功能进行集成测试和页面测试。
  包括：自动生成测试用例、从权限中台接口获取真实鉴权数据、结合业务数据构造正反例、
  输出测试结果并回写到测试用例文件。
  当"鉴权功能开发完成"、"运行集成测试"、"验证权限控制"、"启动测试"、"测试每个页面"时使用。
---

# 权限中台鉴权测试

本 SKILL 负责对业务系统中集成的权限中台鉴权功能进行系统化测试，分为**集成测试**和**页面测试**两个阶段。

> **加载即执行**：当本 SKILL 由 `auth-code-developer` 链式触发时（步骤 9 推送成功后），加载完成即开始集成测试；集成测试全部通过后，**在同一轮回复内**继续执行页面测试。仅当用户**直接输入测试关键词**（"启动测试""验证页面"等）单独唤起本 SKILL 时，才按用户指令决定执行范围。

---

## 零、测试用例文件

在项目根路径下维护一个统一的测试用例文件 `auth-test-cases.json`，所有测试用例和历史测试结果均记录于此。

### 文件结构

```json
{
  "version": "1.0",
  "updatedAt": "2026-01-01T00:00:00Z",
  "cases": [
    {
      "id": "tc-001",
      "permissionCode": "Menu_Button_User_Export",
      "feature": "用户导出",
      "type": "integration",
      "scenario": "positive",
      "description": "有权限且有该组织数据的用户可以正常导出",
      "mockAuthData": { },
      "mockBusinessData": { },
      "expectedStatus": 200,
      "expectedDataRule": "all items org_code starts with OA000001.00002234",
      "lastResult": {
        "passed": true,
        "testedAt": "2026-01-01T00:00:00Z",
        "actual": "..."
      }
    }
  ]
}
```

如文件不存在则自动创建；每次测试执行后将结果回写到对应用例的 `lastResult` 字段。

---

## 一、触发模式

### 1.1 集成测试（自动触发）

**触发时机**：`auth-code-developer` SKILL 完成所有鉴权代码生成（步骤 3-8 全部完成）后，自动触发。

**测试范围**：覆盖项目中**所有**已集成鉴权的权限项，逐一验证「功能权限校验 + 数据范围过滤 + 本地超管模式」完整链路。

**执行流程**：见第二章。

**输出**：集成测试报告。**全部通过后**，自动继续执行页面测试。

### 1.2 页面测试（自动触发）

**触发时机**：集成测试全部通过后，自动触发。也可由用户主动发起（关键词：「启动测试」「测试每个页面」「页面测试」「验证页面能正常查到数据」）。

**测试目标**：
1. 每个已集成鉴权的菜单页面**打开不报错**（HTTP 200，无明显错误响应）
2. 每个页面的**数据查询接口能返回数据**（非空列表，且数据符合权限范围过滤）
3. **菜单权限项管理功能可用**：
   - 页面上有进入「菜单权限项管理」的入口（导航菜单、链接或按钮）
   - 进入后能查询到权限项列表数据（接口返回非空）
   - 页面上存在推送按钮（只验证按钮存在，不触发推送）

**测试范围**：所有 `Menu_Page_` 类型的权限项对应的页面路由和数据查询接口，以及菜单权限项管理模块。

**执行流程**：见第三章。

**遇到问题自动修复**：测试发现报错、无数据、入口缺失或推送按钮不存在时，自动定位并修复代码，修复后自动回归测试，直至所有目标通过。

---

## 二、集成测试执行流程

### 步骤 1：收集全量权限项

扫描项目代码，提取所有已集成鉴权的权限项编码（通过 `// ===== 权限控制开始 =====` 标记和 `checkPermission` 调用定位）。

读取 `auth-test-cases.json` 中已有的用例，对比找出：
- 有用例的权限项 → 直接复用
- 无用例的权限项 → 按步骤 2-4 新建用例

### 步骤 2：获取真实鉴权数据

通过 MCP 工具从权限中台获取真实配置，用于构造模拟数据：

```
# 获取数据范围类型列表
mcp_call_tool("hr-auth-copilot", "execute", {
  "command": "mysql_query",
  "args": {
    "sql": "SELECT DISTINCT dim_type_code, dim_type_name FROM v_ai_data_scope ORDER BY dim_type_code",
    "userQuestion": "获取数据范围类型列表"
  }
})

# 获取指定类型的码值列表（如 Org、WorkPlace）
mcp_call_tool("hr-auth-copilot", "execute", {
  "command": "mysql_query",
  "args": {
    "sql": "SELECT dim_item_code, dim_item_parent_code, dim_item_name, dim_item_full_name FROM v_ai_data_scope WHERE dim_type_code = 'Org' LIMIT 10",
    "userQuestion": "获取Org类型的码值列表"
  }
})
mcp_call_tool("hr-auth-copilot", "execute", {
  "command": "mysql_query",
  "args": {
    "sql": "SELECT dim_item_code, dim_item_parent_code, dim_item_name, dim_item_full_name FROM v_ai_data_scope WHERE dim_type_code = 'WorkPlace'",
    "userQuestion": "获取WorkPlace类型的码值列表"
  }
})
```

用返回的真实码值构造鉴权模拟数据（而非随机捏造），确保测试数据与权限中台实际配置一致。

### 步骤 3：获取业务数据

通过用户已写的业务查询逻辑（SQL 或 ORM）从数据库中查询真实业务数据，用于构造正反例：

```typescript
// 查询业务数据，用于判断哪些数据在权限范围内，哪些不在
// 表名和字段名来自 auth.config.json 中的 DATA_SCOPE_FIELD_MAP 配置
const allData = await db.query('SELECT <org_field>, <scope_field> FROM <business_table> LIMIT 100');
```

业务数据必须使用真实查询，不可硬编码，确保测试覆盖真实数据分布。

### 步骤 4：构造测试用例

每个权限项**至少**生成 **2 个正例 + 2 个反例**：

| 用例类型 | 场景 | 鉴权模拟数据 | 业务数据预期 |
|---------|------|------------|------------|
| 正例 1 | 有权限 + 有该范围内的数据 | 包含该权限项 + 具体数据范围码值 | 返回 200，数据均在范围内 |
| 正例 2 | 有权限 + 拥有「全部」特殊值 | 包含该权限项 + All 特殊值 | 返回 200，数据不过滤 |
| 反例 1 | 无该权限项 | 不包含该权限项（空数组或 null） | 返回 403 |
| 反例 2 | 有权限 + 数据不在范围内 | 包含该权限项 + 无交集的范围码值 | 返回 200，data 为空 |

**鉴权模拟数据格式**（模拟 `getUserOperations` 和 `getUserDataScope` 的返回值）：

```typescript
// 正例 1 的模拟鉴权数据
const mockAuthPositive1 = {
  operations: ['<permissionCode>'],  // 有权限
  dataScope: {
    success: true, code: '0',
    data: [{
      authid: 'test-001',
      roleCode: 'test-role',
      dataScopes: {
        Org: ['<真实组织码值，来自 MCP>'],
        WorkPlace: ['<真实工作地码值，来自 MCP>']
      }
    }]
  }
};

// 反例 1 的模拟鉴权数据
const mockAuthNegative1 = {
  operations: [],  // 无权限（空数组）
  dataScope: null
};

// 反例 2 的模拟鉴权数据（有权限但范围内无数据）
const mockAuthNegative2 = {
  operations: ['<permissionCode>'],
  dataScope: {
    success: true, code: '0',
    data: [{
      authid: 'test-002',
      roleCode: 'test-role',
      dataScopes: {
        Org: ['<不存在的组织码值，确保无交集>'],
        WorkPlace: ['<不存在的工作地码值>']
      }
    }]
  }
};
```

> **⚠️ 格式示例，禁止直接复用**：以上模拟数据中的权限项编码、码值均为示例，生成时必须替换为实际的权限项编码和 MCP 返回的真实码值。

### 步骤 5：并行执行全量测试

对所有权限项逐一执行测试，在 `local` 模式下注入模拟鉴权数据（不依赖真实权限中台账号）：

```typescript
describe('<permissionCode> 鉴权测试', () => {

  it('[正例1] 有权限且数据在授权范围内，应返回过滤后数据', async () => {
    mockAuthService(mockAuthPositive1);
    const res = await callApi('<method>', '<api_path>', userId);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.length).toBeGreaterThan(0);
    // 验证数据均在权限范围内
  });

  it('[正例2] 有权限且拥有全部数据范围，应返回全量数据', async () => {
    mockAuthService(mockAuthPositive2);
    const res = await callApi('<method>', '<api_path>', userId);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.length).toBeGreaterThan(0);
  });

  it('[反例1] 无该权限项，应返回 403', async () => {
    mockAuthService(mockAuthNegative1);
    const res = await callApi('<method>', '<api_path>', userId);
    expect(res.status).toBe(403);
  });

  it('[反例2] 有权限但数据范围内无数据，应返回空列表', async () => {
    mockAuthService(mockAuthNegative2);
    const res = await callApi('<method>', '<api_path>', userId);
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.length).toBe(0);
  });
});
```

### 步骤 6：输出集成测试报告并回写

**输出给用户**：

```
=== 集成测试报告 ===
测试时间：2026-01-01 10:00:00
覆盖权限项：5 个
总用例数：20 个（10 正例 + 10 反例）

权限项                        正例    反例    状态
─────────────────────────────────────────────────
Menu_Page_User_Management     2/2     2/2     ✅ 全通过
Menu_Button_User_Export       2/2     2/2     ✅ 全通过
Menu_Button_User_Delete       1/2     2/2     ⚠️ 1 个失败
Menu_Page_Order_List          2/2     2/2     ✅ 全通过
Menu_Button_Order_Delete      2/2     1/2     ⚠️ 1 个失败

失败详情：
[Menu_Button_User_Delete - 正例2] 全部数据范围时返回了过滤后的数据，预期返回全量...
[Menu_Button_Order_Delete - 反例2] 无交集范围时仍返回了数据，数据范围过滤可能未生效...
```

将完整报告回写到 `auth-test-cases.json` 的 `lastResult` 中。

**若存在失败**：自动分析失败原因，修复对应的鉴权代码，修复后重新执行失败的用例，直至全部通过。

**全部通过后**，自动进入第三章「页面测试执行流程」，无需用户确认。

---

## 三、页面测试执行流程

### 步骤 1：检查本地服务是否可访问

在发起任何 HTTP 请求之前，先检查本地服务是否已启动：

```
访问本地服务根路径（如 http://localhost:3000）
  ├─ 可访问（HTTP 200/3xx）→ 继续执行步骤 2
  └─ 不可访问（Connection Refused / 超时）→ 执行启动流程
```

**启动流程**：
1. 扫描项目 `package.json`，识别启动命令（优先顺序：`dev` > `start` > `serve`）
2. 检查 `.env` / `.env.local` 文件是否存在，缺失则提示用户补充后继续
3. 执行启动命令，等待服务就绪（检测到端口监听或健康检查接口返回 200）
4. 就绪后继续步骤 2；若启动失败则输出错误日志，停止并提示用户排查

### 步骤 2：检查菜单权限项管理模块是否已建设

**在进行任何页面测试之前，先检查菜单权限项管理模块是否存在**，根据结果决定后续行动：

```
扫描项目代码，查找菜单权限项管理模块
  ├─ 已存在（有对应路由、列表接口、推送相关代码）
  │     └─ 将菜单权限项管理页面纳入步骤 4 的全面页面测试范围，继续执行步骤 3
  └─ 不存在
        └─ 先调用 auth-code-developer SKILL 建设菜单权限项管理功能，
           建设完成后将其纳入测试范围，再继续执行步骤 3
```

**菜单权限项管理模块的测试要求**（纳入步骤 4 后按此标准验证）：
1. 页面上有进入菜单权限项管理的导航入口（导航菜单/侧边栏/顶部菜单）
2. 进入后页面可正常加载（HTTP 200，无错误信息）
3. 权限项列表查询接口返回数据（非空）
4. 页面上存在推送按钮（只验证存在，不触发推送）

以上 4 项全部通过才算菜单权限项管理模块验证通过。

### 步骤 3：收集待测页面

扫描以下来源，收集所有需要测试的页面：
1. `auth-test-cases.json` 中 `permissionCode` 以 `Menu_Page_` 开头的用例
2. 项目代码中通过 `PermissionGuard` / 路由守卫保护的页面路由
3. `.hrright/auth.config.json` 中 `permissions` 数组的顶级节点（`Menu_Page_` 类型）
4. 步骤 2 中确认的菜单权限项管理页面

对每个页面记录：页面路由路径、对应的数据查询接口（`GET` 请求）、绑定的权限项编码（菜单权限项管理页面额外记录推送按钮的 HTML 标识）。

### 步骤 4：确认本地超管模式

确认 `~/.hrright/{sysCode}/local-permissions.json` 存在且包含所有 `Menu_Page_` 权限项（含菜单权限项管理页面的权限项）。若文件不存在或权限项缺失，自动生成/补充后继续。

### 步骤 5：逐页面执行测试

对每个页面依次执行：

#### 5.1 页面加载测试

```
访问页面路由（如 GET /employee-management）
  ├─ HTTP 200 → ✅ 页面加载正常
  ├─ HTTP 4xx/5xx → ❌ 页面加载失败，记录错误
  └─ 响应内容包含明显错误信息（如 stack trace、Error:、Exception）→ ❌ 记录错误
```

#### 5.2 数据查询测试

```
调用该页面的数据查询接口（如 GET /api/employee/list）
  ├─ 返回 200 且 data 不为空 → ✅ 能查询到数据
  ├─ 返回 200 但 data 为空或 null → ⚠️ 接口正常但无数据，检查数据库是否有数据
  ├─ 返回 403 → ❌ 权限校验拦截，检查超管文件是否包含该权限项
  └─ 返回 4xx/5xx 或抛出异常 → ❌ 接口报错，记录错误信息
```

#### 5.3 菜单权限项管理专项验证（仅针对该页面）

```
1. 检查是否存在进入菜单权限项管理的导航入口
   ├─ 在导航菜单/侧边栏/顶部菜单中能找到该入口 → ✅
   └─ 找不到任何入口 → ❌ 记录：缺少菜单权限项管理导航入口

2. 检查页面上是否存在推送按钮（含「推送」、「同步」、「推送到权限中台」等字样）
   ├─ 存在推送按钮 → ✅（不触发，只验证存在）
   └─ 不存在推送按钮 → ❌ 记录：缺少推送按钮
```

### 步骤 6：自动修复 Bug

测试中发现问题时，立即定位并修复，修复完成后告知用户做了什么：

| 问题类型 | 自动修复策略 |
|---------|------------|
| 页面路由 404 | 检查路由配置，修复路由注册或路径拼写错误 |
| 页面响应含错误信息 | 查看响应内容，定位问题组件，修复代码 |
| 接口返回 500 | 查看后端日志，定位异常，修复代码 |
| 接口返回 403 | 检查超管文件权限项列表，补充缺失的权限项编码 |
| 接口返回 200 但 data 为空/null | 检查数据范围过滤逻辑，确认超管模式下数据范围是否为 All |
| 数据库查询报错 | 检查 SQL / ORM 语句，修复字段名、表名或语法错误 |
| 缺少菜单权限项管理导航入口 | 在导航菜单配置中添加菜单权限项管理的导航项 |
| 菜单权限项管理页面报错 | 定位报错组件，修复代码后回归 |
| 权限项列表接口无数据 | 检查查询逻辑，确认 `auth.config.json` 中的权限项定义可被正确读取 |
| 缺少推送按钮 | 在菜单权限项管理页面补充推送按钮及对应事件绑定 |

修复完成后，**立即对相关页面/功能重新执行步骤 5**，验证修复是否生效。

### 步骤 6：输出测试报告

所有页面测试完成（或多次修复后全部通过）后，输出汇总报告：

```
=== 页面测试报告 ===
测试时间：2026-04-16 10:00:00
测试页面数：4 个

页面              路由                      数据查询接口               状态
──────────────────────────────────────────────────────────────────────────
员工管理          /employee                 GET /api/employee/list    ✅ 通过
订单列表          /order                    GET /api/order/list       ✅ 通过
部门管理          /department               GET /api/dept/list        ✅ 通过（自动修复 1 次）

【菜单权限项管理专项】
检查项                              状态
──────────────────────────────────────────────────────────
导航菜单中存在入口                   ✅ 通过
管理页面可正常打开                   ✅ 通过
权限项列表接口返回数据               ✅ 通过
推送按钮存在（未触发）               ✅ 通过

测试结果：3/3 页面通过，菜单权限项管理 4/4 项通过 ✅ 全部通过。
```

**自动修复记录**（若有）：
```
[自动修复记录]
页面：部门管理
问题：GET /api/dept/list 返回 500，错误信息：Unknown column 'dept_code' in field list
修复：将字段名 dept_code 改为 department_code（来自步骤1扫描的真实字段名）
回归：修复后重新测试，返回 200，data 包含 12 条记录 ✅
```

### 步骤 7：循环直至全部通过

若仍有页面未通过，**继续修复 + 回归测试**，循环执行步骤 5-6，直至所有页面满足：
- 页面打开不报错（HTTP 200，响应中无明显错误信息）
- 数据查询接口返回数据（`data` 非空且非 null）

---

## 四、测试数据构造规则

### 正例数据构造

1. 从 MCP `hr-auth-copilot.execute`（`mysql_query` 查询 `v_ai_data_scope`）获取真实码值（如真实组织编码）
2. 从数据库查询确认该码值前缀下确实存在业务数据
3. 若无数据，换另一个码值重试，或告知用户数据库中缺少对应测试数据

### 反例数据构造（反例 2：有权限但无数据）

1. 从 MCP 获取真实码值列表
2. 选择一个**确认数据库中没有对应数据**的码值（或构造一个不存在的码值）
3. 确保是「无数据」而非「无权限」，避免混淆两种失败原因

### 「全部」特殊值处理

| 范围类型 | 全部特殊值 |
|---------|-----------|
| `Org` | `Org-All` |
| `WorkPlace` | `WorkPlace-All` |
| 其他 | `global` |

正例 2 必须使用全部特殊值，验证数据范围为「全部」时确实不过滤。

---

## 五、测试不通过时的分析提示

| 失败类型 | 可能原因 | 排查方向 |
|---------|---------|---------|
| 正例返回 403 | 权限项编码拼写错误 / 模拟数据注入未生效 | 检查权限项编码是否与 API 守卫中一致 |
| 正例返回 200 但数据不在范围内 | 数据范围过滤逻辑有误 / 字段映射配置错误 | 检查 `DATA_SCOPE_FIELD_MAP` 中表名和字段名 |
| 反例返回 200（应返回 403） | 路由守卫未生效 / 权限校验被跳过 | 确认 `checkPermission` 在数据查询前执行 |
| 反例 2 有数据（应为空） | 数据范围过滤条件未拼接 / SQL 条件被忽略 | 检查 `buildDataScopeWhere` 的返回值是否正确拼入 SQL |

---

## 六、MCP 工具

测试数据构造时调用：

| 查询目的 | SQL（通过 `hr-auth-copilot.execute` 的 `mysql_query` 命令执行） |
|---------|------|
| 获取全部数据范围类型 | `SELECT DISTINCT dim_type_code, dim_type_name FROM v_ai_data_scope ORDER BY dim_type_code` |
| 获取指定类型下的真实码值 | `SELECT dim_item_code, dim_item_parent_code, dim_item_name, dim_item_full_name FROM v_ai_data_scope WHERE dim_type_code = '<类型编码>'` |
