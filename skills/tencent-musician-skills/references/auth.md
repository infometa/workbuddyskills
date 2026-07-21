# 登录态管理（内嵌能力）

> 本 Skill 已自包含登录能力，**不依赖任何外部 Skill**，调用方无需设置任何环境变量。首次使用会自动弹出浏览器扫码登录，Token 有效期约 30 天，之后日常调用秒级无感。

## Token 获取的自动回退链

所有调用脚本在发起请求前，会通过内部模块 `scripts/_token.py` → `scripts/check_login.py` **自动获取 Token**，四级回退：

```
1. 本地缓存 ~/.tme-login/token.json              ← 秒级，99% 日常场景
       ↓（不存在或为空）
2. 无头 Playwright + ~/.tme-login/storage_state.json 刷新
       ↓（storage_state 失效或缺失）
3. 自动调起 login.py 做有头扫码登录（弹出 Chromium）
       ↓（用户未完成登录）
4. 手动粘贴 Token 兜底
```

每一步成功都会覆盖写入 `token.json`，供后续调用秒级复用。**Token 有效期约 30 天**。

## 双文件缓存

| 文件                                    | 作用                                                              |
| --------------------------------------- | ----------------------------------------------------------------- |
| `~/.tme-login/storage_state.json`       | Playwright 完整存档（cookies + localStorage），由 `login.py` 生成 |
| `~/.tme-login/token.json`               | `tmeHeaderToken` 快照，供 Skill 内部和外部脚本直接读取            |

## Playwright 依赖（🤖 AI 必读：缺失时自动安装，不要把错误丢给用户）

本 Skill 依赖 [Playwright](https://playwright.dev/python/) 驱动 Chromium 完成登录与 Token 刷新。

### 脚本层已自动处理

`scripts/login.py` 与 `scripts/get_token_from_browser.py` 在运行时会**自动检测 Playwright 是否已安装**，若未安装会**自动在当前 Python 环境下执行安装**（`pip install playwright` + `playwright install chromium`），无需人工干预。正常情况下，AI 和用户都**不需要手动装依赖**，直接调用脚本即可。

### ⚠️ 强制行为规范（给调用本 Skill 的 AI）

当你（AI）运行本 Skill 的任何脚本，**看到以下任一信号时**：

- 脚本 stderr 出现 `❌ 未检测到 Playwright` / `PLAYWRIGHT_MISSING` / `ModuleNotFoundError: No module named 'playwright'`
- 提示「请安装依赖：pip install playwright && playwright install chromium」
- `check_login.py` 因 `PLAYWRIGHT_MISSING` 走到手动粘贴兜底

**你必须立刻在终端主动执行下面的安装命令，然后重跑原脚本**，而不是把错误提示原样抛给用户、让用户自己去装：

```bash
python3 -m pip install --upgrade playwright
python3 -m playwright install chromium
```

说明：
1. 使用 `python3 -m pip` / `python3 -m playwright`，避免 `pip` / `playwright` 不在 PATH 里导致的误判
2. 若当前处于虚拟环境或 conda 环境，继续在该环境中执行即可，**不要**切换到系统 Python
3. `playwright install chromium` 会下载约 150MB 浏览器二进制，首次耗时 1-2 分钟是正常的
4. 安装完成后**必须重新执行**原本失败的脚本（例如 `python3 scripts/login.py` 或上层的 `check_login.py`），确认流程能走通再向用户汇报
5. **禁止**向用户输出"请你先执行 pip install ..."这类把安装动作甩回给用户的话

> Chromium 约 150MB，仅本 Skill 使用，不影响系统浏览器。

## 登录相关脚本（普通调用方不需要直接用）

| 功能                                      | 脚本                                   | 典型用法                                 |
| ----------------------------------------- | -------------------------------------- | ---------------------------------------- |
| 首次登录 / 扫码登录（有头）               | `scripts/login.py`                     | `python scripts/login.py`                |
| 获取登录态（缓存→无头→扫码 自动回退）     | `scripts/check_login.py`               | `TOKEN=$(python scripts/check_login.py)` |
| 从 storage_state 无头读取 Token（内部）   | `scripts/get_token_from_browser.py`    | 由 `check_login.py` 调用                 |
| 验证指定 Token 是否有效                   | `scripts/verify_token.py`              | `python scripts/verify_token.py <token>` |

## 强制重新登录（Token 过期或失效）

```bash
rm -f ~/.tme-login/storage_state.json ~/.tme-login/token.json
python scripts/login.py
```

## 环境配置

| 项                  | 值                                                               | 说明                                                                 |
| ------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- |
| 鉴权 Header         | `tme-header-token: <token>`                                      | Skill 内部自动获取，Token 有效期约 30 天                             |
| 调用脚本依赖        | Python 3 标准库（`urllib` / `json`）                             | 零额外依赖                                                           |
| 登录脚本依赖        | Playwright + Chromium                                            | 脚本内置自动安装；若脚本提示缺失，AI 必须自动执行 `python3 -m pip install playwright && python3 -m playwright install chromium`，不要把安装动作交给用户 |
| 缓存目录            | `~/.tme-login/`                                                  | 存放 `token.json` 和 `storage_state.json`，权限 0600                 |
