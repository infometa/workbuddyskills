#!/usr/bin/env bash
# Original implementation by BytesAgain (bytesagain.com)
# This is independent code, not derived from any third-party source
# License: MIT
# Joplin-style note manager — personal knowledge base
set -euo pipefail
NOTES_DIR="${NOTES_DIR:-$HOME/.notes}"
mkdir -p "$NOTES_DIR"
CMD="${1:-help}"; shift 2>/dev/null || true
case "$CMD" in
help) echo "Note Manager — personal knowledge base
Commands:
  new [title]         Create new note
  list [n]            List recent notes (default 10)
  search <query>      Full-text search
  view <id>           View a note
  edit <id> <text>    Append to note
  tag <tag>           List notes by tag
  tags                Show all tags
  notebook <name>     List notes in notebook
  notebooks           List all notebooks
  export [format]     Export all (md/json/html)
  trash <id>          Move to trash
  stats               Note statistics
  info                Version info
Powered by BytesAgain | bytesagain.com";;
new)
    title="${*:-Untitled $(date +%H%M%S)}"
    id=$(date +%s)
    notebook="default"
    mkdir -p "$NOTES_DIR/$notebook"
    cat > "$NOTES_DIR/$notebook/${id}.md" << EOF
---
id: $id
title: $title
created: $(date '+%Y-%m-%d %H:%M')
tags: []
notebook: $notebook
---

# $title

EOF
    echo "✅ Note created: #$id — $title"
    echo "   Path: $NOTES_DIR/$notebook/${id}.md";;
list)
    n="${1:-10}"
    echo "📝 Recent Notes:"
    find "$NOTES_DIR" -name "*.md" -type f 2>/dev/null | while read f; do
        title=$(grep "^title:" "$f" 2>/dev/null | head -1 | cut -d: -f2- | xargs)
        created=$(grep "^created:" "$f" 2>/dev/null | head -1 | cut -d: -f2- | xargs)
        id=$(grep "^id:" "$f" 2>/dev/null | head -1 | awk '{print $2}')
        nb=$(basename "$(dirname "$f")")
        [ -n "$title" ] && echo "  [$id] $created | $nb | $title"
    done | sort -t'|' -k1 -r | head -"$n"
    echo "  Total: $(find "$NOTES_DIR" -name "*.md" | wc -l) notes";;
search)
    q="${1:-}"; [ -z "$q" ] && { echo "Usage: search <query>"; exit 1; }
    echo "🔍 Search: $q"
    grep -rl "$q" "$NOTES_DIR" 2>/dev/null | while read f; do
        title=$(grep "^title:" "$f" 2>/dev/null | head -1 | cut -d: -f2- | xargs)
        match=$(grep -n -m1 "$q" "$f" | head -1)
        echo "  📄 $title"
        echo "     $match"
    done;;
view)
    id="${1:-}"; [ -z "$id" ] && { echo "Usage: view <id>"; exit 1; }
    f=$(find "$NOTES_DIR" -name "${id}.md" 2>/dev/null | head -1)
    [ -z "$f" ] && { echo "Note #$id not found"; exit 1; }
    cat "$f";;
edit)
    id="${1:-}"; shift 2>/dev/null || true; text="$*"
    [ -z "$id" ] && { echo "Usage: edit <id> <text>"; exit 1; }
    f=$(find "$NOTES_DIR" -name "${id}.md" 2>/dev/null | head -1)
    [ -z "$f" ] && { echo "Not found"; exit 1; }
    echo "" >> "$f"; echo "$text" >> "$f"
    echo "✅ Appended to #$id";;
tag)
    t="${1:-}"; [ -z "$t" ] && { echo "Usage: tag <tag>"; exit 1; }
    echo "🏷 Notes tagged: #$t"
    grep -rl "$t" "$NOTES_DIR" 2>/dev/null | while read f; do
        title=$(grep "^title:" "$f" 2>/dev/null | head -1 | cut -d: -f2- | xargs)
        echo "  📄 $title"
    done;;
tags)
    echo "🏷 All Tags:"
    grep -h "^tags:" "$NOTES_DIR"/*/*.md "$NOTES_DIR"/*.md 2>/dev/null | sed 's/tags://;s/\[//;s/\]//;s/,/\n/g' | sort | uniq -c | sort -rn | head -20;;
notebook)
    nb="${1:-default}"
    echo "📒 Notebook: $nb"
    if [ -d "$NOTES_DIR/$nb" ]; then
        ls "$NOTES_DIR/$nb/"*.md 2>/dev/null | while read f; do
            title=$(grep "^title:" "$f" 2>/dev/null | head -1 | cut -d: -f2- | xargs)
            echo "  📄 $title"
        done
    else echo "  (empty)"; fi;;
notebooks)
    echo "📚 Notebooks:"
    for d in "$NOTES_DIR"/*/; do
        [ -d "$d" ] || continue
        nb=$(basename "$d")
        count=$(ls "$d"*.md 2>/dev/null | wc -l)
        echo "  📒 $nb ($count notes)"
    done;;
export)
    fmt="${1:-md}"
    case "$fmt" in
        md) echo "# Notes Export — $(date +%Y-%m-%d)"; echo ""; find "$NOTES_DIR" -name "*.md" | while read f; do cat "$f"; echo -e "\n---\n"; done;;
        json) python3 -c "
import json, os, glob
notes = []
for f in glob.glob('$NOTES_DIR/*/*.md') + glob.glob('$NOTES_DIR/*.md'):
    with open(f) as fh: content = fh.read()
    notes.append({'file': f, 'content': content[:500]})
print(json.dumps(notes, indent=2, ensure_ascii=False))
";;
        *) echo "Formats: md, json";;
    esac;;
trash)
    id="${1:-}"; [ -z "$id" ] && { echo "Usage: trash <id>"; exit 1; }
    f=$(find "$NOTES_DIR" -name "${id}.md" 2>/dev/null | head -1)
    [ -z "$f" ] && { echo "Not found"; exit 1; }
    mkdir -p "$NOTES_DIR/.trash"
    mv "$f" "$NOTES_DIR/.trash/"
    echo "🗑 Note #$id moved to trash";;
stats)
    total=$(find "$NOTES_DIR" -name "*.md" -not -path "*/.trash/*" 2>/dev/null | wc -l)
    notebooks=$(find "$NOTES_DIR" -mindepth 1 -maxdepth 1 -type d -not -name ".trash" 2>/dev/null | wc -l)
    trashed=$(find "$NOTES_DIR/.trash" -name "*.md" 2>/dev/null | wc -l)
    words=$(find "$NOTES_DIR" -name "*.md" -not -path "*/.trash/*" -exec cat {} + 2>/dev/null | wc -w)
    echo "📊 Note Stats:"
    echo "  Notes: $total"
    echo "  Notebooks: $notebooks"
    echo "  Trashed: $trashed"
    echo "  Total words: $words";;
info) echo "Note Manager v1.0.0"; echo "Personal knowledge base tool"; echo "Powered by BytesAgain | bytesagain.com";;
*) echo "Unknown: $CMD"; exit 1;;
esac
