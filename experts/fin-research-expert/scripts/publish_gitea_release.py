#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def api_url(server_url: str, repo: str, path: str) -> str:
    repo_path = "/".join(urllib.parse.quote(part, safe="") for part in repo.split("/"))
    return f"{server_url.rstrip('/')}/api/v1/repos/{repo_path}{path}"


def request_json(
    *,
    method: str,
    url: str,
    token: str,
    payload: dict[str, Any] | None = None,
    expected: tuple[int, ...] = (200,),
    allow_404: bool = False,
) -> dict[str, Any] | None:
    body = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"token {token}",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
            if response.status not in expected:
                raise RuntimeError(f"{method} {url} returned HTTP {response.status}: {data[:500]!r}")
            if not data:
                return {}
            return json.loads(data.decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if allow_404 and error.code == 404:
            return None
        raise RuntimeError(f"{method} {url} failed: HTTP {error.code} {detail}") from error


def multipart_body(file_path: Path, field_name: str = "attachment") -> tuple[bytes, str]:
    boundary = "----codex-gitea-release-boundary"
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    chunks = [
        f"--{boundary}\r\n".encode("utf-8"),
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{file_path.name}"\r\n'
        ).encode("utf-8"),
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
        file_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode("utf-8"),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def request_upload(*, url: str, token: str, file_path: Path) -> None:
    body, content_type = multipart_body(file_path)
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Accept": "application/json",
            "Authorization": f"token {token}",
            "Content-Type": content_type,
            "Content-Length": str(len(body)),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            if response.status not in (200, 201):
                detail = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"upload returned HTTP {response.status}: {detail}")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upload {file_path.name} failed: HTTP {error.code} {detail}") from error


def release_assets(release: dict[str, Any]) -> list[dict[str, Any]]:
    assets = release.get("assets")
    if isinstance(assets, list):
        return assets
    attachments = release.get("attachments")
    if isinstance(attachments, list):
        return attachments
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update a Gitea release and upload assets.")
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--token-env", default="GITEA_TOKEN")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--asset", action="append", default=[])
    args = parser.parse_args()

    token = os.environ.get(args.token_env, "").strip()
    if not token:
        raise SystemExit(f"{args.token_env} is required")

    body = Path(args.body_file).read_text(encoding="utf-8")
    release = request_json(
        method="GET",
        url=api_url(args.server_url, args.repo, f"/releases/tags/{urllib.parse.quote(args.tag, safe='')}"),
        token=token,
        allow_404=True,
    )
    payload = {
        "tag_name": args.tag,
        "target_commitish": args.target,
        "name": args.name,
        "body": body,
        "draft": False,
        "prerelease": False,
    }
    if release is None:
        release = request_json(
            method="POST",
            url=api_url(args.server_url, args.repo, "/releases"),
            token=token,
            payload=payload,
            expected=(201,),
        )
    else:
        release_id = release["id"]
        release = request_json(
            method="PATCH",
            url=api_url(args.server_url, args.repo, f"/releases/{release_id}"),
            token=token,
            payload=payload,
            expected=(200,),
        )

    if not release:
        raise SystemExit("Gitea release response was empty")
    release_id = release["id"]
    release = request_json(
        method="GET",
        url=api_url(args.server_url, args.repo, f"/releases/{release_id}"),
        token=token,
        expected=(200,),
    ) or release
    existing_assets = {asset.get("name"): asset for asset in release_assets(release)}
    for asset_path_text in args.asset:
        asset_path = Path(asset_path_text).resolve()
        if not asset_path.is_file():
            raise SystemExit(f"missing asset: {asset_path}")
        existing = existing_assets.get(asset_path.name)
        if existing and existing.get("id") is not None:
            request_json(
                method="DELETE",
                url=api_url(args.server_url, args.repo, f"/releases/{release_id}/assets/{existing['id']}"),
                token=token,
                expected=(204,),
            )
        upload_url = api_url(
            args.server_url,
            args.repo,
            f"/releases/{release_id}/assets?name={urllib.parse.quote(asset_path.name, safe='')}",
        )
        request_upload(url=upload_url, token=token, file_path=asset_path)

    print(json.dumps({"release_id": release_id, "tag": args.tag, "assets": args.asset}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
