# 故障排除指南

## Skill 调用失败排查

1. **检查名称**: 确保调用名为 `lingxi-financialsearch-skill`
2. **检查位置**: 确认 SKILL.md 位于正确的 Skill 目录中
3. **API Key 过期**: 观察是否收到 4xx 错误，删除 `./gtht-skill-shared/gtht-entry.json` 后执行 `node skill-entry.js authChecker auth`
4. **Windows 特殊处理**: 确保 `node` 在 PATH 中

## 常见问题速查

| 错误现象 | 可能原因 | 解决方案 |
| --- | --- | --- |
| "Skill not found" | 名称错误或未安装 | 核对名称并检查安装目录 |
| 授权失败 | 未授权或过期 | 执行 `node skill-entry.js authChecker auth` |
| "401 Unauthorized" | Key 过期 | 系统将自动重触发授权流程 |
| "找不到模块" | Node.js 环境异常 | 检查 Node.js 安装，重新安装依赖 |
| 返回数据为空 | 股票代码错误或暂无数据 | 检查股票代码是否正确，或该股票暂无相关数据 |
| API Key 无效或已被禁用 | 客户停用 API Key | 删除 `./gtht-skill-shared/gtht-entry.json`，重新走授权流程 |

## Windows PowerShell 兼容性

Windows PowerShell 不支持 `&&` 作为命令分隔符，**必须使用 `;`**。

Windows PowerShell 与 Unix/Linux 命令不兼容，**禁止在 PowerShell 环境中使用 Unix 特有命令**：

| 禁止使用 | 正确替代 | 说明 |
| --- | --- | --- |
| `test -f <path>` | `Test-Path <path>` | Unix 文件测试命令，PowerShell 不识别 |
| `ls` | `Get-ChildItem` 或 `dir` | Unix 目录列表命令 |
| `cat <file>` | `Get-Content <file>` | Unix 文件读取命令 |
| `grep <pattern> <file>` | `Select-String <pattern> <file>` | Unix 文本搜索命令 |
| `rm <file>` | `Remove-Item <file>` | Unix 文件删除命令 |
| `cp <src> <dst>` | `Copy-Item <src> <dst>` | Unix 文件复制命令 |
| `mv <src> <dst>` | `Move-Item <src> <dst>` | Unix 文件移动命令 |
| `mkdir -p <path>` | `New-Item -ItemType Directory -Path <path>` | Unix 创建目录命令 |
| `which <cmd>` | `Get-Command <cmd>` | Unix 命令路径查询 |
| `kill <pid>` | `Stop-Process -Id <pid>` | Unix 进程终止命令 |

**检查文件是否存在（正确方式）：**

```powershell
# ✅ 正确（PowerShell 原生）
if (Test-Path "C:/Users/.../gtht-entry.json") { "EXISTS" } else { "NOT_FOUND" }

# ❌ 错误（Unix 命令，PowerShell 不识别）
test -f "C:/Users/.../gtht-entry.json"
```
