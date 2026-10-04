#!/usr/bin/env python3
"""Shared normalization + hashing for the brand-conflict lexicon.

The lexicon ships as opaque digests, so build and scan must agree byte for byte
on how a phrase is turned into one. Keep this module free of dependencies —
both the offline builder and the runtime scanner import it directly.
"""
import hashlib
import re

DIGEST_BYTES = 8
TOKEN_RE = re.compile(r"[a-z0-9]+")

def tokenize(text: str) -> list:
    """Lowercase and split on anything that is not alphanumeric.

    "GoPro Hero-11" -> ["gopro", "hero", "11"]; "3M" -> ["3m"].
    """
    return TOKEN_RE.findall(text.casefold())

# A phrase whose tokens concatenate to at least this many characters may also be
# indexed in its compact form, so "Go-Pro" / "go pro" still reach the "GoPro" entry.
# Shorter joins collide with ordinary word pairs far too often to be useful.
MIN_COMPACT_CHARS = 5

def digest(tokens) -> bytes:
    """Digest a token sequence. Callers must pass already-tokenized input."""
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).digest()[:DIGEST_BYTES]

def compact_digest(tokens):
    """Digest the punctuation-free join of a phrase, or None when it is too short.

    Only single-token lexicon entries get a compact form: joining a real multi-word
    mark ("the grinch") would invent a spelling nobody writes, while joining a
    seller's hyphenated spelling of a one-word mark is exactly what we want to catch.
    """
    joined = "".join(tokens)
    if len(joined) < MIN_COMPACT_CHARS:
        return None
    return hashlib.sha256(joined.encode("utf-8")).digest()[:DIGEST_BYTES]
