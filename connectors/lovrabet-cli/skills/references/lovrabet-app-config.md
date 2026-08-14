# app-config — 运行态 app-config value 查询

按当前应用和配置 key 读取运行态 app-config value。

app-config 用于应用维度的运行态配置管理。`app-config get` 直接输出 value，返回值可能包含敏感信息。

## app-config get

```bash
lovrabet app-config get <key>
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `<key>` | string | 是 | app-config key |

**风险等级**：`read`

**输出**：`data` 为 value 的具体结果：

```json
{
  "ok": true,
  "command": "lovrabet app-config get",
  "risk": "read",
  "data": "example-value"
}
```

## 边界

- `lovrabet app-config get` 不支持 `--reveal`，命令直接输出 value。
- `lovrabet` 不提供 app-config 的 set/delete/list 管理入口。
- 不要把 app-config value 写入 `.lovrabet.json`、缓存、日志、命令参数或业务 Skill 入参。
- 输出可能是敏感值，Agent 只在用户明确要求查询指定 key 时执行。
- 示例 key 仅用于说明；实际执行必须使用调用方明确给出的 key，不能猜测、按 tags 查找或默认使用示例 key。
- Agent 执行 Skill 需要 value 时也调用该 CLI，不创建或复用取配置 BFF。
- value 只在当前任务内消费；除非用户明确要求查看，最终答复默认不重复展示。

## 示例

```bash
lovrabet app-config get example_api_key --format compress
```

若 key 不存在、当前 AK 无权限或运行态只读接口不可用，命令会返回错误。错误排查只基于 key、appCode、traceId 等定位信息，不应要求用户提供或回显明文 value。

## 参考

- [SKILL.md](../SKILL.md)
- [lovrabet-output-format-jq.md](lovrabet-output-format-jq.md)
