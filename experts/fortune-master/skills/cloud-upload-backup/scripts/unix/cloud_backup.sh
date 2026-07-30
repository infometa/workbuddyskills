#!/usr/bin/env bash
# cloud_backup.sh — 云文件上传备份 skill 统一入口
#
# 命令:
#   upload       上传单个文件
#   batch-upload 批量上传多个文件
#   info         查询云端文件信息
#   list         列出云端目录文件

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/common.sh"

# --------------------------------------------------------
# 帮助信息
# --------------------------------------------------------

print_help() {
  cat <<'EOF'
cloud_backup.sh — 云文件上传备份统一入口

命令：
  upload --local-path <path> [--remote-path <path>] [--conflict-strategy ask|rename|overwrite]
      上传单个本地文件到云端
      --local-path        必填，本地文件绝对路径
      --remote-path       可选，云端目标路径（省略则上传到根目录并保留原文件名）
      --conflict-strategy 可选，同名冲突策略，默认 ask
          ask       — 同名文件存在时返回 HTTP 409，由 QClaw 询问用户
          rename    — 自动重命名（如 file(1).pdf）
          overwrite — 覆盖已有文件

  batch-upload --files <json-array>
      批量上传多个本地文件到云端
      --files  必填，JSON 数组字符串，每项包含 localPath, 可选 remotePath 和 conflictStrategy
      示例: '[{"localPath":"/path/to/a.pdf","conflictStrategy":"ask"},{"localPath":"/path/to/b.jpg"}]'

  info --remote-path <path>
      查询云端文件信息（文件链接、预览、元数据）
      --remote-path  必填，云端文件路径

  list [--dir-path <path>] [--limit <n>]
      列出云端目录中的文件
      --dir-path  可选，目录路径，默认 /
      --limit     可选，最大返回数量，默认 50

  help
      显示此帮助信息
EOF
}

# --------------------------------------------------------
# upload 命令
# --------------------------------------------------------

do_upload() {
  local local_path=""
  local remote_path=""
  local conflict_strategy="ask"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --local-path)        local_path="$2";        shift 2 ;;
      --remote-path)       remote_path="$2";       shift 2 ;;
      --conflict-strategy) conflict_strategy="$2";  shift 2 ;;
      *)                   shift ;;
    esac
  done

  require_param "local-path" "$local_path"

  # 构造请求体
  local body
  if [[ -n "$remote_path" ]]; then
    body=$(json_build "localPath" "$local_path" "remotePath" "$remote_path" "conflictStrategy" "$conflict_strategy")
  else
    body=$(json_build "localPath" "$local_path" "conflictStrategy" "$conflict_strategy")
  fi

  echo "[QClaw] Uploading: $local_path" >&2

  local url="${UPLOAD_API_BASE}/upload"
  local tmp_file
  tmp_file=$(mktemp)
  trap "rm -f '$tmp_file'" RETURN

  local http_status
  http_status=$(curl -s -o "$tmp_file" -w "%{http_code}" \
    -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$body")

  local response
  response=$(cat "$tmp_file")

  # 200 = 成功, 409 = 同名文件冲突（响应体包含冲突详情，需透传给 QClaw）
  if [[ "$http_status" == "200" || "$http_status" == "409" ]]; then
    output_json "$response"
  else
    output_error "HTTP 请求失败，状态码: ${http_status}"
    exit 1
  fi
}

# --------------------------------------------------------
# batch-upload 命令
# --------------------------------------------------------

do_batch_upload() {
  local files=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --files) files="$2"; shift 2 ;;
      *)       shift ;;
    esac
  done

  require_param "files" "$files"

  # 构造请求体
  local body
  body=$("$NODE_EXEC" -e "
const files = JSON.parse(process.argv[1]);
console.log(JSON.stringify({ files }));
" "$files")

  echo "[QClaw] Batch uploading ${files}" >&2

  local response
  response=$(do_upload_post "/batch-upload" "$body")

  # 200 = 成功, 409 = 同名文件冲突（响应体包含冲突详情，需透传给 QClaw）
  if [[ "$HTTP_STATUS" == "200" || "$HTTP_STATUS" == "409" ]]; then
    output_json "$response"
  else
    output_error "HTTP 请求失败，状态码: ${HTTP_STATUS}"
    exit 1
  fi
}

# --------------------------------------------------------
# info 命令
# --------------------------------------------------------

do_info() {
  local remote_path=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --remote-path) remote_path="$2"; shift 2 ;;
      *)             shift ;;
    esac
  done

  require_param "remote-path" "$remote_path"

  local body
  body=$(json_build "remotePath" "$remote_path")

  local response
  response=$(do_upload_post "/info" "$body")

  if [[ "$HTTP_STATUS" != "200" ]]; then
    output_error "HTTP 请求失败，状态码: ${HTTP_STATUS}"
    exit 1
  fi

  output_json "$response"
}

# --------------------------------------------------------
# list 命令
# --------------------------------------------------------

do_list() {
  local dir_path="/"
  local limit="50"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --dir-path) dir_path="$2"; shift 2 ;;
      --limit)    limit="$2";    shift 2 ;;
      *)          shift ;;
    esac
  done

  local body
  body=$(json_build "dirPath" "$dir_path" "limit" "$limit")

  local response
  response=$(do_upload_post "/list" "$body")

  if [[ "$HTTP_STATUS" != "200" ]]; then
    output_error "HTTP 请求失败，状态码: ${HTTP_STATUS}"
    exit 1
  fi

  output_json "$response"
}

# --------------------------------------------------------
# 主入口
# --------------------------------------------------------

main() {
  local cmd="${1:-}"
  if [[ -z "$cmd" ]]; then
    print_help
    exit 0
  fi
  shift || true

  case "$cmd" in
    help|-h|--help)
      print_help
      ;;
    upload)
      do_upload "$@"
      ;;
    batch-upload)
      do_batch_upload "$@"
      ;;
    info)
      do_info "$@"
      ;;
    list)
      do_list "$@"
      ;;
    *)
      output_error "未知命令: ${cmd}，可用命令见 --help"
      exit 1
      ;;
  esac
}

main "$@"
