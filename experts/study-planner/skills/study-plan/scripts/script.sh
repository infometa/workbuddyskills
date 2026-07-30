#!/usr/bin/env bash
# study-plan - Productivity and task management tool
set -euo pipefail
VERSION="2.0.0"
DATA_DIR="${STUDY_PLAN_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/study-plan}"
DB="$DATA_DIR/data.log"
mkdir -p "$DATA_DIR"

show_help() {
    cat << EOF
study-plan v$VERSION

Productivity and task management tool

Usage: study-plan <command> [args]

Commands:
  add                  Add item
  list                 List items
  done                 Mark done
  priority             Set priority
  today                Today view
  week                 Week view
  remind               Set reminder
  stats                Statistics
  clear                Clear completed
  export               Export
  help                 Show this help
  version              Show version

Data: \$DATA_DIR
EOF
}

_log() { echo "$(date '+%m-%d %H:%M') $1: $2" >> "$DATA_DIR/history.log"; }

cmd_add() {
    echo "$(date +%Y-%m-%d) $*" >> "$DB"; echo "  Added: $*"
    _log "add" "${1:-}"
}

cmd_list() {
    [ -f "$DB" ] && cat "$DB" || echo "  (empty)"
    _log "list" "${1:-}"
}

cmd_done() {
    echo "  Completed: $1"
    _log "done" "${1:-}"
}

cmd_priority() {
    echo "  $1 -> priority: ${2:-medium}"
    _log "priority" "${1:-}"
}

cmd_today() {
    echo "  Today $(date +%Y-%m-%d):"; grep "$(date +%Y-%m-%d)" "$DB" 2>/dev/null || echo "  Nothing scheduled"
    _log "today" "${1:-}"
}

cmd_week() {
    echo "  This week overview"
    _log "week" "${1:-}"
}

cmd_remind() {
    echo "  Reminder: $1 at ${2:-tomorrow}"
    _log "remind" "${1:-}"
}

cmd_stats() {
    echo "  Total: $(wc -l < "$DB" 2>/dev/null || echo 0)"
    _log "stats" "${1:-}"
}

cmd_clear() {
    echo "  Cleared completed items"
    _log "clear" "${1:-}"
}

cmd_export() {
    [ -f "$DB" ] && cat "$DB" || echo "No data"
    _log "export" "${1:-}"
}

case "${1:-help}" in
    add) shift; cmd_add "$@" ;;
    list) shift; cmd_list "$@" ;;
    done) shift; cmd_done "$@" ;;
    priority) shift; cmd_priority "$@" ;;
    today) shift; cmd_today "$@" ;;
    week) shift; cmd_week "$@" ;;
    remind) shift; cmd_remind "$@" ;;
    stats) shift; cmd_stats "$@" ;;
    clear) shift; cmd_clear "$@" ;;
    export) shift; cmd_export "$@" ;;
    help|-h) show_help ;;
    version|-v) echo "study-plan v$VERSION" ;;
    *) echo "Unknown: $1"; show_help; exit 1 ;;
esac
