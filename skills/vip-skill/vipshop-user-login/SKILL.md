---
name: vipshop-user-login
description: >
  唯品会账号扫码登录技能。当用户说"登录唯品会"、"唯品会登录"、"扫码登录唯品会"、
  "我要登录唯品会账号"，或其他技能检测到未登录需要引导登录时，应立即触发此技能。
  执行完整的二维码登录流程：获取二维码 → 展示给用户扫码 → 轮询确认 → 保存登录态到
  ~/.vipshop-user-login/tokens.json，供其他唯品会技能使用。
---

# 唯品会扫码登录 Skill

> ⚠️ **重要规范**：AI 必须先加载本 skill 规范（use_skill），再执行任何脚本或返回结果，不得绕过 skill 规范自行处理数据。
>
> **二维码展示规范**：执行登录脚本后，AI 智能体 **必须优先** 从 stdout 中提取机器可读标记：`[VIPSHOP_QR_PAYLOAD_BEGIN]` 与 `[VIPSHOP_QR_PAYLOAD_END]` 之间的 JSON，读取其中的 `qrImageUrl` 字段，并以 Markdown 图片语法 `![唯品会登录二维码](URL)` 直接展示给用户。仅当该标记不存在时，才允许回退到提取 `二维码链接` 后面的 URL。**不要仅输出链接或文字描述，必须展示图片**。

此Skill提供唯品会扫码登录的完整解决方案，用于AI助手自动化完成唯品会账号登录流程。

## 使用场景

- AI助手需要访问唯品会用户数据
- 自动化脚本需要模拟用户登录
- 集成测试需要真实用户身份
- 数据采集需要登录态

## 工作流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  初始化二维码  │ ──→ │  展示二维码   │ ──→ │  轮询状态    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                          │
       │ 2. 返回qrToken                           │
       │←─────────────────────────────────────────┤
       │                                          │
       ▼                                          │
┌──────────────┐                                 │
│  用户扫码     │←────────────────────────────────┤
│  确认登录     │                                 │
└──────────────┘                                 │
       │                                         │
       │ 3. CONFIRMED                            │
       │─────────────────────────────────────────→│
       │                                         │
       ▼                                         ▼
┌──────────────┐                       ┌──────────────┐
│  登录成功     │                       │  保存Cookie   │
└──────────────┘                       └──────────────┘
```

1. **初始化二维码** - 调用API获取qrToken（自动校验格式，格式错误自动重试）
2. **获取二维码图片** - 使用qrToken获取二维码图片并展示
3. **轮询状态** - 定时检查扫码状态（NOT_SCANNED/SCANNED/CONFIRMED/INVALID）
4. **登录成功** - 状态为CONFIRMED时，Cookie中已包含登录凭证

## 核心功能

### 1. 获取登录二维码

```python
from scripts.vip_login import VIPLoginManager

manager = VIPLoginManager()
result = manager.login()
```

### 2. 展示二维码

支持多种展示方式：
- **终端显示** - 使用ASCII字符在终端显示（适合SSH环境）
- **打开图片** - 生成图片文件并用系统默认程序打开
- **AI智能体展示** - 脚本输出二维码链接 URL，AI 智能体应提取该 URL 并以 `![唯品会登录二维码](URL)` 展示图片
- **OpenClaw展示** - 检测 `OPENCLAW_SESSION=1` 时输出 `[OPENCLAW_SEND_FILE]路径[/OPENCLAW_SEND_FILE]`

### 3. 轮询登录状态

自动轮询二维码状态，检测：
- `NOT_SCANNED` - 未扫码
- `SCANNED` - 已扫码（等待确认）
- `CONFIRMED` - 已确认登录（成功）
- `INVALID` - 二维码过期/失效

### 4. Cookie管理

- 登录凭证自动保存到 `~/.vipshop-user-login/tokens.json`
- 单用户模式，自动覆盖旧登录态
- 基于Cookie的会话保持
- 登录态有效期与 PASSPORT_ACCESS_TOKEN cookie 一致

### 5. 版本检测与更新提示

登录成功后，脚本会输出版本信息并检测版本变化：

- 登录成功后会输出当前版本号（如 `当前版本: 1.0.0`）
- `tokens.json` 中保存当前版本号 `version`
- 如果检测到新版本，脚本只会提示用户按受控发布流程手动更新，不会自动执行更新命令，也不会远程下载并覆盖本地文件；提示信息中会给出可手动执行的命令 `npx clawhub update vipshop-skills --force`

**AI 助手职责**：

1. 登录成功后，**必须将脚本输出的当前版本号告知用户**（如"当前登录版本为 1.0.0"）
2. 如果脚本提示有新版本，**AI 必须提示用户按受控发布流程手动更新**，并可转述脚本给出的手动命令 `npx clawhub update vipshop-skills --force`；如需查看最新版本，可访问 https://github.com/vipshop/vipshop-ai-skills

## 使用方法

### 命令行使用

**默认非阻塞模式**（获取二维码后立即结束，不等待扫码）：

```bash
# 执行扫码登录（非阻塞模式，获取二维码后结束）
python scripts/vip_login.py

# 使用阻塞模式（获取二维码后等待扫码完成）
python scripts/vip_login.py --blocking

# 在终端显示二维码（不打开图片）
python scripts/vip_login.py --terminal

# 指定请求来源
python scripts/vip_login.py --where-from xxx

# 查看已登录记录
python scripts/vip_login.py --list

# 查看登录状态
python scripts/vip_login.py --status

# 注销登录记录
python scripts/vip_login.py --logout TOKEN_ID

# 使用指定qrToken继续登录（非阻塞模式后）
python scripts/vip_login.py --poll <qrToken>

# 继续上次未完成的登录
python scripts/vip_login.py --continue
```

### Python API使用

```python
from scripts.vip_login import VIPLoginManager, Config

# 方式1: 使用默认配置
manager = VIPLoginManager()
result = manager.quick_login()

if result.success:
    print(f"登录成功!")
    print(f"qrToken: {result.qr_token}")
    if result.redirect_url:
        print(f"跳转URL: {result.redirect_url}")
else:
    print(f"登录失败: {result.message}")

# 方式2: 自定义配置
class MyConfig(Config):
    SHOW_IN_TERMINAL = True   # 在终端显示二维码
    POLL_INTERVAL = 1         # 轮询间隔1秒
    POLL_TIMEOUT = 180        # 超时3分钟

manager = VIPLoginManager(MyConfig())
result = manager.login(where_from="my_app")

# 获取已保存的登录凭证
token_info = manager.get_stored_token("current_user")
if token_info:
    print(f"用户ID: {token_info.user_id}")
    print(f"Cookies: {token_info.cookies}")
```

### 非阻塞交互式登录（AI助手/OpenClaw场景）

适用于AI助手或OpenClaw场景：**发送二维码给用户后立即结束脚本**，不阻塞主会话。用户扫码确认后，通过后续命令继续完成登录。

**AI 智能体二维码展示：**
脚本执行后会在 stdout 中输出以下机器可读片段：

```text
[VIPSHOP_QR_PAYLOAD_BEGIN]
{"qrToken": "10000-xxx", "qrImageUrl": "https://passport.vip.com/qrLogin/getQrImage?qrToken=10000-xxx"}
[VIPSHOP_QR_PAYLOAD_END]
```

AI 智能体应优先提取该 JSON 中的 `qrImageUrl`，并以 Markdown 图片语法 `![唯品会登录二维码](URL)` 直接展示二维码图片。仅当该标记不存在时，才回退到读取 `二维码链接:` 后面的 URL。该链接为公网可访问 URL，无需依赖本地文件。

**OpenClaw 自动识别：**
当检测到 `OPENCLAW_SESSION=1` 环境变量时，脚本会自动输出 `[OPENCLAW_SEND_FILE]路径[/OPENCLAW_SEND_FILE]`，OpenClaw 可直接在会话中展示图片。

```python
from scripts.vip_login import VIPLoginManager

manager = VIPLoginManager()

# 定义发送二维码给用户的回调
def send_qr_to_user(image_bytes: bytes, image_format: str):
    """将二维码图片发送给用户"""
    # 实现你的发送逻辑，例如通过消息平台发送图片
    print(f"[发送二维码给用户] 格式: {image_format}, 大小: {len(image_bytes)} bytes")
    # 这里可以调用你的消息发送API

# 执行非阻塞登录
result = manager.login(
    where_from="my_app",
    send_qr_to_user_callback=send_qr_to_user
)

if result.success and result.qr_token:
    if result.message == "二维码已发送，请扫码确认后使用 --poll 参数继续":
        print(f"二维码已发送，qrToken: {result.qr_token}")
        print(f"如果二维码展示失败，请点击 {result.qr_url} 查看二维码")
        print("用户扫码确认后，调用 manager.login(qr_token_to_poll=qr_token) 继续")
    else:
        print("登录成功!")
else:
    print(f"登录失败: {result.message}")
```

**后续继续登录流程：**

```python
# 用户扫码确认后，使用之前保存的 qrToken 继续
result = manager.login(qr_token_to_poll="之前保存的qrToken")

if result.success:
    print("登录成功!")
else:
    print(f"登录失败: {result.message}")
```

### 分步骤使用

```python
from scripts.qr_code_client import QRCodeClient
from scripts.status_poller import StatusPoller, LoginStatus
from scripts.token_manager import TokenManager, TokenInfo
import time

# 1. 获取二维码
qr_client = QRCodeClient(
    base_url="https://passport.vip.com",
    init_endpoint="/qrLogin/initQrLogin",
    image_endpoint="/qrLogin/getQrImage"
)

success, qr_token, data = qr_client.init_qr_code(where_from="xxx")
if success:
    # 2. 展示二维码
    success, image_bytes, fmt = qr_client.get_qr_image(qr_token)
    qr_client.open_qr_image(image_bytes, fmt)

    # 3. 轮询状态
    poller = StatusPoller(
        base_url="https://passport.vip.com",
        check_endpoint="/qrLogin/checkStatus"
    )
    result = poller.poll_until_complete(qr_token)

    if result.status == LoginStatus.CONFIRMED:
        print("登录成功!")
        # 4. 保存凭证（从响应中提取 cookies）
        token_mgr = TokenManager()
        token_info = TokenInfo(
            cookies={"session": "xxx"},  # 从 result.raw_http_response 中提取
            user_id="user_id",
            nickname="nickname",
            expires_at=time.time() + 7 * 24 * 3600
        )
        token_mgr.save_token("current_user", token_info)
```

## 配置说明

在 `scripts/vip_login.py` 的 `Config` 类中可以自定义以下参数：

```python
class Config:
    # API 配置
    BASE_URL = "https://passport.vip.com"
    INIT_QR_ENDPOINT = "/qrLogin/initQrLogin"
    GET_QR_IMAGE_ENDPOINT = "/qrLogin/getQrImage"
    CHECK_STATUS_ENDPOINT = "/qrLogin/checkStatus"

    # 轮询配置
    POLL_INTERVAL = 1    # 轮询间隔（秒），建议每秒轮询一次
    POLL_TIMEOUT = 180   # 超时时间（秒），二维码有效期约3分钟

    # 二维码配置
    SHOW_IN_TERMINAL = False  # False=打开图片, True=终端显示

    # 交互模式配置（默认非阻塞模式）
    NON_BLOCKING_MODE = True  # True=非阻塞（获取二维码后结束）, False=阻塞（等待扫码完成）
```

## API接口文档

详细的API接口规范请参考 `references/api_reference.md`

主要接口：
- `POST /qrLogin/initQrLogin` - 初始化二维码（返回qrToken）
- `GET /qrLogin/getQrImage?qrToken=xxx` - 获取二维码图片
- `POST /qrLogin/checkStatus` - 轮询状态

状态值说明：
| 状态 | 说明 |
|------|------|
| NOT_SCANNED | 未扫描 |
| SCANNED | 已扫描 |
| CONFIRMED | 已确认登录（成功） |
| INVALID | 已失效 |

## 依赖安装

```bash
pip install requests qrcode Pillow
```

## 目录结构

```
vipshop-user-login/
├── SKILL.md                      # 此文档
├── scripts/
│   ├── vip_login.py              # 主登录脚本（入口）
│   ├── qr_code_client.py         # 二维码处理
│   ├── status_poller.py          # 状态轮询
│   ├── token_manager.py          # Token管理
│   ├── mars_cid_generator.py     # 设备ID生成器
│   └── logger.py                 # 日志上报（问题排查）
└── references/
    └── api_reference.md          # API接口文档
```

## 其他技能集成

本 Skill 登录成功后，会在 `~/.vipshop-user-login/tokens.json` 中保存登录态。

其他技能可以通过以下方式获取登录态：

```python
import json
from pathlib import Path

# 读取 cookies
token_file = Path.home() / ".vipshop-user-login" / "tokens.json"

if token_file.exists():
    with open(token_file, 'r') as f:
        data = json.load(f)
        cookies = data.get("cookies", {})
else:
    cookies = {}
```

详见：[集成指南](references/integration_guide.md)

## 注意事项

1. **二维码有效期**: 二维码默认3分钟过期，超时后状态变为`INVALID`，需重新获取
2. **轮询频率**: 建议每秒轮询一次，避免频繁请求导致IP被封
3. **Cookie保持**: 登录成功后，Cookie会自动包含登录凭证，无需额外获取token
4. **Token安全**: 凭证文件存储在用户目录`~/.vipshop-user-login/`下，权限设置为仅所有者可读写
5. **依赖项**: 需要安装 requests、qrcode、Pillow
6. **qrToken格式**: 系统会自动校验qrToken格式（如`10000-xxx`），格式错误会重试或报错，不会生成无效二维码
