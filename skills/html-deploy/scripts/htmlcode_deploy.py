#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://www.htmlcode.fun"
UA = "OpenClaw html-deploy skill"


def request_json(url: str, method: str = "GET", payload: dict | None = None):
    data = None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"success": False, "error": body}
        return e.code, parsed


def print_result(status: int, data: dict) -> int:
    result = {"httpStatus": status, **data}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if status == 429 and data.get("retryAfterSeconds"):
        print(f"Retry after {data['retryAfterSeconds']} seconds.", file=sys.stderr)
    if data.get("preserveHint"):
        print(f"\nPreserve hint: {data['preserveHint']}", file=sys.stderr)
    return 0 if 200 <= status < 300 and data.get("success", True) is not False else 1


def read_html(path_arg: str) -> tuple[pathlib.Path, str]:
    path = pathlib.Path(path_arg)
    return path, path.read_text(encoding="utf-8")


def fetch_version_record(code_arg: str, version_arg: str) -> dict | None:
    code = urllib.parse.quote(code_arg, safe="")
    status, data = request_json(f"{BASE}/api/deploys/{code}/versions")
    if not (200 <= status < 300) or not data.get("success"):
        raise SystemExit(
            "Could not inspect version history before editing: "
            + json.dumps({"httpStatus": status, **data}, ensure_ascii=False)
        )
    for item in data.get("versions", []):
        if str(item.get("versionNumber")) == str(version_arg) or str(item.get("id")) == str(version_arg):
            return item
    raise SystemExit(f"Version {version_arg!r} was not found for code {code_arg!r}.")


def ensure_unliked_version(code_arg: str, version_arg: str, action: str) -> None:
    item = fetch_version_record(code_arg, version_arg)
    like_count = int(item.get("likeCount") or 0)
    if like_count > 0:
        raise SystemExit(
            f"Refusing to {action} {code_arg} version {item.get('versionNumber')}: "
            f"likeCount={like_count}. Liked versions are preserved snapshots; append a new version instead."
        )


def require_description(args):
    if not args.description:
        raise SystemExit("--description is required by htmlcode.fun (one concise sentence, max 240 chars).")
    if len(args.description) > 240:
        raise SystemExit("--description must be at most 240 characters.")


def deploy(args):
    require_description(args)
    path, html = read_html(args.file)
    payload = {
        "filename": args.filename or path.name,
        "content": html,
        "description": args.description,
    }
    if args.title:
        payload["title"] = args.title
    if args.code:
        payload["enableCustomCode"] = True
        payload["customCode"] = args.code
        if args.create_version:
            payload["createVersion"] = True
    status, data = request_json(f"{BASE}/api/deploy", method="POST", payload=payload)
    return print_result(status, data)


def append_version(args):
    require_description(args)
    path, html = read_html(args.file)
    payload = {
        "filename": args.filename or path.name,
        "content": html,
        "description": args.description,
        "enableCustomCode": True,
        "customCode": args.code,
        "createVersion": True,
    }
    if args.title:
        payload["title"] = args.title
    status, data = request_json(f"{BASE}/api/deploy", method="POST", payload=payload)
    return print_result(status, data)


def overwrite_version(args):
    require_description(args)
    ensure_unliked_version(args.code, args.version, "overwrite")
    path, html = read_html(args.file)
    payload = {
        "content": html,
        "description": args.description,
        "filename": args.filename or path.name,
    }
    if args.title:
        payload["title"] = args.title
    version = urllib.parse.quote(str(args.version), safe="")
    code = urllib.parse.quote(args.code, safe="")
    status, data = request_json(f"{BASE}/api/deploys/{code}/versions/{version}", method="PATCH", payload=payload)
    return print_result(status, data)


def set_version_status(args):
    if args.status not in {"active", "inactive"}:
        raise SystemExit("status must be active or inactive")
    ensure_unliked_version(args.code, args.version, f"set status to {args.status} for")
    version = urllib.parse.quote(str(args.version), safe="")
    code = urllib.parse.quote(args.code, safe="")
    payload = {"status": args.status}
    status, data = request_json(f"{BASE}/api/deploys/{code}/versions/{version}", method="PATCH", payload=payload)
    return print_result(status, data)


def delete_version(args):
    ensure_unliked_version(args.code, args.version, "delete")
    version = urllib.parse.quote(str(args.version), safe="")
    code = urllib.parse.quote(args.code, safe="")
    status, data = request_json(f"{BASE}/api/deploys/{code}/versions/{version}", method="DELETE")
    return print_result(status, data)


def versions(args):
    code = urllib.parse.quote(args.code, safe="")
    status, data = request_json(f"{BASE}/api/deploys/{code}/versions")
    return print_result(status, data)


def set_current(args):
    code = urllib.parse.quote(args.code, safe="")
    payload: dict[str, int | str] = {}
    if args.version_id:
        payload["versionId"] = args.version_id
    else:
        try:
            payload["versionNumber"] = int(args.version)
        except ValueError:
            payload["versionId"] = args.version
    status, data = request_json(f"{BASE}/api/deploys/{code}/current", method="PATCH", payload=payload)
    return print_result(status, data)


def get_content(args):
    query_data = {"code": args.code}
    if args.version:
        query_data["version"] = args.version
    if args.download:
        query_data["download"] = 1
    query = urllib.parse.urlencode(query_data)
    url = f"{BASE}/api/deploy/content?{query}"

    if not args.download:
        status, data = request_json(url)
        if not (200 <= status < 300) or not data.get("success"):
            print(json.dumps({"httpStatus": status, **data}, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        content = data.get("content")
        if not isinstance(content, str):
            print(json.dumps({"httpStatus": status, **data}, ensure_ascii=False, indent=2), file=sys.stderr)
            return 1
        if args.output:
            pathlib.Path(args.output).write_text(content, encoding="utf-8")
        else:
            sys.stdout.write(content)
        return 0

    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/html,*/*"})
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        sys.stderr.write(e.read().decode("utf-8", "replace"))
        return 1
    if args.output:
        pathlib.Path(args.output).write_bytes(body)
    else:
        try:
            sys.stdout.write(body.decode("utf-8"))
        except UnicodeDecodeError:
            sys.stdout.buffer.write(body)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Deploy and manage single-file HTML pages on htmlcode.fun")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_deploy = sub.add_parser("deploy", help="Deploy a new HTML page; add --code for a stable short code")
    p_deploy.add_argument("file", help="Path to an HTML file")
    p_deploy.add_argument("--description", required=True, help="Required concise description, max 240 chars")
    p_deploy.add_argument("--title", help="Optional title metadata")
    p_deploy.add_argument("--filename", help="Filename sent to the API")
    p_deploy.add_argument("--code", help="Stable custom short code")
    p_deploy.add_argument("--create-version", action="store_true", help="Append a version if --code already exists")
    p_deploy.set_defaults(func=deploy)

    p_append = sub.add_parser("append", help="Append a new version to an existing stable short code")
    p_append.add_argument("code", help="Existing or desired stable short code")
    p_append.add_argument("file", help="Path to an HTML file")
    p_append.add_argument("--description", required=True, help="Required concise description, max 240 chars")
    p_append.add_argument("--title", help="Optional title metadata")
    p_append.add_argument("--filename", help="Filename sent to the API")
    p_append.set_defaults(func=append_version)

    p_overwrite = sub.add_parser("overwrite", help="Overwrite one unlocked version (likeCount must be 0)")
    p_overwrite.add_argument("code", help="Short code")
    p_overwrite.add_argument("version", help="Version number or version UUID")
    p_overwrite.add_argument("file", help="Path to an HTML file")
    p_overwrite.add_argument("--description", required=True, help="Required concise description, max 240 chars")
    p_overwrite.add_argument("--title", help="Optional title metadata")
    p_overwrite.add_argument("--filename", help="Filename sent to the API")
    p_overwrite.set_defaults(func=overwrite_version)

    p_status = sub.add_parser("status", help="Publish or unpublish one unlocked version")
    p_status.add_argument("code", help="Short code")
    p_status.add_argument("version", help="Version number or version UUID")
    p_status.add_argument("status", choices=["active", "inactive"])
    p_status.set_defaults(func=set_version_status)

    p_delete = sub.add_parser("delete-version", help="Delete one unlocked version; use carefully")
    p_delete.add_argument("code", help="Short code")
    p_delete.add_argument("version", help="Version number or version UUID")
    p_delete.set_defaults(func=delete_version)

    p_versions = sub.add_parser("versions", help="List version history for a short code")
    p_versions.add_argument("code", help="Short code")
    p_versions.set_defaults(func=versions)

    p_current = sub.add_parser("current", help="Switch current public version")
    p_current.add_argument("code", help="Short code")
    p_current.add_argument("version", help="Version number or version UUID")
    p_current.add_argument("--version-id", action="store_true", help="Treat version argument as versionId")
    p_current.set_defaults(func=set_current)

    p_get = sub.add_parser("get", help="Fetch deployed content by code")
    p_get.add_argument("code", help="Existing deployed short code")
    p_get.add_argument("--version", help="Version number or version UUID")
    p_get.add_argument("--download", action="store_true", help="Request download mode")
    p_get.add_argument("--output", help="Write response to a file")
    p_get.set_defaults(func=get_content)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
