# update — 一体更新 CLI 与 Built-in Skill

`lovrabet update` 从 npm registry 查询 CLI 包的 dist-tags，不依赖 CDN 配置文件。CLI 与 Built-in Skill 一体升级，不提供拆分升级模式。

默认升级入口是 `lovrabet update`；beta 预览和精确版本复现才使用对应选项。

## 命令

```bash
# 默认等价于 --latest
lovrabet update

lovrabet update --latest
lovrabet update --beta
lovrabet update --version <version>
```

`--latest`、`--beta`、`--version <version>` 互斥；精确版本必须是完整 semver，例如 `2.1.23` 或 `2.2.0-beta.1`。

## 行为

- npm 安装包携带同版本 Built-in Skill，安装阶段自动完成 Agent Skill 安装。
- CLI 升级成功后，旧进程只验证目标版本 Skill 是否已安装，不使用旧包内容重复覆盖。
- CLI 已经是目标版本时，命令从当前 npm 包内检查并修复 Built-in Skill。
- Skill 缺失、版本不一致或验证失败时，命令返回失败并提示 `lovrabet cli-skill install`；不要把“CLI 包已更新”误报为完整成功。
- `lovrabet skill install` 仍只管理当前应用的业务 Skill，与 Built-in Skill 生命周期相互独立。

手动复现或修复 npm 安装问题时，可以使用：

```bash
npm install -g @lovrabet/lovrabet-cli@<version>
lovrabet doctor
lovrabet cli-skill install
```
