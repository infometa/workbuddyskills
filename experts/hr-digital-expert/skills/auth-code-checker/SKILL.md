---
name: auth-code-checker
description: >
  权限代码启动前检查 SKILL。在用户本地启动或重启项目前自动执行，
  检查权限中台集成的完整性，确保本地开发环境配置正确。
  触发时机：检测到以下任意情况时自动触发——
  启动命令：npm run dev、npm start、yarn dev、pnpm dev、node server、ts-node、next dev；
  重启场景：重启项目、重新启动、restart、重跑、kill 后重启；
  测试启动：npm test、npm run test、jest、vitest、启动测试、跑测试、run test；
  调试场景：debug 模式启动、本地调试、F5 启动；
  用户口语：开始预览、打开项目、运行项目、帮我启动、开启服务、把项目跑起来、打开预览看看、帮我运行一下项目、预览项目、把项目跑一下、帮我启动预览、开始运行、运行起来看看、启动项目、跑起来、起一下、run 起来、本地测试一下、看看效果、跑起来看看、开一下服务、起服务。
---
# 权限代码启动前检查

在项目启动前，快速扫描权限中台集成状态，确保本地开发所需的超管静态鉴权文件已就绪。**检查耗时极短，不影响启动流程。**

---

## 执行流程

### 第一步：判断项目是否集成了权限中台

扫描项目代码（后端目录），搜索是否存在对权限中台接口的调用：

- 搜索关键词：`/api/ai/auth/getUserOperations`
- 搜索范围：项目后端代码文件（`.ts`、`.js`、`.mjs` 等）

**判断结果**：

| 结果                 | 处理方式                                                             |
| -------------------- | -------------------------------------------------------------------- |
| **未找到**调用 | 输出「项目未集成权限中台，跳过检查」，**立即结束**，不阻塞启动 |
| **找到**调用   | 继续执行第二步                                                       |

---

### 第二步：读取系统编码（sysCode）

从后端代码根目录的 `.hrright/auth.config.json` 读取 `sysCode`：

```
后端根目录/.hrright/auth.config.json → 读取 sysCode 字段
```

若文件不存在或 `sysCode` 为空，输出警告并终止检查：

```
⚠️ 未找到 .hrright/auth.config.json 或 sysCode 为空。
   请先完成权限中台集成（执行 auth-code-developer SKILL），再启动项目。
```

---

### 第三步：判断运行环境

读取环境参数 `hrright_env`，判断当前环境：

```
process.env.hrright_env === 'prod'？
  ├─ 是 → 生产环境，输出「✅ 生产环境（hrright_env=prod），无需本地超管文件，跳过检查」，立即结束
  └─ 否 → 继续执行第四步（检查本地超管文件）
```

> **说明**：生产环境通过 docker 容器注入 `hrright_env=prod`，鉴权数据直接调用权限中台生产接口，不需要本地超管文件。

---

### 第四步：检查本地超管静态鉴权文件

基于 `sysCode`，构造本地超管文件路径：

```
~/.hrright/{sysCode}/local-permissions.json
~/.hrright/{sysCode}/local-data-scopes.json
```

跨平台路径规则（使用 `os.homedir()` 获取 Home 目录）：

| 系统    | 实际路径示例                                                   |
| ------- | -------------------------------------------------------------- |
| Windows | `C:\Users\{用户名}\.hrright\{sysCode}\local-permissions.json` |
| macOS   | `/Users/{用户名}/.hrright/{sysCode}/local-permissions.json`   |
| Linux   | `/home/{用户名}/.hrright/{sysCode}/local-permissions.json`    |

**检查两个文件是否均存在**：

- **均存在** → 输出「✅ 本地超管鉴权文件已就绪」，检查通过，允许启动
- **任一不存在** → 进入第五步，自动生成缺失的文件

---

### 第五步：自动生成缺失的超管静态鉴权文件

从项目代码中扫描所有权限项编码（搜索 `Menu_Page_` 和 `Menu_Button_` 前缀的字符串），以及 `auth.config.json` 中的 `permissions` 字段，收集完整的权限项列表。

**生成 `local-permissions.json`**（若不存在）：

```json
{
  "success": true,
  "code": "0",
  "msg": "success",
  "data": [
    "Menu_Page_Home",
    "Menu_Page_User_Management",
    "Menu_Button_User_Export"
    // ... 所有从代码中扫描到的权限项编码
  ]
}
```

**生成 `local-data-scopes.json`**（若不存在）：

对每个权限项，生成一条「全部」特殊值的数据范围条目：

```json
{
  "Menu_Page_User_Management": {
    "success": true,
    "code": "0",
    "msg": "success",
    "data": [
      {
        "authid": "local-dev",
        "roleCode": "superadmin",
        "dataScopes": {
          "Org": ["Org-All"],
          "WorkPlace": ["WorkPlace-All"]
        }
      }
    ]
  }
}
```

`dataScopes` 中需要包含哪些范围类型，从 `auth.config.json` 的 `permissions[].dataScopeType` 字段读取。若某权限项的 `dataScopeType` 为空数组，则 `dataScopes` 也为空对象 `{}`。

**生成完成后**：

```
✅ 已自动生成本地超管鉴权文件：
   📄 ~/.hrright/{sysCode}/local-permissions.json（包含 N 个权限项）
   📄 ~/.hrright/{sysCode}/local-data-scopes.json（包含 N 个权限项的数据范围）

💡 这些文件仅用于本地开发，不会被打包到部署包中。
   如需切换为真实权限中台鉴权，删除或重命名这两个文件即可。
```

---

## 输出规范

检查结束后，输出一行简洁的状态摘要，然后允许启动继续进行：

```
=== 权限代码启动前检查 ===
[状态] 检查通过 / 跳过 / 已修复
[耗时] Xms
继续启动项目...
```

**检查不应阻塞项目启动**：无论检查结果如何（通过、跳过、修复），都应在检查结束后允许启动命令继续执行。只有在发现严重配置错误（如 `auth.config.json` 缺失）时，才输出警告，但仍不强制阻止启动。
