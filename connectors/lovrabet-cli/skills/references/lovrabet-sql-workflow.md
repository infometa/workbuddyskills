# Custom SQL 查询工作流

查看和执行 Custom SQL。Custom SQL 在 Lovrabet 平台上创建，CLI 用于查看详情和执行。

## 前置条件

- `sql detail` 和 `sql exec` 使用当前 CLI 认证，默认推荐 **accessKey（client-ak）**

## 先判断 app 是否明确

`sql` 命令组也不要默认先查 app。

### 可以直接进入 Detail 的场景

以下情况直接进入 `sql detail`，但不能跳过契约与数据范围核对：

- 用户已经给了 `--appcode`
- 用户已经给了 `--app <name>`
- 当前问题明显沿用上文已确认的同一 app 上下文
- 用户明确说“当前应用”“默认应用”，且没有新的业务域线索

`defaultApp` 只是默认候选。Custom SQL 可能按业务域分布在不同 app 中；用户提到新的业务域且未指定 app 时，先把 `defaultApp` 当第一个候选验证，验证不成立再扩大到应用列表。

### 需要先做应用决议的场景

以下情况才扩大到 `lovrabet app list`：

- 用户只给了业务需求，没有明确说明是哪个应用里的 Custom SQL
- 当前没有显式 `--appcode` / `--app`，且需求包含业务域线索
- 同一类业务可能落在多个 app 中
- 已经把 `defaultApp` 作为候选检查过，但无法确认它承载本次 Custom SQL

推荐方式：

1. 有 `defaultApp` 时，先把它作为第一个候选
2. 无法确认默认候选承载本次 Custom SQL 时，再 `lovrabet app list`
3. 用业务关键词选 1-2 个候选 app
4. 从业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选定位 Custom SQL；无法唯一定位时停止，不猜测
5. 再回到 `lovrabet sql detail`；契约、参数和数据范围核对通过后才执行 `sql exec`

## sql detail — 查看 Custom SQL 详情

```bash
lovrabet sql detail --sqlcode <code>

# 返回原始完整 API 响应
lovrabet sql detail --sqlcode <code> --verbose
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--sqlcode` | string | **是** | Custom SQL 标识字段 `sqlCode`，格式：`xxxxxxxx-xxxxxxxx`（8 位 hex + 8 位 hex） |
| `--verbose` | boolean | 否 | 返回完整原始对象 |

**输出**：Custom SQL 名称、SQL 内容和关联的数据库等。

Custom SQL 只有在标识来源可信、所属应用匹配且 Detail 实际返回的名称、数据库和 SQL 内容与当前任务一致时，才作为稳定查询规则复用。`sql detail` 不单独提供参数约束或副作用契约；缺失信息仍视为未知。Custom SQL 已存在或 `detail` 成功本身不代表业务口径正确，也不代表已经获得执行授权。

SQL 内容属于敏感实现资产。当前 `sql detail` 会按真实接口返回 SQL 内容，Agent 只用于当前任务的契约核对，不写入 KB、业务 Skill、日志或全量规则目录，最终答复默认不回显；用户明确要求查看时，也只能在服务端授权成功后按最小必要范围展示。不提供 `sql list` 只能降低批量枚举和暴露面，不能替代服务端资源级授权；`detail` 与 `exec` 仍需按当前 AK、应用和具体 Custom SQL 独立鉴权，知道或猜到 `sqlCode` 不代表有权查看或执行。

## sql exec — 执行 Custom SQL

```bash
# 无参数执行
lovrabet sql exec --sqlcode <code>

# 带参数执行
lovrabet sql exec --sqlcode <code> --params '{"status":"active"}'
```

| Flag | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--sqlcode` | string | **是** | Custom SQL 标识字段 `sqlCode`，格式：`xxxxxxxx-xxxxxxxx` |
| `--params` | string | 否 | 查询参数，JSON 格式 |

**CLI 风险元数据**：`read`。这只反映命令注册，不代表真实副作用。Custom SQL 可能包含业务写入、`DROP`、`TRUNCATE` 等破坏性语句；执行前必须核对 SQL 内容、权限和用户授权，副作用不明确时不自动执行。

**输出**：查询结果数据，格式由 `--format` 控制。

## 典型工作流

```bash
# 0. 如果默认候选验证不成立，再看应用目录
lovrabet app list

# 1. 如果不知道 sqlCode，从业务 Skill、可信 Service Tree、
#    前序已确认上下文或可信 KB 候选定位；无法唯一定位时停止

# 2. 查看 Custom SQL 详情，核对名称、数据库和 SQL 内容
lovrabet sql detail --sqlcode 2305f915-dd48cd4c

# 3. 核对契约、参数和数据范围后执行 Custom SQL
lovrabet sql exec --sqlcode 2305f915-dd48cd4c --params '{"status":"active"}'

# 4. 指定 JSON 格式输出，便于程序解析
lovrabet sql exec --sqlcode 2305f915-dd48cd4c --params '{"status":"active"}' --format json
```

## 注意

- Custom SQL 标识字段 `sqlCode` 的格式为 `{8位hex}-{8位hex}`，如 `2305f915-dd48cd4c`
- `--params` 必须是合法 JSON 字符串
- `lovrabet` 没有 `sql list` 命令；`sqlCode` 必须来自用户明确输入、业务 Skill、可信 Service Tree、前序已确认上下文或可信 KB 候选
- 运行态发现业务能力，不枚举 Custom SQL 实现资产；基础事实查询优先使用已治理 Dataset，稳定规则由业务 Skill 或可信 Service Tree 绑定到已发布 Custom SQL
- 不知道 `sqlCode` 时不猜测，也不从 Dataset 原始字段重写已有稳定规则
- 当业务归属不清时，先验证 `defaultApp`；验证不成立再 `app list` 做应用决议，再去确认 `sqlCode`，而不是直接盲猜当前 app

## 参考

- [SKILL.md](../SKILL.md)
- [instant-api-workflow.md](instant-api-workflow.md)
