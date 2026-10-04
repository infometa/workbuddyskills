"""
通用 iOA 开放 API 客户端。

核心能力：
- call(action, body): 对任意云规范接口发起 TC3 签名请求，自动解析 Response / Error
- 读写保护：默认仅放行只读类动作（Describe/List/Get/Query/Check/Search...），
  写动作（Create/Modify/Delete/Save/...）需显式 allow_write=True，避免误改客户系统
- 公钥获取与敏感字段 RSA 加密辅助（如创建账号 Password）

安全说明：
- base_url 指向「客户自己的 iOA 后台」，由客户在配置中显式提供，属预期访问；
  本工具不会自动探测/连接任何其它内网地址。
"""

import json
from typing import Any, Dict, Optional, Tuple

import requests

try:
    from .signer import build_signed_headers, DEFAULT_API_VERSION
    from .config import validate_config
    from .crypto_utils import rsa_encrypt_pkcs1_v15
except ImportError:
    from signer import build_signed_headers, DEFAULT_API_VERSION
    from config import validate_config
    from crypto_utils import rsa_encrypt_pkcs1_v15


# 只读动作前缀（动作名最后一段的开头）
READONLY_PREFIXES = (
    "Describe", "List", "Get", "Query", "Check", "Search", "Export", "Show",
)


def is_readonly_action(action: str) -> bool:
    """根据动作命名约定判断是否为只读接口。"""
    verb = action.strip("/").split("/")[-1]
    return verb.startswith(READONLY_PREFIXES)


class IOAOpenApiClient:
    def __init__(self, config: Dict, allow_write: bool = False):
        self.config = config
        self.allow_write = allow_write
        self.config_valid, self.config_msg = validate_config(config)
        self._public_key_pem: Optional[str] = None
        self.session = requests.Session()
        try:
            import urllib3  # type: ignore
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except Exception:
            pass

    # ------------------------------ 通用调用 ------------------------------ #
    def call(self, action: str, body: Optional[Dict[str, Any]] = None,
             version: Optional[str] = None,
             force: bool = False) -> Tuple[bool, str, Any]:
        """调用任意云规范接口。

        action: 形如 "Assets/Account/DescribeLocalAccounts"（不含 path_prefix）
        body:   请求体 dict，默认 {}
        version: X-TC-Version，默认取配置 api_version
        force:  True 时跳过读写保护（写动作放行）
        返回 (ok, msg, data)，data 为 Response 内容（或其 Data）。
        """
        if not self.config_valid:
            return False, f"配置无效: {self.config_msg}", None

        action = action.strip("/")
        body = body or {}

        # 读写保护
        if not force and not self.allow_write and not is_readonly_action(action):
            return (False,
                    f"动作 '{action}' 疑似写操作，已被读写保护拦截。"
                    f"如确需执行，请加 --confirm-write（或调用 call(..., force=True)）。",
                    None)

        version = version or self.config.get("api_version") or DEFAULT_API_VERSION
        canonical_uri = f"{self.config['path_prefix']}/{action}"
        url = f"{self.config['base_url']}{canonical_uri}"
        headers = build_signed_headers(self.config, canonical_uri, body, version=version)

        try:
            resp = self.session.post(
                url, headers=headers,
                data=json.dumps(body, separators=(",", ":")),
                timeout=self.config.get("timeout", 30),
                verify=self.config.get("verify_ssl", False),
            )
        except requests.exceptions.Timeout:
            return False, "请求超时", None
        except requests.exceptions.ConnectionError as e:
            return False, f"连接失败: {e}", None
        except Exception as e:
            return False, f"请求异常: {e}", None

        if resp.status_code == 401:
            return False, "鉴权失败（401）：请检查 SecretId/SecretKey、时间戳同步、API 版本号", None
        if resp.status_code != 200:
            return False, f"HTTP {resp.status_code}: {resp.text[:500]}", None

        try:
            raw = resp.json()
        except Exception:
            return False, f"非 JSON 响应: {resp.text[:500]}", None

        return self._parse_response(raw)

    @staticmethod
    def _parse_response(raw: Any) -> Tuple[bool, str, Any]:
        """统一解析云规范 / v1 响应。"""
        data = raw.get("Response") if isinstance(raw, dict) and "Response" in raw else raw

        if isinstance(data, list):
            return True, "ok", data
        if not isinstance(data, dict):
            return True, "ok", data

        # 云规范错误：Response.Error.{Code, Message}
        err = data.get("Error")
        if isinstance(err, dict) and err.get("Code"):
            return False, f"API 错误({err.get('Code')}): {err.get('Message', '')}", data

        # v1 错误：顶层 Code/Message
        code = data.get("Code")
        if code is not None and str(code) not in ("0", ""):
            return False, f"API 错误(Code={code}): {data.get('Message', '')}", data

        # trpc CommonRsp 错误
        common = data.get("CommonRsp") or {}
        if common.get("Code") and str(common.get("Code")) not in ("0", ""):
            return False, f"API 错误(CommonRsp.Code={common.get('Code')}): {common.get('Msg', '')}", data

        return True, "ok", data

    # ------------------------------ 连通性 ------------------------------ #
    def test_connection(self) -> Tuple[bool, str]:
        """用一个只读接口验证签名与连通性。"""
        ok, msg, _ = self.call(
            "Assets/Account/DescribeLocalAccounts",
            {"Condition": {"PageNum": 1, "PageSize": 1}},
        )
        return (True, "API 连接成功") if ok else (False, msg)

    # ------------------------------ 公钥 / 字段加密 ------------------------------ #
    def get_public_encrypt_key(self) -> Tuple[bool, str, str]:
        """获取后台 RSA 公钥（PEM），带内存缓存。"""
        import base64
        if self._public_key_pem:
            return True, "cached", self._public_key_pem
        ok, msg, data = self.call("common/DescribePublicEncryptKey", {}, force=True)
        if not ok:
            return False, msg, ""
        b64 = ""
        if isinstance(data, dict):
            b64 = (data.get("Data") or {}).get("PublicEncryptKey") or ""
        if not b64:
            return False, "响应中未找到 PublicEncryptKey", ""
        try:
            pem = base64.b64decode(b64).decode("utf-8")
        except Exception as e:
            return False, f"公钥解码失败: {e}", ""
        self._public_key_pem = pem
        return True, "ok", pem

    def encrypt_field(self, plain_text: str) -> Tuple[bool, str, str]:
        """对敏感字段做 RSA 加密（先取后台公钥），用于 Password 等字段。"""
        ok, msg, pem = self.get_public_encrypt_key()
        if not ok:
            return False, f"获取公钥失败: {msg}", ""
        try:
            return True, "ok", rsa_encrypt_pkcs1_v15(plain_text, pem)
        except Exception as e:
            return False, f"RSA 加密失败: {e}", ""

    # ------------------------------ 高层语义：查账号 / 查资源 / 授权 ------------------------------ #
    @staticmethod
    def _items(data: Any):
        """从已解析的 Response 中取出分页 Items 列表。"""
        if isinstance(data, dict):
            d = data.get("Data")
            if isinstance(d, dict):
                return d.get("Items") or []
            if isinstance(d, list):
                return d
        return []

    def find_account(self, identifier: str) -> Tuple[Optional[Dict], str]:
        """根据 UserId 或 UserName 查找账号。返回 (账号dict 或 None, 说明)。"""
        identifier = (identifier or "").strip()
        if not identifier:
            return None, "账号标识为空"

        for field in ("UserId", "UserName"):
            ok, msg, data = self.call(
                "Assets/Account/DescribeLocalAccounts",
                {"Condition": {"PageNum": 1, "PageSize": 50,
                               "FilterGroups": [{"Filters": [
                                   {"Field": field, "Operator": "eq",
                                    "Values": [identifier]}]}]},
                 "ShowFlag": 1},
            )
            if not ok:
                return None, msg
            items = self._items(data)
            for it in items:
                if str(it.get(field, "")).lower() == identifier.lower():
                    return it, f"按 {field} 精确匹配"
            # eq 无精确命中时，UserName 可能返回近似项，留待最后兜底
            if field == "UserName" and items:
                return items[0], "按 UserName 近似匹配（首条）"
        return None, "未找到账号"

    def find_area(self, area_name_or_id: str) -> Tuple[Optional[int], Optional[Dict]]:
        """资源组名 -> AreaId；若传入纯数字则直接当作 AreaId。"""
        v = str(area_name_or_id or "").strip()
        if not v:
            return None, None
        if v.isdigit():
            return int(v), None
        ok, _, data = self.call(
            "GatewayResource/DescribeResourceModules",
            {"Condition": {"PageNum": 1, "PageSize": 200}})
        if ok:
            for it in self._items(data):
                if str(it.get("AreaName", "")).strip() == v:
                    return int(it.get("AreaId") or 0) or None, it
        return None, None

    @staticmethod
    def _resource_id(r: Dict) -> int:
        return int(r.get("ServiceId") or r.get("Id") or 0)

    def find_resource(self, name: str, area_id: Optional[int] = None):
        """按资源名查找业务资源。

        返回 (resource dict 或 None, candidates 列表, 状态)
        状态: 'matched' / 'not_found' / 'ambiguous' / 错误信息
        """
        name = (name or "").strip()
        if not name:
            return None, [], "资源名为空"
        body: Dict[str, Any] = {"ServiceName": name,
                                "Condition": {"PageNum": 1, "PageSize": 100}}
        if area_id:
            body["AreaId"] = int(area_id)
        ok, msg, data = self.call("GatewayResource/DescribeBusinessResources", body)
        if not ok:
            return None, [], msg
        items = self._items(data)
        exact = [r for r in items if str(r.get("ServiceName", "")).strip() == name]
        if area_id:
            exact = [r for r in exact if int(r.get("AreaId") or 0) == int(area_id)]
        if len(exact) == 1:
            return exact[0], items, "matched"
        if len(exact) > 1:
            return None, exact, "ambiguous"
        return None, items, "not_found"

    def grant_resources(self, account_id: int, resource_ids,
                        resource_type: int = 1, expire_time: int = 0):
        """给账号授权一组资源（NGN/SaveAccountResources）。"""
        rids = [int(r) for r in resource_ids if r]
        if not rids:
            return False, "没有可授权的资源 ID", None
        items = [{"ResourceId": r, "ResourceType": int(resource_type),
                  "ExpireTime": int(expire_time)} for r in rids]
        return self.call("NGN/SaveAccountResources",
                         {"AccountId": int(account_id), "ResourceList": items},
                         force=True)
