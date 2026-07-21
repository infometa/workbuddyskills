#!/usr/bin/env python3
"""
Extract leadership-style signals from .eml or .mbox email archives.
"""

from __future__ import annotations

import argparse
import mailbox
from email import policy
from email.parser import BytesParser
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract target messages from .eml or .mbox email files.")
    parser.add_argument("--file", required=True, help="Input .eml or .mbox file.")
    parser.add_argument("--target", required=True, help="Target sender name or email.")
    parser.add_argument("--output", required=True, help="Output txt file.")
    return parser.parse_args()


def get_body(message) -> str:
    if message.is_multipart():
        parts = []
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                try:
                    parts.append(part.get_content())
                except Exception:
                    continue
        return "\n".join(parts).strip()
    try:
        return message.get_content().strip()
    except Exception:
        return ""


def format_message(sender: str, subject: str, body: str) -> str:
    compact_body = " ".join(body.split())
    if len(compact_body) > 400:
        compact_body = compact_body[:397] + "..."
    return f"From: {sender}\nSubject: {subject}\nBody: {compact_body}"


def main() -> int:
    args = parse_args()
    path = Path(args.file)
    target = args.target.casefold()
    hits: list[str] = []

    if path.suffix.lower() == ".eml":
        message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        sender = str(message.get("from", ""))
        if target in sender.casefold():
            hits.append(format_message(sender, str(message.get("subject", "")), get_body(message)))
    else:
        box = mailbox.mbox(path)
        for message in box:
            sender = str(message.get("from", ""))
            if target in sender.casefold():
                hits.append(format_message(sender, str(message.get("subject", "")), get_body(message)))

    out = [f"# Email extract for {args.target}", ""]
    out.extend(hits or ["No matching messages found."])
    Path(args.output).write_text("\n\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
