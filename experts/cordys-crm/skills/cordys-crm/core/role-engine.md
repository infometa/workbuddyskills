# 🧠 角色感知引擎

本文件定义了系统如何**自动发现用户身份**并匹配到正确的工作模式。
支持通过环境变量自定义角色映射，无需修改代码。

---

## 1. 初始化流程

每次对话开始（或 API Key 变更后），执行：

```
检查 Cordys.md 是否存在？
├─ 存在 → 验证有效性（确认非空、含必要字段）
│   ├─ 有效 → 加载角色上下文，进入交互
│   └─ 无效 → 重新执行初始化
└─ 不存在 →
    ├─ cordys.sh crm verify       验证 API Key
    ├─ cordys.sh crm whoami       获取用户信息 (GET /personal/center/info)
    ├─ 将结果写入 Cordys.md         持久化用户身份
    └─ 匹配角色，加载 profiles/{role}.md
```

**换账号 / 刷新身份**：用户说"刷新身份"或"换账号" → 重新执行上述流程，覆盖 Cordys.md。

> `Cordys.md` 位于 skill 根目录，由系统自动管理，请勿手动编辑。

---

## 2. 角色匹配规则

采用**两层匹配策略**：先尝试用户自定义映射，再 fallback 内置规则。

### 2.1 用户自定义角色映射（优先级最高）

如果 `.env` 中配置了 `ROLE_MAP` 环境变量，则优先使用：

```bash
# .env 配置示例
# 格式：岗位关键词|岗位关键词...=角色ID，多组用逗号或换行分隔
# 角色ID 必须对应 profiles/ 目录下已存在的 .md 文件（不含扩展名）

ROLE_MAP=总经理|副总裁|VP=executive,总监|经理=sales-manager,区域经理|城市经理=territory-manager,商务|合同管理=contract-admin,销售|顾问=sales,财务|会计|出纳=finance
```

AI 在启动时读取 `ROLE_MAP`，解析为映射表：

```python
# AI 内部解析逻辑（参考）
import os

ROLE_MAP = {}
raw = os.environ.get("ROLE_MAP", "")

for entry in raw.split(","):
    entry = entry.strip()
    if "=" not in entry:
        continue
    keywords, role_id = entry.rsplit("=", 1)
    for kw in keywords.split("|"):
        ROLE_MAP[kw.strip()] = role_id.strip()

# 匹配流程
def match_custom(positions, role_map):
    """按自定义映射匹配：返回第一个匹配的角色ID"""
    for kw in sorted(role_map.keys(), key=len, reverse=True):  # 长关键词优先
        if any(kw in pos for pos in positions):
            return role_map[kw]
    return None
```

> **为什么长关键词优先？** 比如同时有"经理"和"区域经理"，长关键词更精确。如果不追求层级可以省略排序。

### 2.2 内置角色映射（fallback）

当 `ROLE_MAP` 未设置或无匹配时，使用内置规则：

```python
fields = response.data

# 优先级 1：管理员（id=admin 或角色包含 admin）
if fields.id == "admin" or "admin" in str(fields.roles or ""):
    role = "sales-manager"  # 管理员默认按经理视角

# 优先级 2：高管岗（全公司视角，不限制部门）
elif any(kw in str(fields.position or "") for kw in 
         ["总经理","副总裁","VP","CEO","COO","CFO","总裁","合伙人","董事长"]):
    role = "executive"

# 优先级 3：管理岗（部门视角）
elif any(kw in str(fields.position or "") for kw in 
         ["经理","总监","主管","负责人","leader","部长","主任"]):
    role = "sales-manager"

# 优先级 4：财务岗
elif any(kw in str(fields.position or "") for kw in 
         ["财务","会计","出纳","财务经理","财务总监"]):
    role = "finance"

# 优先级 5：商务/合同岗
elif any(kw in str(fields.position or "") for kw in 
         ["商务","合同管理","合同专员","法务","合规","商务经理","商务总监"]):
    role = "contract-admin"

# 优先级 6：销售岗
elif any(kw in str(fields.position or "") for kw in 
         ["销售","BD","专员","顾问","业务员","运营"]):
    role = "sales"

# 兜底：无法识别时默认个人模式（防止权限扩散）
else:
    role = "sales"
```

> **匹配规则说明**：高管控（总经理/VP）优先于管理岗（经理/总监），避免误匹配。商务岗从销售岗独立出来。

### 2.3 从行为推断（软规则——仅内置规则使用）

如果 `position` 为空且自定义映射也未命中，按内置规则无法确认角色时，通过历史行为推断：

- 检查历史对话记录中最常查询的模块
- 频繁查 `contract/payment-plan`、`invoice`、回款 → 走财务视角
- 频繁查 `org`、`members`、跨部门数据 → 走经理视角
- 频繁查自己的 lead/opportunity → 走销售视角

此规则仅作为补充，不覆盖 position 匹配。

---

## 3. 自定义角色配置文件（profiles/{role}.md）

用户可以为任意角色创建自定义配置文件，只需在 `profiles/` 目录下新建 `{role}.md` 即可：

```bash
# 例子：创建一个 territory-manager 角色
# 1. 确认 ROLE_MAP 中已经把"区域经理"映射到 territory-manager
# 2. 创建 profiles/territory-manager.md
# 3. 在文件中定义核心关注、查询偏好、交互模式和异常预警
```

系统启动时自动扫描 `profiles/*.md` 获取可用角色列表。引用了不存在的角色 ID 会降级到 `sales` 角色。

---

## 4. Cordys.md 生命周期

### 创建
```markdown
# 🧠 用户身份上下文

> 自动获取：2026-05-09 10:30
> 匹配角色：sales-manager

## 身份信息
| 字段 | 值 |
|------|-----|
| 用户ID | admin |
| 姓名 | 张三 |
| 岗位 | 销售一部经理 |
| 邮箱 | zhang@company.com |
| 角色ID | sales-manager |
```

### 刷新条件
| 事件 | 动作 |
|------|------|
| 用户说"刷新身份" | 重新执行初始化 |
| 用户说"换账号" | 清除 Cordys.md + 重新初始化 |
| 连续 3 次 API 调用返回 401/403 | 提示用户检查密钥，建议刷新 |
| 从创建起超过 7 天 | 后台静默刷新（不打扰用户） |

### 约束
- `Cordys.md` 是运行时产物，**不提交版本控制**
- AI 每次对话第一件事：确认 Cordys.md 就绪且有效
- 如果 Cordys.md 存在但解析失败（格式损坏），视为不存在
