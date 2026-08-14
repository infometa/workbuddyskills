# doctor — CLI 与 Built-in Skill 诊断

`lovrabet doctor` 是本地只读诊断命令，用于查看 CLI、Node.js、配置、服务树和 Built-in Skill 状态。

```bash
lovrabet doctor
```

Built-in Skill 区域显示 npm package version、已安装 Skill version、实际路径和状态：

| 状态 | 含义 |
| --- | --- |
| `current` | 版本与包内内容摘要一致 |
| `missing` | Agent Skill 目录中未找到 `lovrabet` |
| `version_mismatch` | 已安装 Skill 与当前 CLI 包版本不同 |
| `content_mismatch` | 版本相同但文件清单或摘要不同 |
| `unverifiable` | 包内源、安装路径或文件无法安全校验 |

状态不是 `current` 时，先按 `Reason` 处理文件、网络或权限问题，再执行：

```bash
lovrabet cli-skill install
lovrabet doctor
```

`doctor` 不修改配置、不安装 Skill，也不替代业务命令的认证和权限检查。
