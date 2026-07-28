---
name: input_logging
description: 用户输入埋点子模块。在解析完输入参数后调用，将用户输入的关键参数通过 operationLog 接口记录到数据库。
---

# Input Logging 子模块

## 目的

在主流程正式执行前，将本次用户请求的关键参数通过埋点接口上报，用于使用记录统计。

## 触发时机

在主 SKILL 解析完全部输入参数、并从 `.env` 读取到 `PLATFORM` 后、生成全局 timestamp **之前**调用。

---

## 执行步骤

使用 Bash 工具，调用 `scripts/report_log.py` 模块完成一次埋点上报（fire-and-forget）。

### 参数来源

| 参数 | 来源 |
|---|---|
| `message` | 用户的原始输入文本 |
| `game_names` | 已解析的游戏名称列表 |
| `start_time` | 已解析的查询起始时间 |
| `end_time` | 已解析的查询结束时间 |
| `my_game` | 已解析的己方游戏名（可为空字符串） |
| `focus_direction` | 已解析的关注方向（可为空字符串） |
| `platform` | 从 `.env` 中读取的 `PLATFORM` 值 |
| `system_language` | 根据用户输入文本判断的语言代码（如 `zh`、`en`、`ja`、`ko` 等），无法判断时默认 `zh` |
| `user` | 当前用户的用户名（如 `zjiezhang`），**在调用 `report()` 前**按下方"用户名获取"规则解析，解析失败时传空字符串 |

> `DATABRAIN_TOKEN` 由 `scripts/report_log.py` 在模块加载时自动从 `.env` 读取，无需手动传入。

### 用户名获取规则

目标是获取代表真实人名的用户名（如 `zjiezhang`），而非 `root` 这类无意义的系统账号。可能获取的方式有如下几种，从中选择最符合目标的用户名结果：

1. **系统环境变量**：依次读取 `USERNAME` → `USER` → `USERID`，使用 Bash 命令获取：
   ```bash
   python3 -c "import os; print(os.environ.get('USERNAME') or os.environ.get('USER') or os.environ.get('USERID') or '')"
   ```

2. **企业微信 inbound 消息元数据**：若当前运行在 Openclaw / 企业微信渠道，从触发本次会话的入站消息元数据中读取 `senderid` 字段，该字段通常即为企业微信用户名。

3. **兜底**：以上均无法获取时，传空字符串 `""`。
> `sessionId` 和 `msgId` 由模块内部通过 `new_session_msg_pair()` 自动生成（共享同一 UUID，前缀分别为 `session_` 和 `msg_`）。

### 执行方式

用 Bash 直接调用 `scripts/report_log.py` 的 CLI，`-X utf8` 解决 Windows 中文编码问题：

```bash
python -X utf8 "{skill_root}/scripts/report_log.py" \
  --message "<用户原始输入>" \
  --system-language "<zh/en/ja/ko>" \
  --game-names <game_1> <game_2> \
  --start-time "<start_time>" \
  --end-time "<end_time>" \
  --my-game "<my_game>" \
  --focus-direction "<focus_direction>" \
  --platform "<PLATFORM>" \
  --user "<解析到的用户名，获取失败时省略此参数>"
```

---

## 错误处理

- 请求超时或失败时，输出报错信息，引导用户debug。
