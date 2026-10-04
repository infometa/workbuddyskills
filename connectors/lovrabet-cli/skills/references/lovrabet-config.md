# `.lovrabet.json` 配置参考

`.lovrabet.json` 现在只承载**用户意图配置**，不再承载平台应用目录。

这意味着：
- `accessKey` / `format` / `riskLevel` / `defaultApp` 等仍然放在 `.lovrabet.json`
- 当前 AK 在平台上可见的应用列表，放在 `~/.lovrabet/cache/.../my-apps.json`
- 首次使用推荐执行 `lovrabet config init` 配置全局节点。未执行时仍按默认中国大陆节点 `cn` 工作

只自动读取 `.lovrabet.json`；`.lovrabetrc` 和其他 CLI 的配置文件不参与运行态配置发现。需要导入外部配置时，显式执行 `lovrabet app import --file <path>`。

## 单应用模式

```json
{
  "appcode": "app-xxxxxxxx",
  "accessKey": "<ACCESS_KEY>"
}
```

## 默认应用模式

```json
{
  "accessKey": "<ACCESS_KEY>",
  "defaultApp": "crm"
}
```

`defaultApp` 现在只表示“没有更明确 app 线索时的默认候选远端应用名”。真正的应用目录来自 cache / remote，不再在本地维护 `apps.*` overrides。

## app cache

平台应用列表缓存路径：

```text
~/.lovrabet/cache/.../my-apps.json
```

这个 cache 由以下命令维护：
- `lovrabet app list`
- `lovrabet app list --no-cache`
- `lovrabet app pull`

## 顶层字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `appcode` | string | — | 兼容单应用模式，直接指定 appcode |
| `accessKey` | string | — | User Access Key（client-ak） |
| `format` | string | — | 默认输出格式：`json` / `pretty` / `compress` |
| `pageSize` | number | — | 默认分页大小 |
| `riskLevel` | string | `write` | 允许执行的最高风险等级 |
| `defaultApp` | string | — | 默认候选应用名称 |
| `region` | string | `cn` | 当前开放的官方节点：`cn` / `id` / `global`；默认 `cn` 可省略 |
| `userDomain` | string | 节点内置值 | User 服务 HTTPS origin 覆盖 |
| `apiDomain` | string | 节点内置值 | 平台 API HTTPS origin 覆盖 |
| `runtimeDomain` | string | 节点内置值 | Runtime HTTPS origin 覆盖，包含 Personal KB 管理 |
| `skillDomain` | string | 节点默认 | SkillHub HTTPS origin 覆盖 |
| `kbServiceDomain` | string | 官方目录（如有）；独立部署无 | KB Service HTTPS origin 覆盖；无法解析有效地址时搜索报错 |

各 Domain 独立覆盖同名服务地址。没有显式配置时，CLI 按 `region` 和 `env` 使用内置节点；Indonesia 的最终服务地址统一使用 `*.lovrabet.id`。`development` 与 `daily` 使用当前节点的 daily 层级；该层级缺失时按既有规则使用同节点 production。Personal KB 管理走 Runtime；知识搜索只使用专用 `kbServiceDomain`，或本次调用的 `--kb-service-url` 覆盖，不从其他 Domain 推导。执行 `lovrabet doctor` 可查看当前实际生效的 Domain。

`config init` 的完整模式切换、独立部署 JSON 和校验规则见 [配置管理](lovrabet-config-commands.md#config-init--初始化连接配置)。

## 解析优先级

```
CLI flag (--appcode, --format, --app ...)
  ↓
环境变量 (LOVRABET_APPCODE, LOVRABET_FORMAT ...)
  ↓
当前目录 .lovrabet.json（兼容本地配置）
  ↓
全局级 ~/.lovrabet.json
  ↓
内置默认值
```

## 关于 `defaultApp`

`defaultApp` 仍然是本地配置字段，但它现在只表示默认候选的远端应用名称。

所以：
- 通过 `workspace init/use --app <name>` 建立或修改命名绑定时会写入 `defaultApp`
- 运行时通过 cache 解析对应 `appcode`
- Agent 场景中，`defaultApp` 是第一个验证候选；用户未指定 app 时先查默认候选的数据集，验证不成立再扩大到应用列表

## 环境变量

| 环境变量 | 对应字段 |
|----------|----------|
| `LOVRABET_APPCODE` | `appcode` |
| `LOVRABET_ACCESS_KEY` | `accessKey` |
| `LOVRABET_FORMAT` | `format` |
| `LOVRABET_PAGE_SIZE` | `pageSize` |
| `LOVRABET_VERBOSE` | verbose |
| `LOVRABET_APP` | 当前应用名 |

## 查找与合并

| 作用域 | 查找目录 | 文件名优先级 |
|--------|---------|------------|
| 当前目录 | `process.cwd()` | 仅 `.lovrabet.json` |
| 全局级 | `~` | 仅 `.lovrabet.json` |

合并策略：
- 标量字段：当前目录配置覆盖全局级
- `defaultApp`：当前目录显式声明 > 全局 `defaultApp`
- `apps`：当前目录显式声明时整体覆盖全局 `apps`；当前目录未声明时使用全局 `apps`
- `inherit` 不是受支持的配置项；旧字段会被忽略，可用 `lovrabet config delete inherit` 清理

因此，`lovrabet config init` 固定更新全局连接配置；当前目录文件中的兼容路由字段仍可能覆盖全局同名字段。初始化后可执行 `lovrabet doctor` 查看最终生效值。

## 示例

### 全局 AK + 默认应用

```json
{
  "accessKey": "<ACCESS_KEY>",
  "defaultApp": "crm"
}
```

### 当前目录默认候选（兼容场景）

```json
{
  "defaultApp": "crm"
}
```
