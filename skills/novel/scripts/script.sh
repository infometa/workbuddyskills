#!/usr/bin/env bash
# Novel — utility tool
# Powered by BytesAgain | bytesagain.com | hello@bytesagain.com
set -euo pipefail

DATA_DIR="${HOME}/.local/share/novel"
mkdir -p "$DATA_DIR"

_log() { echo "$(date '+%m-%d %H:%M') $1: $2" >> "$DATA_DIR/history.log"; }
_version() { echo "novel v2.0.0"; }

_help() {
    echo "Novel v2.0.0 — utility toolkit"
    echo ""
    echo "Usage: novel <command> [args]"
    echo ""
    echo "Commands:"
    echo "  run                Run"
    echo "  check              Check"
    echo "  convert            Convert"
    echo "  analyze            Analyze"
    echo "  generate           Generate"
    echo "  preview            Preview"
    echo "  batch              Batch"
    echo "  compare            Compare"
    echo "  export             Export"
    echo "  config             Config"
    echo "  status             Status"
    echo "  report             Report"
    echo "  stats              Summary statistics"
    echo "  export <fmt>       Export (json|csv|txt)"
    echo "  search <term>      Search entries"
    echo "  recent             Recent activity"
    echo "  status             Health check"
    echo "  help               Show this help"
    echo "  version            Show version"
    echo ""
    echo "Data: $DATA_DIR"
}

_stats() {
    echo "=== Novel Stats ==="
    local total=0
    for f in "$DATA_DIR"/*.log; do
        [ -f "$f" ] || continue
        local name=$(basename "$f" .log)
        local c=$(wc -l < "$f")
        total=$((total + c))
        echo "  $name: $c entries"
    done
    echo "  ---"
    echo "  Total: $total entries"
    echo "  Data size: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)"
}

_export() {
    local fmt="${1:-json}"
    local out="$DATA_DIR/export.$fmt"
    case "$fmt" in
        json)
            echo "[" > "$out"
            local first=1
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                local name=$(basename "$f" .log)
                while IFS='|' read -r ts val; do
                    [ $first -eq 1 ] && first=0 || echo "," >> "$out"
                    printf '  {"type":"%s","time":"%s","value":"%s"}' "$name" "$ts" "$val" >> "$out"
                done < "$f"
            done
            echo "\n]" >> "$out"
            ;;
        csv)
            echo "type,time,value" > "$out"
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                local name=$(basename "$f" .log)
                while IFS='|' read -r ts val; do echo "$name,$ts,$val" >> "$out"; done < "$f"
            done
            ;;
        txt)
            echo "=== Novel Export ===" > "$out"
            for f in "$DATA_DIR"/*.log; do
                [ -f "$f" ] || continue
                echo "--- $(basename "$f" .log) ---" >> "$out"
                cat "$f" >> "$out"
            done
            ;;
        *) echo "Formats: json, csv, txt"; return 1 ;;
    esac
    echo "Exported to $out ($(wc -c < "$out") bytes)"
}

_status() {
    echo "=== Novel Status ==="
    echo "  Version: v2.0.0"
    echo "  Data dir: $DATA_DIR"
    echo "  Entries: $(cat "$DATA_DIR"/*.log 2>/dev/null | wc -l) total"
    echo "  Disk: $(du -sh "$DATA_DIR" 2>/dev/null | cut -f1)"
    echo "  Last: $(tail -1 "$DATA_DIR/history.log" 2>/dev/null || echo never)"
    echo "  Status: OK"
}

_search() {
    local term="${1:?Usage: novel search <term>}"
    echo "Searching for: $term"
    for f in "$DATA_DIR"/*.log; do
        [ -f "$f" ] || continue
        local m=$(grep -i "$term" "$f" 2>/dev/null || true)
        if [ -n "$m" ]; then
            echo "  --- $(basename "$f" .log) ---"
            echo "$m" | sed 's/^/    /'
        fi
    done
}

_recent() {
    echo "=== Recent Activity ==="
    tail -20 "$DATA_DIR/history.log" 2>/dev/null | sed 's/^/  /' || echo "  No activity yet."
}

case "${1:-help}" in
    run)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent run entries:"
            tail -20 "$DATA_DIR/run.log" 2>/dev/null || echo "  No entries yet. Use: novel run <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/run.log"
            local total=$(wc -l < "$DATA_DIR/run.log")
            echo "  [Novel] run: $input"
            echo "  Saved. Total run entries: $total"
            _log "run" "$input"
        fi
        ;;
    check)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent check entries:"
            tail -20 "$DATA_DIR/check.log" 2>/dev/null || echo "  No entries yet. Use: novel check <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/check.log"
            local total=$(wc -l < "$DATA_DIR/check.log")
            echo "  [Novel] check: $input"
            echo "  Saved. Total check entries: $total"
            _log "check" "$input"
        fi
        ;;
    convert)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent convert entries:"
            tail -20 "$DATA_DIR/convert.log" 2>/dev/null || echo "  No entries yet. Use: novel convert <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/convert.log"
            local total=$(wc -l < "$DATA_DIR/convert.log")
            echo "  [Novel] convert: $input"
            echo "  Saved. Total convert entries: $total"
            _log "convert" "$input"
        fi
        ;;
    analyze)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent analyze entries:"
            tail -20 "$DATA_DIR/analyze.log" 2>/dev/null || echo "  No entries yet. Use: novel analyze <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/analyze.log"
            local total=$(wc -l < "$DATA_DIR/analyze.log")
            echo "  [Novel] analyze: $input"
            echo "  Saved. Total analyze entries: $total"
            _log "analyze" "$input"
        fi
        ;;
    generate)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent generate entries:"
            tail -20 "$DATA_DIR/generate.log" 2>/dev/null || echo "  No entries yet. Use: novel generate <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/generate.log"
            local total=$(wc -l < "$DATA_DIR/generate.log")
            echo "  [Novel] generate: $input"
            echo "  Saved. Total generate entries: $total"
            _log "generate" "$input"
        fi
        ;;
    preview)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent preview entries:"
            tail -20 "$DATA_DIR/preview.log" 2>/dev/null || echo "  No entries yet. Use: novel preview <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/preview.log"
            local total=$(wc -l < "$DATA_DIR/preview.log")
            echo "  [Novel] preview: $input"
            echo "  Saved. Total preview entries: $total"
            _log "preview" "$input"
        fi
        ;;
    batch)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent batch entries:"
            tail -20 "$DATA_DIR/batch.log" 2>/dev/null || echo "  No entries yet. Use: novel batch <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/batch.log"
            local total=$(wc -l < "$DATA_DIR/batch.log")
            echo "  [Novel] batch: $input"
            echo "  Saved. Total batch entries: $total"
            _log "batch" "$input"
        fi
        ;;
    compare)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent compare entries:"
            tail -20 "$DATA_DIR/compare.log" 2>/dev/null || echo "  No entries yet. Use: novel compare <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/compare.log"
            local total=$(wc -l < "$DATA_DIR/compare.log")
            echo "  [Novel] compare: $input"
            echo "  Saved. Total compare entries: $total"
            _log "compare" "$input"
        fi
        ;;
    export)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent export entries:"
            tail -20 "$DATA_DIR/export.log" 2>/dev/null || echo "  No entries yet. Use: novel export <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/export.log"
            local total=$(wc -l < "$DATA_DIR/export.log")
            echo "  [Novel] export: $input"
            echo "  Saved. Total export entries: $total"
            _log "export" "$input"
        fi
        ;;
    config)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent config entries:"
            tail -20 "$DATA_DIR/config.log" 2>/dev/null || echo "  No entries yet. Use: novel config <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/config.log"
            local total=$(wc -l < "$DATA_DIR/config.log")
            echo "  [Novel] config: $input"
            echo "  Saved. Total config entries: $total"
            _log "config" "$input"
        fi
        ;;
    status)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent status entries:"
            tail -20 "$DATA_DIR/status.log" 2>/dev/null || echo "  No entries yet. Use: novel status <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/status.log"
            local total=$(wc -l < "$DATA_DIR/status.log")
            echo "  [Novel] status: $input"
            echo "  Saved. Total status entries: $total"
            _log "status" "$input"
        fi
        ;;
    report)
        shift
        if [ $# -eq 0 ]; then
            echo "Recent report entries:"
            tail -20 "$DATA_DIR/report.log" 2>/dev/null || echo "  No entries yet. Use: novel report <input>"
        else
            local input="$*"
            local ts=$(date '+%Y-%m-%d %H:%M')
            echo "$ts|$input" >> "$DATA_DIR/report.log"
            local total=$(wc -l < "$DATA_DIR/report.log")
            echo "  [Novel] report: $input"
            echo "  Saved. Total report entries: $total"
            _log "report" "$input"
        fi
        ;;
    stats) _stats ;;
    export) shift; _export "$@" ;;
    search) shift; _search "$@" ;;
    recent) _recent ;;
    status) _status ;;
    help|--help|-h) _help ;;
    version|--version|-v) _version ;;
    *)
        echo "Unknown: $1 — run 'novel help'"
        exit 1
        ;;
esac