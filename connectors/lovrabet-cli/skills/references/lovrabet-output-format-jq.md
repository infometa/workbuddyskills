# 输出格式与全局 `--jq`

运行态 `lovrabet` 的声明式命令统一支持**结构化输出**、**compress 默认偏好**和**全局 `--jq`**。

## `--format`

| 值 | 说明 |
|----|------|
| `json` | 缩进 JSON，信封 `{ ok, command, risk, data?, ... }` |
| `compress` | 与 `json` 同一信封，**单行**紧凑，适合 Agent / 管道 |
| `pretty` | 人类可读（非 JSON 信封的展示型输出，依命令而定） |

解析顺序：**CLI `--format`** > 配置文件 `format` > 默认（产品默认多为 **compress**，以当前 CLI 版本 `--help` 为准）。

## 结构化输出契约

- `json` / `compress` 只输出机器可读信封，不携带运行时升级提示等交互式 notice。
- 升级提示只在交互式 `pretty` 输出中写入 stderr，不污染 stdout。
- 自动化脚本不要依赖 `_notice.update`；需要主动升级时显式执行 `lovrabet update`。

## 全局 `--jq '<expr>'`

- **作用**：在**最终要打印的整段 JSON 字符串**上执行 **jq** 表达式（与手动 `… \| jq '<expr>'` 一致）。
- **适用**：仅当本次输出走 **`--format json` 或 `compress`** 时；若当前为 `pretty` 且你传了 `--jq`，管线会将格式**升格为 json** 再跑 jq。
- **信封**：表达式作用在**完整信封**上，取业务数据多用 **`.data…`**（例如 `.data.items`、`.data.datasets[]`）。
- **二进制**：按 **`JQ_PATH` → CLI 内置 sidecar jq → `PATH` 上的 jq** 的顺序解析。若显式设置了 **`JQ_PATH`**，它必须指向一个真实可执行文件；否则命令会直接报错，不会静默回退。

## 示例

```bash
# 列表只取必要字段（compress + jq）
lovrabet dataset list --format compress --jq '.data.datasets[] | {code, name}'

# 数据集详情：投影 data 段（json）
lovrabet dataset detail --code <数据集编码> --format json --jq '.data | {fields, operations: [.operations[].name]}'
```

## 不适用 `--jq` 的命令

声明式命令里若 **`hasFormat: false`**（例如 `lovrabet doctor`），输出由命令自控，**不参与**上述 `--format` / `--jq` 管线，传 `--jq` 无意义。
