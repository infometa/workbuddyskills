"""
Drug labeling &amp; medication info search - script (depends on sinohealth_skills_sdk)

- SKILLS_BIZ_TYPE / SKILLS_BIZ_TOKEN: must be provided by environment, see SKILL.md

Usage:
    python drug_instructions.py "&lt;user query&gt;"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from skills_sdk import SkillsClient

_ENV_OUT_FILE = "SKILLS_QUERY_OUTPUT_FILE"
_ENV_TYPE = "SKILLS_BIZ_TYPE"
_ENV_TOKEN = "SKILLS_BIZ_TOKEN"

_SKILL_URL = "/dataset/drug"


def _format_output(data: Any) -> str:
    if isinstance(data, dict) and "choices" in data:
        choices = data["choices"]
        if choices and isinstance(choices[0], dict):
            content = choices[0].get("message", {}).get("content", "")
            if content:
                try:
                    inner = json.loads(content)
                    if isinstance(inner, dict):
                        t = inner.get("text")
                        if isinstance(t, str) and t.strip():
                            return t
                except (json.JSONDecodeError, TypeError):
                    pass
                return content
    if isinstance(data, dict):
        text = data.get("text")
        if isinstance(text, str) and text.strip():
            return text
    if isinstance(data, str) and data.strip():
        return data
    return json.dumps(data, ensure_ascii=False, indent=2)


def _emit_result_to_file(skill_dir: Path, text: str) -> None:
    override = (os.environ.get(_ENV_OUT_FILE) or "").strip()
    if override:
        out = Path(override).expanduser().resolve()
    else:
        out = skill_dir / "query_result_full.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    # Output only a relative filename (ASCII-safe) to stdout.
    # The Agent should resolve the full path by combining the Skill root
    # directory with this filename, rather than relying on stdout for the
    # absolute path — terminal environments may not render CJK characters
    # in stdout correctly.
    print(out.name, flush=True)


def _resolve_biz_credentials() -> tuple[str, str]:
    biz_type = (os.environ.get(_ENV_TYPE) or "").strip()
    biz_token = (os.environ.get(_ENV_TOKEN) or "").strip()
    return biz_type, biz_token


def main():
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
    try:
        from pathlib import Path as _PathSkillRoot
        _skill_root = _PathSkillRoot(__file__).resolve().parent.parent.parent
        if str(_skill_root) not in sys.path:
            sys.path.insert(0, str(_skill_root))
        from skill_stdio_utf8 import ensure_utf8_stdio
        ensure_utf8_stdio()
    except ImportError:
        pass

    skill_dir = Path(__file__).resolve().parent.parent

    parser = argparse.ArgumentParser(description="Drug labeling &amp; medication info search")
    parser.add_argument("prompt", help="User's query")
    args = parser.parse_args()
    prompt = (args.prompt or "").strip()
    if not prompt:
        print("Error: prompt cannot be empty", file=sys.stderr)
        sys.exit(2)

    biz_type, biz_token = _resolve_biz_credentials()
    if not biz_type or not biz_token:
        print(
            "Error: SKILLS_BIZ_TYPE or SKILLS_BIZ_TOKEN not set.\n"
            "See SKILL.md: try connect_cloud_service to get token; if successful, set both to 'workbuddy' and export;\n"
            "if not available, pre-configure valid SKILLS_BIZ_TYPE and SKILLS_BIZ_TOKEN in environment.",
            file=sys.stderr,
        )
        sys.exit(2)
    os.environ[_ENV_TYPE] = biz_type

    client = SkillsClient(biz_type=biz_type, biz_token=biz_token, stream=False)
    try:
        response = client.call_skill(
            _SKILL_URL,
            {
                "prompt": prompt,
                "msgId": "debug",
                "medBase": "药品",
            }
        )
        if response.success:
            data = response.data
            if isinstance(data, dict) and data.get("error") is not None:
                err = data["error"]
                msg = (
                    err
                    if isinstance(err, str)
                    else json.dumps(err, ensure_ascii=False)
                )
                print(msg, file=sys.stderr)
                sys.exit(1)
            _emit_result_to_file(skill_dir, _format_output(data))
        else:
            err = response.error or "调用失败"
            print(err, file=sys.stderr)
            low = str(err).lower()
            if any(x in low for x in ("401", "403", "认证", "鉴权", "token", "unauthorized")):
                print("Hint: Authentication failed, please check service or network configuration.", file=sys.stderr)
            sys.exit(1)
    finally:
        client.close()


if __name__ == "__main__":
    main()
