#!/usr/bin/env python3
"""用验证码登录 LinkFox 并获取 API key。

用法：
    python scripts/login_and_get_key.py <phone> <code>

流程：
    1. POST /user/v3/web/login 拿 accessToken + refreshToken + userId（含 newUser 标记）
    2. 仅新用户（newUser=true）：POST /account/loginByToken 触发新用户送积分
    3. POST /linkFoxApp/api/userCenter/userInfo 拿 agentTeamId(groupId) + agentMemberId(memberId)
    4. POST /group/getApiToken 查已有 token；无则 POST /group/generateApiToken 生成

输出 JSON：
    成功：{"api_key": "<token>", "phone": "188****1234", "group_id": "...", "member_id": "...", "source": "existing|generated"}
    失败：{"error": "<阶段>: <信息>", "phone": "188****1234"}

手机号在输出时脱敏（保留前 3 后 4），脚本内部仍用完整手机号调接口。
"""
from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, __file__.rsplit("\\", 1)[0] if "\\" in __file__ else __file__.rsplit("/", 1)[0])

from setup_common import login_post, agent_user_post, _stderr_tag


def _mask_phone(phone: str) -> str:
    """脱敏：188****1234。"""
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return phone


def _login(phone: str, code: str, channel: str) -> dict:
    """v3 登录，返回 {access_token, refresh_token, user_id, nick_name, is_new_user} 或 {error}。"""
    body = {
        "type": "sms",
        "method": "login",
        "systemId": "LinkFoxAgent",
        "data": {
            "areaCode": "+86",
            "authPhone": phone,
            "authCode": code,
            "sourceChannel": channel or "skill",
        },
    }
    resp = login_post("/user/v3/web/login", body, with_uid=True)
    if "_http_error" in resp or "_error" in resp:
        return {"error": f"login: {resp.get('_body') or resp.get('_error', 'HTTP错误')}"}
    if not (resp.get("success") or resp.get("code") == "OK"):
        return {"error": f"login: {resp.get('message') or json.dumps(resp, ensure_ascii=False)}"}
    data = resp.get("data") or {}
    access_token = data.get("accessToken")
    refresh_token = data.get("refreshToken")
    user_id = data.get("userId")
    if not access_token or not user_id:
        return {"error": f"login: 响应缺 accessToken/userId: {json.dumps(resp, ensure_ascii=False)}"}
    return {
        "access_token": access_token,
        "refresh_token": refresh_token or "",
        "user_id": str(user_id),
        "nick_name": data.get("userName", ""),
        "is_new_user": bool(data.get("newUser") or data.get("isFirstRegister")),
    }


def _login_by_token(access_token: str, refresh_token: str) -> dict:
    """新用户触发送积分：POST /account/loginByToken。

    仅新用户（newUser=true）需要调。老用户调了无副作用但也无收益，故跳过。
    返回 {} 成功 或 {error}。
    """
    try:
        import requests
    except ImportError:
        return {"error": "loginByToken: 缺少 requests 依赖，请运行: pip install requests"}
    from setup_common import _get_agent_user_base, _stderr_tag
    url = f"{_get_agent_user_base()}/account/loginByToken"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://agent.linkfox.com",
        "Referer": "https://agent.linkfox.com/",
        "source": "agent-linkfox-web",
        "authorization": access_token,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    }
    body = {
        "token": access_token,
        "refreshToken": refresh_token,
        "device": {
            "aid": "3026344186",  # 固定设备指纹，实测可用（后端不校验唯一性）
            "did": "",
            "type": "Windows",
            "os": "10",
            "model": "149.0.0.0",
            "brand": "Chrome",
        },
    }
    try:
        r = requests.post(url, json=body, headers=headers, timeout=30)
        resp = r.json()
    except Exception as e:
        return {"error": f"loginByToken: {e}"}
    if resp.get("errcode") != 200:
        return {"error": f"loginByToken: {resp.get('errmsg') or json.dumps(resp, ensure_ascii=False)}"}
    print(f"{_stderr_tag()} loginByToken 成功，新用户积分已触发发放", file=sys.stderr)
    return {}


def _fetch_user_info(access_token: str, user_id: str) -> dict:
    """拿 userInfo，返回 {group_id, member_id, team_name} 或 {error}。"""
    # userInfo 走 api.linkfox.com（不是 agent-api）
    url_path = "/linkFoxApp/api/userCenter/userInfo"
    # 复用 login_post（同域名 api），但需要 agent-linkfox-web source + 自定义 uid
    # 这里直接构造，不调 login_post（它 source 固定 ai-linkfox-web）
    try:
        import requests
    except ImportError:
        return {"error": "userInfo: 缺少 requests 依赖，请运行: pip install requests"}
    from setup_common import _get_login_base, build_uid_header
    url = f"{_get_login_base()}{url_path}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://agent.linkfox.com",
        "Referer": "https://agent.linkfox.com/",
        "source": "agent-linkfox-web",
        "authorization": access_token,
        "uid": build_uid_header(access_token, user_id),
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    }
    try:
        r = requests.post(url, json={}, headers=headers, timeout=30)
        body = r.json()
    except Exception as e:
        return {"error": f"userInfo: {e}"}
    if body.get("code") != "OK":
        return {"error": f"userInfo: {body.get('message') or json.dumps(body, ensure_ascii=False)}"}
    data = body.get("data") or {}
    teams = data.get("teamList") or []
    if not teams:
        return {"error": f"userInfo: 用户未开通任何团队空间，请先访问 https://agent.linkfox.com/ 完成开通"}
    # 选团队：优先 isSelect=1 且 agentTeamId 非空；否则第一个 agentTeamId 非空的
    selected = next((t for t in teams if t.get("isSelect") == 1 and t.get("agentTeamId")), None)
    if not selected:
        selected = next((t for t in teams if t.get("agentTeamId")), None)
    if not selected:
        return {"error": f"userInfo: 所有团队均未开通 agent 空间（agentTeamId 为空），请访问 https://agent.linkfox.com/ 登录后开通"}
    group_id = selected.get("agentTeamId")
    member_id = selected.get("agentMemberId")
    if not group_id or not member_id:
        return {"error": f"userInfo: 选中团队缺 agentTeamId/agentMemberId: {json.dumps(selected, ensure_ascii=False)}"}
    return {
        "group_id": str(group_id),
        "member_id": str(member_id),
        "team_name": selected.get("teamName", ""),
    }


def _get_or_generate_api_token(access_token: str, user_id: str, group_id: str) -> dict:
    """先查 getApiToken，无则 generateApiToken。"""
    body = {"id": group_id}
    # 查已有
    resp = agent_user_post(
        "/group/getApiToken", body,
        access_token=access_token, user_id=user_id, group_id=group_id,
    )
    if "_http_error" in resp or "_error" in resp:
        return {"error": f"getApiToken: {resp.get('_body') or resp.get('_error', 'HTTP错误')}"}
    # 成功响应可能直接是 token 字符串，或 {token:...}，或 {data:{apiToken:...}}
    token = _extract_token(resp)
    if token:
        return {"api_key": token, "source": "existing"}

    # 查无 → 生成
    resp = agent_user_post(
        "/group/generateApiToken", body,
        access_token=access_token, user_id=user_id, group_id=group_id,
    )
    if "_http_error" in resp or "_error" in resp:
        return {"error": f"generateApiToken: {resp.get('_body') or resp.get('_error', 'HTTP错误')}"}
    token = _extract_token(resp)
    if token:
        return {"api_key": token, "source": "generated"}
    return {"error": f"generateApiToken: 未拿到 token，响应: {json.dumps(resp, ensure_ascii=False)}"}


def _extract_token(resp: dict) -> str:
    """从响应里提取 token 字符串。

    实测响应字段：getApiToken/generateApiToken 成功时返回
    {"errcode":200,"key":"<短id>","token":"<JWT>","createDate":"..."}。
    token 为空字符串表示无 token（getApiToken 查无）。
    """
    if not isinstance(resp, dict):
        return ""
    # 实测字段名：token（JWT 字符串），key 是短 id（非 API key）
    for key in ("token", "apiToken", "api_token", "apiKey", "api_key"):
        v = resp.get(key)
        if isinstance(v, str) and v:
            return v
    data = resp.get("data")
    if isinstance(data, dict):
        for key in ("token", "apiToken", "api_token", "apiKey", "api_key"):
            v = data.get(key)
            if isinstance(v, str) and v:
                return v
    if isinstance(data, str) and data:
        return data
    return ""


def login_and_get_key(phone: str, code: str, channel: str) -> dict:
    masked = _mask_phone(phone)
    if not re.fullmatch(r"\d{11}", phone):
        return {"error": f"login: 手机号格式不正确: {phone}", "phone": masked}
    if not re.fullmatch(r"\d{4,8}", code):
        return {"error": f"login: 验证码格式不正确: {code}", "phone": masked}

    login_res = _login(phone, code, channel)
    if "error" in login_res:
        return {"error": login_res["error"], "phone": masked}
    access_token = login_res["access_token"]
    user_id = login_res["user_id"]

    # 仅新用户触发送积分
    if login_res.get("is_new_user"):
        lbt = _login_by_token(access_token, login_res.get("refresh_token", ""))
        if "error" in lbt:
            # loginByToken 失败不阻断主流程，stderr 提示但继续拿 key
            print(f"[real] {lbt['error']}（不影响后续拿 key，但新用户积分可能未发放）", file=sys.stderr)

    info = _fetch_user_info(access_token, user_id)
    if "error" in info:
        return {"error": info["error"], "phone": masked}
    group_id = info["group_id"]
    member_id = info["member_id"]

    tok = _get_or_generate_api_token(access_token, user_id, group_id)
    if "error" in tok:
        return {"error": tok["error"], "phone": masked}

    return {
        "api_key": tok["api_key"],
        "phone": masked,
        "group_id": group_id,
        "member_id": member_id,
        "source": tok["source"],
        "nick_name": login_res.get("nick_name", ""),
        "team_name": info.get("team_name", ""),
        "is_new_user": login_res.get("is_new_user", False),
    }


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(json.dumps({"error": "用法: python login_and_get_key.py <phone> <code>"}, ensure_ascii=False))
        return 2
    phone = argv[1].strip()
    code = argv[2].strip()
    channel = argv[3].strip()
    result = login_and_get_key(phone, code, channel)
    print(json.dumps(result, ensure_ascii=False))
    if "api_key" in result:
        print(
            f"{_stderr_tag()} 成功获取 API key（来源: {result['source']}）。"
            "请引导用户配置环境变量 LINKFOX_AGENT_API_KEY 或 LINKFOXAGENT_API_KEY。",
            file=sys.stderr,
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
