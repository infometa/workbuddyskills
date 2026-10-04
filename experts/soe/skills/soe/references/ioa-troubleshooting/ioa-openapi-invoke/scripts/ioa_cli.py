"""
ioa-openapi-invoke 命令行入口：让客户针对自己的 iOA 系统调用任意开放 API。

子命令：
- test     测试签名与连通性
- call     调用任意云规范接口（最常用）
- encrypt  对敏感字段（如密码）做后台 RSA 加密，得到可直接放进 body 的密文
- pubkey   获取后台 RSA 公钥（PEM）

示例：
    # 1) 测试连通
    python ioa_cli.py test --config ../configs/customerA.json

    # 2) 调用查询账号列表（body 来自字符串）
    python ioa_cli.py call \
        --action Assets/Account/DescribeLocalAccounts \
        --body '{"Condition":{"PageNum":1,"PageSize":10}}' \
        --config ../configs/customerA.json

    # 3) 调用查询设备列表（body 来自文件）
    python ioa_cli.py call --action Assets/DescribeDevices \
        --body-file ./body.json --config ../configs/customerA.json

    # 4) 执行写操作需显式确认
    python ioa_cli.py call --action NGN/AddBlackDevices \
        --body '{"device_ids":["xxxx"]}' --confirm-write \
        --config ../configs/customerA.json

    # 5) 用 --pwd-field 自动加密某字段后再调用（如创建账号 Password）
    python ioa_cli.py call --action Assets/Account/CreateLocalAccount \
        --body-file ./create.json --pwd-field Password --confirm-write \
        --config ../configs/customerA.json
"""

import argparse
import json
import os
import sys
from typing import Any, Dict

try:
    from .config import load_config, validate_config
    from .ioa_client import IOAOpenApiClient, is_readonly_action
    from .crypto_utils import encrypt_credential
except ImportError:
    from config import load_config, validate_config
    from ioa_client import IOAOpenApiClient, is_readonly_action
    from crypto_utils import encrypt_credential


def _configs_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))


def _print_header(title: str) -> None:
    bar = "=" * 70
    print(bar)
    print(f"  {title}")
    print(bar)


def _load_body(args) -> Dict[str, Any]:
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as f:
            return json.load(f)
    if args.body:
        return json.loads(args.body)
    return {}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ioa-openapi-invoke",
        description="通用 iOA 开放 API 调用工具（客户针对自己的系统调用任意接口）",
    )
    sub = p.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", default=None, help="客户配置文件路径（JSON）")
    common.add_argument("--verbose", "-v", action="store_true", help="打印调试信息")

    sub.add_parser("test", parents=[common], help="测试签名与连通性")

    c = sub.add_parser("call", parents=[common], help="调用任意云规范接口")
    c.add_argument("--action", required=True,
                   help="接口动作，如 Assets/Account/DescribeLocalAccounts")
    c.add_argument("--body", default="", help="请求体 JSON 字符串")
    c.add_argument("--body-file", default="", help="请求体 JSON 文件路径")
    c.add_argument("--version", default="", help="覆盖 X-TC-Version（默认取配置）")
    c.add_argument("--confirm-write", action="store_true",
                   help="放行写操作（Create/Modify/Delete/Save 等）")
    c.add_argument("--pwd-field", default="",
                   help="对 body 中该字段做后台 RSA 加密后再发送（如 Password）")
    c.add_argument("--raw", action="store_true", help="原样打印完整响应")

    e = sub.add_parser("encrypt", parents=[common], help="对敏感字段做后台 RSA 加密")
    e.add_argument("--text", required=True, help="待加密明文")

    sub.add_parser("pubkey", parents=[common], help="获取后台 RSA 公钥(PEM)")

    g = sub.add_parser("grant", parents=[common],
                       help="一句话授权：自动查账号、查资源，存在则授权，缺失则告知")
    g.add_argument("--account", required=True, help="账号 UserId 或 UserName")
    g.add_argument("--resource", required=True, action="append",
                   help="资源名称，可多次传入或用逗号分隔")
    g.add_argument("--resource-area", default="",
                   help="资源所在资源组名或 AreaId（同名资源消歧用）")
    g.add_argument("--resource-type", type=int, default=1, choices=[1, 2],
                   help="1=业务资源 2=资源组，默认 1")
    g.add_argument("--expire", type=int, default=0, help="到期时间戳，0=永久")
    g.add_argument("--dry-run", action="store_true", help="只查不授权，仅预览匹配结果")

    i = sub.add_parser("init", help="向导式生成客户配置（引导填写后台地址与凭证）")
    i.add_argument("--customer", default="", help="客户标识，生成 configs/<customer>.json")
    i.add_argument("--base-url", default="", help="iOA 后台地址，如 https://ioa.example.com:8443")
    i.add_argument("--secret-id", default="", help="API SecretId")
    i.add_argument("--secret-key", default="", help="API SecretKey")
    i.add_argument("--service", default="", help="签名 service（私有化留空，SaaS 填 ioa）")
    i.add_argument("--verify-ssl", action="store_true", help="校验 SSL 证书（默认不校验）")
    i.add_argument("--encrypt", action="store_true",
                   help="将凭证用本机密钥加密后存储（更安全）")
    i.add_argument("--force", action="store_true", help="目标文件已存在时覆盖")
    i.add_argument("--no-input", action="store_true", help="禁用交互提示，仅用命令行参数")
    i.add_argument("--no-test", action="store_true", help="生成后不自动做连通性测试")
    return p


def _make_client(args) -> IOAOpenApiClient:
    config = load_config(args.config)
    ok, msg = validate_config(config)
    if not ok:
        print(f"[!] 配置校验失败: {msg}")
        print("    请通过 --config 指定客户配置文件，或设置 IOA_BASE_URL / "
              "IOA_SECRET_ID / IOA_SECRET_KEY 环境变量。")
        sys.exit(2)
    return IOAOpenApiClient(config, allow_write=getattr(args, "confirm_write", False))


def cmd_test(args) -> int:
    client = _make_client(args)
    _print_header("iOA OpenAPI 连通性测试")
    sid = client.config.get("secret_id", "")
    print(f"  base_url:  {client.config.get('base_url')}")
    print(f"  secret_id: {sid[:6]}***{sid[-4:] if len(sid) > 10 else ''}")
    ok, msg = client.test_connection()
    print(f"  结果: {'成功' if ok else '失败'}  ({msg})")
    return 0 if ok else 4


def cmd_call(args) -> int:
    client = _make_client(args)
    try:
        body = _load_body(args)
    except Exception as e:
        print(f"[!] 解析 body 失败: {e}")
        return 2

    # 写保护提示
    if not is_readonly_action(args.action) and not args.confirm_write:
        print(f"[!] '{args.action}' 疑似写操作。如确认执行，请加 --confirm-write。")
        return 3

    # 字段加密
    if args.pwd_field:
        if args.pwd_field not in body:
            print(f"[!] body 中不存在字段 '{args.pwd_field}'")
            return 2
        ok, msg, enc = client.encrypt_field(str(body[args.pwd_field]))
        if not ok:
            print(f"[!] 字段加密失败: {msg}")
            return 4
        body[args.pwd_field] = enc
        print(f"[*] 已对字段 '{args.pwd_field}' 完成后台 RSA 加密")

    version = args.version or None
    ok, msg, data = client.call(args.action, body, version=version,
                                force=args.confirm_write)
    if not ok:
        print(f"[FAIL] {msg}")
        if args.raw and data is not None:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 5

    print("[OK]")
    payload = data if args.raw else (
        data.get("Data") if isinstance(data, dict) and "Data" in data else data)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_encrypt(args) -> int:
    client = _make_client(args)
    ok, msg, enc = client.encrypt_field(args.text)
    if not ok:
        print(f"[FAIL] {msg}")
        return 4
    print(enc)
    return 0


def cmd_pubkey(args) -> int:
    client = _make_client(args)
    ok, msg, pem = client.get_public_encrypt_key()
    if not ok:
        print(f"[FAIL] {msg}")
        return 4
    print(pem)
    return 0


def _split_resources(values):
    """支持 --resource a,b --resource c 这种混合写法。"""
    out = []
    for v in values or []:
        for part in str(v).split(","):
            part = part.strip()
            if part and part not in out:
                out.append(part)
    return out


def cmd_grant(args) -> int:
    client = _make_client(args)
    _print_header("一句话授权：查账号 → 查资源 → 授权")

    resource_names = _split_resources(args.resource)
    print(f"  账号:   {args.account}")
    print(f"  资源:   {resource_names}")
    if args.resource_area:
        print(f"  资源组: {args.resource_area}")
    print()

    # 1) 查账号
    account, amsg = client.find_account(args.account)
    if not account:
        print(f"❌ 账号不存在：未找到账号 '{args.account}'（{amsg}），无法授权。")
        return 3
    account_id = int(account.get("AccountId") or account.get("Id") or 0)
    print(f"✅ 找到账号：{account.get('UserId')} / {account.get('UserName')} "
          f"(AccountId={account_id})")

    # 2) 解析资源组（可选，用于同名消歧）
    area_id = None
    if args.resource_area:
        area_id, area_info = client.find_area(args.resource_area)
        if not area_id:
            print(f"⚠️  未找到资源组 '{args.resource_area}'，将忽略资源组限定继续查找。")
        else:
            print(f"   资源组 AreaId={area_id}"
                  f"{(' (' + str((area_info or {}).get('AreaName')) + ')') if area_info else ''}")

    # 3) 查资源
    found = []      # [(name, resource_id, area_name)]
    missing = []    # [name]
    ambiguous = []  # [(name, candidates)]
    for name in resource_names:
        res, candidates, status = client.find_resource(name, area_id=area_id)
        if status == "matched" and res:
            rid = client._resource_id(res)
            found.append((name, rid, res.get("AreaName") or res.get("AreaId")))
            print(f"✅ 找到资源：{name} -> ResourceId={rid} "
                  f"(组={res.get('AreaName') or res.get('AreaId')})")
        elif status == "ambiguous":
            ambiguous.append((name, candidates))
            opts = [f"AreaId={c.get('AreaId')}({c.get('AreaName')})" for c in candidates[:5]]
            print(f"⚠️  资源 '{name}' 有多个同名项，需用 --resource-area 指定：{opts}")
        elif status == "not_found":
            missing.append(name)
            sim = [c.get("ServiceName") for c in (candidates or [])[:5]]
            hint = f"（相似资源：{sim}）" if sim else ""
            print(f"❌ 资源不存在：未找到资源 '{name}'{hint}")
        else:
            missing.append(name)
            print(f"❌ 查询资源 '{name}' 失败：{status}")

    # 4) 汇总与授权
    print()
    if not found:
        print("结论：没有可授权的资源（账号存在但资源均缺失/不明确），未执行任何授权。")
        return 4

    if args.dry_run:
        print(f"[DRY-RUN] 预览完成：可授权 {len(found)} 个资源给账号 "
              f"{account.get('UserId')}，未实际下发。")
        return 0

    rids = [rid for _, rid, _ in found]
    ok, msg, _ = client.grant_resources(
        account_id, rids, resource_type=args.resource_type, expire_time=args.expire)
    if ok:
        names = [n for n, _, _ in found]
        print(f"🎉 授权成功：已将资源 {names} 授权给账号 "
              f"{account.get('UserId')} (AccountId={account_id})。")
        if missing:
            print(f"   注意：以下资源不存在，未授权：{missing}")
        if ambiguous:
            print(f"   注意：以下资源同名多项需指定资源组：{[n for n, _ in ambiguous]}")
        return 0
    print(f"❌ 授权失败：{msg}")
    return 5


def _prompt(label: str, default: str = "", required: bool = False,
            secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        try:
            val = input(f"{label}{suffix}: ").strip()
        except EOFError:
            val = ""
        if not val and default:
            val = default
        if val or not required:
            return val
        print("  该项必填，请输入。")


def cmd_init(args) -> int:
    _print_header("配置向导：填写你自己环境的 iOA 地址与凭证")
    interactive = not args.no_input

    customer = args.customer
    base_url = args.base_url
    secret_id = args.secret_id
    secret_key = args.secret_key
    service = args.service

    if interactive:
        print("提示：SecretId/SecretKey 在 iOA 控制台「系统设置 → 第三方对接 → "
              "API接口管理 → 添加API凭证」获取。\n")
        customer = customer or _prompt("客户标识(用于文件名，如 customerA)", "default", required=True)
        base_url = base_url or _prompt("iOA 后台地址(https://主机:端口)", required=True)
        secret_id = secret_id or _prompt("SecretId", required=True)
        secret_key = secret_key or _prompt("SecretKey", required=True)
        if not service:
            service = _prompt("签名 service(私有化直接回车；SaaS 填 ioa)", "")
    else:
        customer = customer or "default"

    missing = [n for n, v in (("--base-url", base_url), ("--secret-id", secret_id),
                              ("--secret-key", secret_key)) if not v]
    if missing:
        print(f"[!] 缺少必填项: {missing}（非交互模式请在命令行提供）")
        return 2

    base_url = base_url.rstrip("/")
    cfg: Dict[str, Any] = {
        "base_url": base_url,
        "verify_ssl": bool(args.verify_ssl),
        "timeout": 30,
        "service": service or "",
        "path_prefix": "/capi",
        "api_version": "2022-06-01",
    }
    if args.encrypt:
        cfg["secret_id"] = ""
        cfg["secret_key"] = ""
        cfg["encrypted_secret_id"] = encrypt_credential(secret_id)
        cfg["encrypted_secret_key"] = encrypt_credential(secret_key)
        print("[*] 凭证已用本机密钥加密（仅本机可解密）。")
    else:
        cfg["secret_id"] = secret_id
        cfg["secret_key"] = secret_key

    os.makedirs(_configs_dir(), exist_ok=True)
    path = os.path.join(_configs_dir(), f"{customer}.json")
    if os.path.exists(path) and not args.force:
        print(f"[!] 配置已存在: {path}（如需覆盖请加 --force）")
        return 3
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[OK] 已生成配置: {path}")
    print(f"     后续调用统一加: --config ../configs/{customer}.json")

    if args.no_test:
        return 0

    print("\n[*] 正在做连通性测试 ...")
    config = load_config(path)
    ok, msg = validate_config(config)
    if not ok:
        print(f"[!] 配置校验失败: {msg}")
        return 4
    ok, tmsg = IOAOpenApiClient(config).test_connection()
    print(f"    结果: {'成功 ✅' if ok else '失败 ❌'}  ({tmsg})")
    if not ok:
        print("    排查：检查地址是否可达、SecretId/SecretKey 是否正确、本机与服务器时钟是否同步、"
              "SaaS 是否需要把 service 设为 ioa。")
    return 0 if ok else 4


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    handlers = {
        "init": cmd_init,
        "test": cmd_test,
        "call": cmd_call,
        "encrypt": cmd_encrypt,
        "pubkey": cmd_pubkey,
        "grant": cmd_grant,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
