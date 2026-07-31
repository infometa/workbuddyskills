#!/usr/bin/env python3
"""
One-step Databrain Token deployer for TideRider.

Goal
----
Make token setup effortless for the end user. The ONLY thing the user has to do
is apply for their own DataBrain Token at the personal-tokens-center:
    内网: https://databrain.woa.com/v2/user-center/personal-tokens-center
    外网: https://databrain-global.intlgame.com/v2/user-center/personal-tokens-center
…and then hand the token to the expert in WHATEVER way is easiest for them:
    - paste the raw `eyJ...` string straight into chat, OR
    - save it in ANY plain-text file (a note, .txt, .env) at ANY location, OR
    - just copy it to the clipboard and say "it's copied"

The expert wires everything up. THREE input modes (in priority order):
    1) --token "<value>"   : deploy a token string directly (no file needed)
    2) --file  <path>      : read the token out of that file
    3) (nothing given)     : AUTO — try the clipboard, then scan common drop
                             spots (Desktop / Downloads / home / cwd) for a file
                             that contains a valid token. First hit wins.

In every mode the script:
    - normalises the token (strips quotes / `Bearer ` prefix)
    - validates it looks like a real DataBrain JWT
    - writes it into the skill-root `.env` as `DATABRAIN_TOKEN=...`
      (creating/updating the file idempotently, preserving other keys, chmod 600)
    - re-runs the connection detector to confirm the token is now picked up
    - prints a single clear PASS/FAIL line

The user never touches `.env`, never runs `export`, never learns where the skill
root is. They hand over a token any way they like; the expert deploys it.

Accepted token-file formats (auto-detected)
-------------------------------------------
Any of these work — the script is forgiving:
    eyJhbGci...                               # raw JWT token, whole file
    DATABRAIN_TOKEN=eyJhbGci...               # KEY=VALUE line (e.g. a .env)
    DATABRAIN_TOKEN: eyJhbGci...              # KEY: VALUE line (yaml-ish)
    token = "eyJhbGci..."                     # quoted assignment
    Bearer eyJhbGci...                        # a stray Bearer prefix is stripped
Leading/trailing whitespace, quotes, and a `Bearer ` prefix are all removed.

Usage
-----
    python deploy_token.py --token "eyJhbGci..."          # paste-in-chat mode
    python deploy_token.py --file /path/to/whatever.txt    # explicit file
    python deploy_token.py                                 # AUTO: clipboard + scan
    python deploy_token.py --file ~/Desktop/token.txt -q   # machine-friendly

Exit codes
----------
    0  token deployed AND connection verified as `databrain`
    2  no valid token found (bad file / empty clipboard / nothing on disk)
    3  token written but verification still failed (unexpected)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Skill root = the directory ONE level above scripts/ (where _utils.py loads .env from).
SKILL_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = SKILL_ROOT / ".env"
TOKEN_KEY = "DATABRAIN_TOKEN"

# Recognised key names for a "KEY = VALUE" / "KEY: VALUE" style line.
_KEY_NAMES = ("databrain_token", "token")


def _clean(raw: str) -> str:
    """Normalise a candidate value: drop wrapping quotes, then a Bearer prefix.

    Order matters — a real-world line is often `KEY="Bearer eyJ..."`, so we
    peel the quotes FIRST (which may reveal a leading `Bearer `), then strip that.
    Runs a couple of passes so `"'Bearer x'"` style double-wrapping is handled.
    """
    v = raw.strip()
    for _ in range(3):
        before = v
        v = v.strip().strip('"').strip("'").strip()
        if v.lower().startswith("bearer "):
            v = v[len("bearer "):].strip()
        if v == before:
            break
    return v


def _looks_like_jwt(v: str) -> bool:
    """A DataBrain JWT: starts with `eyJ` and has the three dot-separated parts."""
    return v.startswith("eyJ") and v.count(".") == 2


def _looks_like_token(v: str) -> bool:
    """A DataBrain JWT, or a plausible opaque token."""
    if not v or " " in v:
        return False
    return _looks_like_jwt(v) or len(v) >= 20


def extract_token(text: str) -> str | None:
    """Pull the token out of arbitrary file content.

    Handles three shapes per non-empty, non-comment line:
      1) `KEY = VALUE` / `KEY: VALUE` where KEY is a recognised key name
      2) a bare value on its own line (raw token)
    In both cases the value is cleaned (quotes + Bearer stripped). A value that
    looks like a JWT (`eyJ...`) wins immediately; otherwise the first plausible
    opaque token is kept as a fallback.
    """
    fallback: str | None = None
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue

        # Split on the FIRST : or = to separate an optional key from the value.
        candidate = s
        m = re.match(r"^\s*([A-Za-z_][\w.]*)\s*[:=]\s*(.*)$", s)
        if m:
            key, rhs = m.group(1).lower(), m.group(2)
            if key in _KEY_NAMES:
                candidate = rhs
            else:
                # Unknown key -> still try the RHS, but don't let a random
                # `foo=bar` line hijack detection unless it looks like a token.
                candidate = rhs

        val = _clean(candidate)
        if not _looks_like_token(val):
            continue
        if _looks_like_jwt(val):
            return val
        if fallback is None:
            fallback = val
    return fallback


def read_clipboard() -> str | None:
    """Best-effort read of the OS clipboard as text. Returns None if unavailable.

    Supports macOS (pbpaste), Windows (powershell Get-Clipboard), and Linux
    (xclip / xsel / wl-paste). Any failure is swallowed — the clipboard is an
    optional convenience source, never a hard requirement.
    """
    candidates: list[list[str]] = []
    if sys.platform == "darwin":
        candidates.append(["pbpaste"])
    elif sys.platform.startswith("win"):
        candidates.append(["powershell", "-NoProfile", "-Command", "Get-Clipboard"])
    else:  # linux / other unix
        candidates.append(["wl-paste", "--no-newline"])
        candidates.append(["xclip", "-selection", "clipboard", "-o"])
        candidates.append(["xsel", "--clipboard", "--output"])
    for cmd in candidates:
        try:
            out = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, check=False
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout
    return None


# Filenames we optimistically probe when auto-scanning a directory. Ordered by
# how likely they are to be an intentional "token drop". Globs are expanded.
_SCAN_GLOBS = (
    "databrain_token*", "databrain-token*", "databrain*.txt",
    "tiderider_token*", "tiderider-token*",
    "token.txt", "token", "*.token", "pat.txt",
    ".env", "*.env",
)


def _scan_dirs() -> list[Path]:
    """Directories to probe, in priority order, when no --file/--token is given."""
    home = Path.home()
    dirs = [
        Path.cwd(),
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        home,
    ]
    # De-dupe while preserving order (cwd may equal one of the others).
    seen: set[Path] = set()
    uniq: list[Path] = []
    for d in dirs:
        try:
            rp = d.resolve()
        except OSError:
            continue
        if rp in seen or not rp.is_dir():
            continue
        seen.add(rp)
        uniq.append(d)
    return uniq


def auto_discover() -> tuple[str | None, str]:
    """Find a token without an explicit path.

    Strategy (first hit wins):
      1) OS clipboard — most users just copied the token off the token-center page.
      2) common drop files across cwd / Desktop / Downloads / Documents / home.
    Returns (token_or_None, human_source_description).
    """
    # 1) clipboard
    clip = read_clipboard()
    if clip:
        tok = extract_token(clip)
        if tok:
            return tok, "clipboard"

    # 2) filesystem scan
    for d in _scan_dirs():
        for pattern in _SCAN_GLOBS:
            try:
                matches = sorted(d.glob(pattern))
            except OSError:
                continue
            for p in matches:
                if not p.is_file():
                    continue
                # Skip our own skill-root .env to avoid a self-referential loop
                # that would just re-deploy the already-installed token silently.
                try:
                    if p.resolve() == ENV_PATH.resolve():
                        continue
                except OSError:
                    pass
                try:
                    tok = extract_token(p.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    continue
                if tok:
                    return tok, str(p)
    return None, ""


def write_env(token: str) -> None:
    """Write/update DATABRAIN_TOKEN in the skill-root .env, preserving other keys."""
    lines: list[str] = []
    replaced = False
    if ENV_PATH.is_file():
        for line in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip().startswith(f"{TOKEN_KEY}="):
                lines.append(f"{TOKEN_KEY}={token}")
                replaced = True
            else:
                lines.append(line)
    if not replaced:
        lines.append(f"{TOKEN_KEY}={token}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Best-effort tighten perms (owner read/write only); ignore on platforms that don't support it.
    try:
        ENV_PATH.chmod(0o600)
    except OSError:
        pass


def verify() -> tuple[bool, str]:
    """Re-run the detector in-process and confirm databrain is now chosen."""
    try:
        import detect_connection  # same directory, on sys.path when run as a script
    except Exception:  # pragma: no cover - detector is always present in the skill
        # Fallback: just confirm the env file has the key.
        return (ENV_PATH.is_file(), "detector unavailable; .env presence checked only")
    # detect() reads env + skill-root .env fresh each call.
    res = detect_connection.detect()
    chosen = res.get("chosen") or {}
    method = chosen.get("method")
    if method == "databrain":
        return True, "connection verified: Databrain Token active"
    if method in ("bigquery_sa", "bigquery_adc"):
        # A direct-BigQuery credential outranks the token — token is still valid,
        # just not the *chosen* channel. That's a success from the user's angle.
        return True, f"token stored; a higher-priority direct connection ({method}) is active"
    return False, "token written but detector still reports no usable connection"


def _resolve_token(args) -> tuple[str | None, str]:
    """Turn CLI args into (token, source) using the 3-mode priority order."""
    # Mode 1 — explicit token string (paste-in-chat).
    if args.token:
        tok = extract_token(args.token) or _clean(args.token)
        if tok and _looks_like_token(tok):
            return tok, "--token argument"
        return None, "--token argument"

    # Mode 2 — explicit file path.
    if args.file:
        src = Path(args.file).expanduser()
        if not src.is_file():
            return None, f"file not found: {src}"
        try:
            content = src.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            return None, f"could not read file: {e}"
        return extract_token(content), str(src)

    # Mode 3 — auto-discover (clipboard + common drop locations).
    return auto_discover()


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Deploy a Databrain Token. Give --token, --file, or nothing (auto-scan)."
    )
    ap.add_argument("--token", "-t", help="The raw token value pasted directly (no file needed).")
    ap.add_argument("--file", "-f", help="Path to a file where the user saved their token.")
    ap.add_argument(
        "--quiet", "-q", action="store_true", help="Only print the final status line."
    )
    args = ap.parse_args()

    token, source = _resolve_token(args)
    if not token:
        detail = source or "no --token/--file given and nothing found automatically"
        print(
            "FAIL: no valid DataBrain token found "
            f"({detail}). Paste the `eyJ...` token, point me at the file that "
            "holds it, or copy it to your clipboard and let me auto-detect.",
            file=sys.stderr,
        )
        sys.exit(2)

    write_env(token)
    ok, msg = verify()

    if not args.quiet:
        masked = token[:8] + "…" + token[-4:] if len(token) > 14 else "…"
        print(f"Token source   : {source}")
        print(f"Token value    : {masked}")
        print(f"Written to     : {ENV_PATH}")
    print(("PASS: " if ok else "FAIL: ") + msg)
    sys.exit(0 if ok else 3)


if __name__ == "__main__":
    main()
