# workspace — 工作目录配置

`workspace` 用来给**当前工作目录**绑定默认应用。适合 WorkBuddy、Agent 项目目录、客户交付目录这类“打开一个目录就知道默认操作哪个应用”的场景。

它解决的是本地使用体验，不是平台权限配置：

- 配置文件固定写到当前目录的 `.lovrabet.json`
- 不写 AccessKey
- 不同步远端应用目录
- 不影响其他目录

## 命令

```bash
lovrabet workspace init --appcode <appcode> [--env daily]
lovrabet workspace init --app <name> [--env daily]
lovrabet workspace use --appcode <appcode> [--env daily]
lovrabet workspace use --app <name> [--env daily]
```

`init` 和 `use` 对应不同的目录生命周期：

- `init`：只为尚未绑定应用的目录建立 Lovrabet 应用上下文；已有绑定时停止并提示使用 `use`
- `use`：只修改已有应用绑定；尚未绑定时停止并提示先使用 `init`

状态判断只读取当前目录 `.lovrabet.json`，不会把全局配置中的应用选择当作当前目录已经初始化。只有顶层非空 `appcode`，或 `defaultApp` 指向有效的 `apps.<name>.appcode`，才算已有活动绑定；旧字段、未选中的 alias 和无效 `defaultApp` 不算绑定。配置文件只包含 `format`、域名等非应用字段时，仍可执行 `init`。

## 参数

| 参数 | 说明 |
|------|------|
| `--app <name>` | 应用名称。CLI 会用当前 AK 在指定环境的已发布应用列表中解析 appcode |
| `--appcode <code>` | 直接写入 appcode，不需要远端查询 |
| `--env <env>` | 可选。写入当前目录配置，取值为 `production` / `development` / `daily` |

必须且只能传 `--app` 或 `--appcode` 之一。

## 写入效果

直接用 appcode：

```bash
lovrabet workspace init --appcode app-64e32817 --env daily
```

当前目录 `.lovrabet.json`：

```json
{
  "env": "daily",
  "appcode": "app-64e32817"
}
```

用业务名称绑定默认应用：

```bash
lovrabet workspace use --app crm --env daily
```

当前目录 `.lovrabet.json`：

```json
{
  "env": "daily",
  "defaultApp": "crm",
  "apps": {
    "crm": {
      "appcode": "app-64e32817"
    }
  }
}
```

## 注意事项

- 不要主动创建或修改工作目录配置；只有用户明确要求“初始化当前目录”“记住这个应用”“绑定这个工作目录”等语义时，才执行 `workspace init/use`
- 执行前先判断当前目录状态：没有应用绑定用 `workspace init`，已有应用绑定用 `workspace use`
- 如果连续多次在同一目录使用同一个 app 或 appcode，可以提醒用户是否要写入当前目录 `.lovrabet.json`，但必须先得到明确同意
- `--app <name>` 需要当前已有合法 AccessKey，因为 CLI 要查询当前 AK 可见的应用列表
- 未发布应用不能被绑定为工作目录默认应用
- 如果只是临时执行一次命令，优先直接在目标命令上传 `--app` 或 `--appcode`
