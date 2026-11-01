# version

查看本机 CLI 版本，或对照官网 Skill zip 检测是否有更新。不安装、不覆盖二进制。

## 用法

```text
reelmate --version
reelmate version check [--json]
```

## 子命令说明

| 命令 | 作用 |
|---|---|
| `reelmate --version` | 打印本机版本；缓存过期时可能在 stderr 提示官网新版本 |
| `reelmate version check` | 立即探测官网 Skill zip，报告是否需要按安装原话升级 |

## `reelmate --version`

### 作用

打印本机已安装的 CLI 版本字符串。不访问网络；当本地缓存认为官网 Skill 可能有新版本时，可能在 stderr 提示升级，但不改变 stdout 的版本行。

### 参数

无子命令参数。全局 `--json` 不适用本入口。

### 输出

单行版本号（与 `reelmate-cli-skill/VERSION` 及发版 CLI 对齐）。

### 示例

```bash
reelmate --version
```

## `reelmate version check`

### 作用

下载官网固定地址的 Skill zip，只在内存读取 `INSTALL.md` 钉死版本，与本机 `reelmate --version` 比较。有更新时打印与自动提示相同的官网安装原话。不要执行 `npm update`，不要安装 `@latest`。看到更新后，先完成本轮付费写，再按该原话重做 `INSTALL.md`。

### 参数

- `--json`：输出 JSON。`data` 含 `current`、`latest`、`update_available`、`skill_zip_url`、`agent_install_line`。

### 输出

成功时人读文本为安装原话或「当前已是最新版本」。失败时非 0，并走标准错误 envelope。

## 注意事项

- `version check` 只报告是否需要升级，不安装、不覆盖二进制，也不替换 Skill 目录；升级动作按 zip 内 `INSTALL.md` 与 [SKILL.md](../SKILL.md)「准备」段执行。
- 看到更新提示时先完成本轮付费写操作，再重装；不要用 `npm update` 或 `@latest` 代替钉死版本安装原话。
- `--json` 的 `agent_install_line` 等人读安装句可原样交给用户，但不要在其中夹带凭据或内部路径。
