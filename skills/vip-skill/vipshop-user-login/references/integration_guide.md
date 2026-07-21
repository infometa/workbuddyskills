# 唯品会扫码登录 - 其他技能集成指南

本文档说明如何在其他 Skill 中使用本登录功能的登录结果。

## 登录态存储位置

登录成功后，会在用户目录下保存登录态：

```
~/.vipshop-user-login/tokens.json
```

存储格式：

```json
{
  "cookies": {
    "PASSPORT_ACCESS_TOKEN": "xxx",
    "VipRUID": "123456789",
    "VipRNAME": "nickname",
    "mars_cid": "..."
  },
  "user_id": "123456789",
  "nickname": "用户昵称",
  "created_at": 1699123456.789,
  "expires_at": 1699715256.789
}
```

## 使用方式

### 方式1: 直接读取 Cookie 文件

```python
import json
from pathlib import Path
import requests

# 读取保存的登录态
token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
if token_file.exists():
    with open(token_file, 'r') as f:
        data = json.load(f)
        cookies = data.get("cookies", {})
    
    # 使用 cookies 访问唯品会 API
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.vip.com/',
    })
    
    # 设置 cookies
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.vip.com')
    
    # 发起请求
    response = session.get("https://www.vip.com/user/info")
    print(response.text)
else:
    print("未找到登录态，请先执行扫码登录")
```

### 方式2: 通过 TokenManager 获取

如果你的 Skill 可以访问本 Skill 的 `scripts` 目录，推荐使用 TokenManager：

```python
from scripts.token_manager import TokenManager

manager = TokenManager()
token_info = manager.get_token()

if token_info:
    cookies = token_info.cookies
    user_id = token_info.user_id
    nickname = token_info.nickname
    
    # 使用 cookies 发起请求
    import requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.vip.com/',
    })
    
    # 设置 cookies
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.vip.com')
    
    # 发起请求
    response = session.get("https://www.vip.com/user/info")
    print(response.text)
else:
    print("登录态已过期，需要重新登录")
```

## 关键 Cookie 说明

| Cookie 名称 | 说明 |
|------------|------|
| `PASSPORT_ACCESS_TOKEN` | 访问令牌，用于身份验证 |
| `VipRUID` | 用户ID |
| `VipRNAME` | 用户昵称（URL编码） |
| `mars_cid` | 设备ID |

## 检查登录态是否有效

```python
from scripts.token_manager import TokenManager

manager = TokenManager()

# 获取登录态（get_token 内部已处理过期逻辑）
token_info = manager.get_token()

if token_info:
    print("登录态有效")
    cookies = manager.get_cookies()
else:
    print("未登录或登录态已过期，请先执行扫码登录")
```

## 完整示例：获取用户信息

```python
import json
from pathlib import Path
import requests

def get_vip_user_info():
    """获取唯品会用户信息"""
    # 读取登录态
    token_file = Path.home() / ".vipshop-user-login" / "tokens.json"
    
    if not token_file.exists():
        return {"error": "未登录，请先执行扫码登录"}
    
    with open(token_file, 'r') as f:
        data = json.load(f)
    
    cookies = data.get("cookies", {})
    
    if not cookies:
        return {"error": "登录态无效"}
    
    # 检查是否过期（简单检查 PASSPORT_ACCESS_TOKEN 是否存在）
    if "PASSPORT_ACCESS_TOKEN" not in cookies:
        return {"error": "登录态已过期"}
    
    # 创建 session
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.vip.com/',
        'Accept': 'application/json, text/plain, */*',
    })
    
    # 设置 cookies
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.vip.com')
    
    # 发起请求获取用户信息
    try:
        response = session.get(
            "https://www.vip.com/user/info",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"请求失败: {e}"}

# 使用示例
result = get_vip_user_info()
print(result)
```

## 注意事项

1. **登录态有效期**: 默认与 PASSPORT_ACCESS_TOKEN cookie 的 Max-Age 一致（约7天）
2. **Cookie 域名**: 设置 cookie 时必须指定 `domain='.vip.com'`，否则无法跨子域使用
3. **Referer 头**: 请求唯品会 API 时必须携带正确的 Referer 头
4. **重新登录**: 如果登录态过期，需要引导用户重新执行扫码登录
