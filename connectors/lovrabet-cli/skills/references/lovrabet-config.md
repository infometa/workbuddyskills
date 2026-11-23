# `.lovrabet.json` 配置参考

`.lovrabet.json` 保存用户凭证、默认应用偏好和连接设置。普通业务使用无需配置环境，沿用当前连接设置。AK 属于用户，不属于应用；默认 AppCode 是优先查询位置，不限制当前用户访问有权限的其他应用。

当前目录配置优先于全局配置；缺失字段再使用全局值。平台可见应用目录单独缓存在 `~/.lovrabet/cache/.../my-apps.json`。

首次使用可执行 `lovrabet config init` 配置全局节点。未执行时按默认中国大陆节点 `cn` 工作。

只自动读取 `.lovrabet.json`；`.lovrabetrc` 和其他 CLI 的配置文件不参与运行态配置发现。需要导入外部配置时，显式执行 `lovrabet app import --file <path>`。

## 默认应用配置（常用）

```json
{
  "appcode": "app-xxxxxxxx",
  "accessKey": "<ACCESS_KEY>"
}
```

## 按名称绑定应用

```json
{
  "accessKey": "<ACCESS_KEY>",
  "defaultApp": "crm"
}
```

`defaultApp` 是应用名称绑定：先匹配本地 `apps.<alias>.appcode`，未命中时通过 cache / remote 解析远端应用名。本地别名不代表平台应用目录或访问权限。

## 多应用名称配置（可选）

需要为多个应用保留本地名称时，使用 `apps + defaultApp`，不同时设置顶层 appcode：

```json
{
  "accessKey": "<USER_ACCESS_KEY>",
  "defaultApp": "crm",
  "apps": {
    "crm": { "appcode": "app-crm" },
    "erp": { "appcode": "app-erp" }
  }
}
```

默认先查 crm；`--app erp` 只切换目标 AppCode，继续使用同一用户 AK 与连接环境。连接与认证设置共享顶层配置，不在各应用下分别配置。

本地无需登记所有有权限的应用。Agent 可通过应用目录发现其他目标，用显式参数进行查询，不改写默认配置。

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
| `appcode` | string | — | 默认查询的 AppCode |
| `accessKey` | string | — | 当前用户的 User Access Key（client-ak） |
| `env` | string | `production` | 兼容连接设置，通常无需配置；保留已有值，不随应用切换 |
| `apps` | object | — | 本地应用名称到 appcode 的映射，不配置独立连接或凭证 |
| `format` | string | — | 默认输出格式：`json` / `pretty` / `compress` |
| `pageSize` | number | — | 默认分页大小 |
| `riskLevel` | string | `write` | 允许执行的最高风险等级 |
| `defaultApp` | string | — | 应用名称绑定 |
| `region` | string | `cn` | 当前开放的官方节点：`cn` / `id` / `global`；默认 `cn` 可省略 |
| `userDomain` | string | 节点内置值 | User 服务 HTTPS origin 覆盖 |
| `apiDomain` | string | 节点内置值 | 平台 API HTTPS origin 覆盖 |
| `runtimeDomain` | string | 节点内置值 | Runtime HTTPS origin 覆盖 |
| `skillDomain` | string | 节点默认 | SkillHub HTTPS origin 覆盖 |
| `kbServiceDomain` | string | 节点内置值（如有） | KB Service HTTPS origin 覆盖；仅无内置地址且无覆盖值时对应知识操作报错 |
| `harnessDomain` | string | 节点内置值（如有） | Harness 服务 HTTPS origin 覆盖 |

各 Domain 独立覆盖同名服务地址，官方配置和独立部署均采用相同的缺省规则。`config init` 中官方地区与企业 Domain 二选一；配置文件允许同时包含 `region` 和 Domain，服务地址按下方解析优先级确定。没有显式配置时，CLI 使用当前连接配置对应的内置节点；Indonesia 的最终服务地址统一使用 `*.lovrabet.id`。Personal KB 管理和知识搜索使用 `kbServiceDomain`，不从其他 Domain 推导；`--kb-service-url` 仅覆盖本次搜索。执行 `lovrabet doctor` 可查看当前实际生效的 Domain。

`config init` 的完整模式切换、独立部署 JSON 和校验规则见 [配置管理](lovrabet-config-commands.md#config-init--初始化连接配置)。

## 解析优先级

连接配置先合并再解析：项目配置覆盖全局同名字段；`routing` 对象整体替换，不逐项合并。

- 合并后存在 `routing` 时，`routing` 整体优先于顶层 Domain，缺省服务使用内置值，不回退到顶层 Domain。
- 没有 `routing` 时，使用顶层显式 Domain；API 地址依次读取 `apiDomain → host → 内置值`，SkillHub 地址依次读取 `skillDomain → skillHubDomain → agentDomain → platformDomain → 内置值`。这些字段为空字符串或 null 时读取下一项。
- `kbServiceDomain` 仅使用自身的非空字符串或内置值；`harnessDomain` 未配置时使用内置值，配置时必须为非空 HTTPS origin，不含凭据、路径、查询参数或片段。两者均不借用其他 Domain 或别名。
- 内置值由合并后的地区和连接设置决定；项目与全局均未配置 `region` 时使用 `cn`。请求失败不会切换地址。

- 凭证：`项目顶层 accessKey > LOVRABET_ACCESS_KEY > 全局顶层 accessKey`。应用选择不参与凭证解析。项目 accessKey 为 `""` 或 `null` 时仍屏蔽全局 AK，但允许环境变量提供凭证。
- 应用目标：`--appcode > --app > 项目 appcode > 项目 defaultApp > LOVRABET_APPCODE > LOVRABET_APP > 全局 appcode > 全局 defaultApp`。兼容字段 app 可用于直接指定 AppCode。
- 应用名称先匹配本地映射，再解析远端名称。项目默认应用存在时，环境变量不能覆盖它；选定名称无法解析时返回错误，不退到低优先级目标。
- 输出格式与分页选项依次使用命令支持的参数、对应环境变量、项目配置、全局配置、内置默认值。

项目声明 apps 时整体替换全局映射，不深度合并。CLI 不根据应用名称推断环境，不根据 AppCode 选择 AK，不在名称无法解析时猜第一个应用。

认证失败返回原始错误，不换 AK 或环境重试。普通业务命令不提供通用 `--access-key`；`auth login --access-key` 用于保存用户凭证。

## 默认应用与其他应用

`appcode` 是常用默认目标。`defaultApp` 提供按名称选择的方式，可指向本地名称或远端应用名；未传本次应用参数时，项目默认应用优先于环境变量和全局配置。

Agent 先查默认应用，没有合理匹配且用户未限定应用范围时，可通过 `app list` 发现当前用户有权限的其他应用。切换应用使用本次参数，不要求修改配置。权限错误不触发这种扩展查找。

用户明确要求记住默认目标时，才通过 `workspace init/use` 建立或修改绑定。

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
- 标量字段：当前目录配置覆盖全局级；项目顶层空值屏蔽全局顶层值
- `defaultApp`：当前目录显式声明 > 全局 `defaultApp`
- `apps`：当前目录显式声明时整体覆盖全局 `apps`；当前目录未声明时使用全局 `apps`
- `inherit` 不是受支持的配置项；旧字段会被忽略，可用 `lovrabet config delete inherit` 清理

因此，`lovrabet config init` 固定更新全局连接配置；当前目录文件中的兼容路由字段仍可能覆盖全局同名字段。初始化后可执行 `lovrabet doctor` 查看最终生效值。

已有顶层连接配置继续生效；绑定或切换应用无需重写它，riskLevel 与自定义 Domain 保留。

## 示例

### 全局 AK + 默认应用

```json
{
  "accessKey": "<ACCESS_KEY>",
  "defaultApp": "crm"
}
```

### 当前目录名称绑定

```json
{
  "defaultApp": "crm"
}
```
