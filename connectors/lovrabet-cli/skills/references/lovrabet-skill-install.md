# skill install

安装当前应用、当前租户可生效的业务 Skill。默认安装到用户级 Agent Skill 目录，让本机 Agent 可发现并使用这些业务 Skill；也可以显式安装到当前项目。

## 用法

```bash
lovrabet skill install [--scope all|personal|company] [--code <skillCode>] [--project]
lovrabet skill install --project
```

## 说明

- 需要 AccessKey 和 App Code。
- 默认等价于 `--scope all`，安装当前应用下当前用户可见的 personal/company 业务 Skill。
- 默认将有效 Skill 链接到用户级 Agent Skill 目录，并保留 `<appCode>--<skillCode>` 名称，避免不同应用同名 Skill 冲突。
- 只有明确需要绑定当前项目时才传 `--project`；项目链接写入当前工作目录的 `.agents/skills/<skillCode>`，适合 `/workspace/<appCode>` 这类一应用一项目目录。
- 用户级与项目级安装可以共存；显式项目安装不会删除已有用户级链接，也会保留这些链接仍在引用的缓存。
- 项目安装会拒绝覆盖 `lovrabet`、`runtime-observe`、`secret-retriever` 等平台保留 Skill 名称。
- personal 与 company 出现同一 `skillCode` 时，personal 版本生效。
- `--scope personal` 只安装个人业务 Skill；`--scope company` 只安装公司业务 Skill。
- `--code` 只安装指定业务 Skill，并清理该 code 对应的失效链接或 cache。
- 安装产物面向 Agent 消费，不建议直接编辑；新建或修改业务 Skill 时使用 `lovrabet skill create` / `lovrabet skill validate` / `lovrabet skill push --diagram-file <mermaid-file>`。
- 下载缓存仍保存在 `~/.lovrabet/cache/<env>/<ak_fingerprint>/skills/<appCode>/...`，不会复制到项目目录。

## CLI Built-in Skill

`lovrabet skill install` 仅安装当前应用的业务 Skill。CLI Built-in Skill 已包含在当前 npm 包内，并在安装或升级 CLI 时自动安装。诊断显示缺失、版本不一致或内容不一致时，使用当前包内的确定版本修复：

```bash
lovrabet cli-skill install
```

该命令只使用已校验的包内目录；外部 `skills` CLI 负责把它安装到 Agent 可发现的位置。失败时根据稳定错误码处理网络、权限或安装目标问题，再重试同一命令。
