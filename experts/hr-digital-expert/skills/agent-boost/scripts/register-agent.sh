#!/usr/bin/env bash
# ============================================================
# agent-boost register — Agent 注册脚本（dev/prod 统一使用）
#
# 认证方式：通过 X-Staff-Name header 传递身份（agent-server get_current_user 自动解析）。
# dev/prod 统一使用本脚本，仅 AGENT_SERVER_URL 不同（dev 直连 / prod 生产地址）。
#
# 用法:
#   AGENT_NAME="my-agent" \
#   PROJECT_ID="proj-xxx" \
#   PROJECT_DIR="/path/to/project" \
#   AGENT_SERVER_URL="http://..." \
#   MCP_URL="http://{projectId}-internal-mcp-service.prod.hrainative.woa.com/mcp" \
#   STAFF_NAME="owner" \
#   bash register-agent.sh
#
# 环境变量:
#   MCP_URL           — Bridge 的 MCP 地址（必填，域名格式）
#   STAFF_NAME        — Agent owner 企微名（必填，作为 X-Staff-Name header 认证）
# ============================================================
set -euo pipefail
source "$(dirname "$0")/_env.sh"   # AGENT_SERVER_URL 默认值

AGENT_NAME="${AGENT_NAME:-}"
PROJECT_ID="${PROJECT_ID:-}"
PROJECT_DIR="${PROJECT_DIR:-}"
MCP_URL="${MCP_URL:-}"
STAFF_NAME="${STAFF_NAME:-}"

if test -z "${AGENT_NAME}" || test -z "${PROJECT_ID}" || test -z "${PROJECT_DIR}"; then
    echo "ERROR: AGENT_NAME, PROJECT_ID, PROJECT_DIR are required" >&2
    exit 1
fi

if test -z "${MCP_URL}"; then
    echo "ERROR: MCP_URL is required (Bridge address)" >&2
    exit 1
fi

if test -z "${STAFF_NAME}"; then
    echo "ERROR: STAFF_NAME is required (agent owner)" >&2
    exit 1
fi

# ---- 读取 agent.md body 作为 systemPrompt ----
SYSTEM_PROMPT=""
if test -f "${PROJECT_DIR}/.agent/agent.md"; then
    # 去掉 YAML frontmatter（--- 之间的内容）
    # 用 Python 替代 sed，避免 GNU/BSD sed 语法差异（macOS BSD sed 不支持块内标签循环）
    SYSTEM_PROMPT=$(AGENT_MD="${PROJECT_DIR}/.agent/agent.md" python3 << 'PYEOF'
import os
lines = open(os.environ["AGENT_MD"]).read().split('\n')
if lines and lines[0].strip() == '---':
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            body = '\n'.join(lines[i+1:])
            break
    else:
        body = '\n'.join(lines)
else:
    body = '\n'.join(lines)
print('\n'.join(l for l in body.split('\n') if l.strip()))
PYEOF
    )
fi
if test -z "${SYSTEM_PROMPT}"; then
    SYSTEM_PROMPT="You are ${AGENT_NAME}, an AI assistant."
fi

# ---- 收集 skills ----
# 遍历每个 skill 目录，收集 SKILL.md 全文 + 支撑文件
SKILLS_JSON="[]"
SKILLS_DIR="${PROJECT_DIR}/.agent/skills"
if test -d "${SKILLS_DIR}"; then
    SKILLS_JSON=$(SKILLS_DIR="${SKILLS_DIR}" python3 << 'PYEOF'
import os, json

skills = []
d = os.environ.get("SKILLS_DIR", "")
if os.path.isdir(d):
    for name in sorted(os.listdir(d)):
        skill_dir = os.path.join(d, name)
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        with open(skill_md, "r") as fh:
            content = fh.read()
        # 收集支撑文件（除 SKILL.md 外的所有文本文件）
        files = {}
        for root, _dirs, filenames in os.walk(skill_dir):
            for fname in filenames:
                if fname == "SKILL.md":
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, skill_dir).replace(os.sep, "/")
                try:
                    with open(abs_path, "r") as fh2:
                        files[rel_path] = fh2.read()
                except UnicodeDecodeError:
                    pass  # 跳过非文本文件
        skills.append({"name": name, "content": content, "files": files})
print(json.dumps(skills, ensure_ascii=False))
PYEOF
    )
fi

# ---- 构建注册请求体 ----
# 用环境变量传递参数，避免 heredoc 变量注入（systemPrompt 含 """ 或 \ 会破坏 Python）
REQUEST_BODY=$( \
    AGENT_NAME="${AGENT_NAME}" \
    PROJECT_ID="${PROJECT_ID}" \
    PROJECT_DIR="${PROJECT_DIR}" \
    SYSTEM_PROMPT="${SYSTEM_PROMPT}" \
    SKILLS_JSON="${SKILLS_JSON}" \
    MCP_URL="${MCP_URL}" \
    python3 << 'PYEOF'
import os, json

system_prompt = os.environ.get("SYSTEM_PROMPT", "")
if not system_prompt:
    system_prompt = f"You are {os.environ.get('AGENT_NAME', '')}, an AI assistant."

skills_json = os.environ.get("SKILLS_JSON", "[]")
try:
    skills = json.loads(skills_json)
except json.JSONDecodeError:
    skills = []

project_id = os.environ.get("PROJECT_ID", "")
mcp_servers = [{
    "name": project_id + "-bridge",
    "type": "http",
    "url": os.environ.get("MCP_URL", "")
}]

# 能力 MCP 依赖：从 boost-state.json 读取 capabilities，追加已启用能力声明的 MCP 服务
# DW_MCP_URL 环境变量优先（prod-deploy.sh 传入 prod 地址），否则用 boost-state.json 的 mcpUrl（dev 地址）
_state_file = os.path.join(os.environ.get("PROJECT_DIR", ""), ".agent", "boost-state.json")
if os.path.isfile(_state_file):
    try:
        with open(_state_file) as _f:
            _state = json.load(_f)
        _dw_mcp_url_override = os.environ.get("DW_MCP_URL", "")
        for _cap in _state.get("capabilities", {}).values():
            if not _cap.get("enabled"):
                continue
            _dep = _cap.get("mcpDependency")
            _url = _dw_mcp_url_override or _cap.get("mcpUrl", "")
            if _dep and _url and not any(s["name"] == _dep for s in mcp_servers):
                mcp_servers.append({"name": _dep, "type": "http", "url": _url})
    except (json.JSONDecodeError, IOError):
        pass

body = {
    "name": os.environ.get("AGENT_NAME", ""),
    "projectId": project_id,
    "systemPrompt": system_prompt,
    "skills": skills,
    "mcpServers": mcp_servers,
}

print(json.dumps(body, indent=2, ensure_ascii=False))
PYEOF
)

# ---- Step 1: POST 注册（通过 X-Staff-Name header 认证） ----
# 注册接口内部已内置 unload 旧实例 → upsert 配置 → load 新实例 → 清缓存，无需先 DELETE。
REGISTER_RESP=$(curl -s -X POST "${AGENT_SERVER_URL}/api/agent/register" \
    -H "Content-Type: application/json" \
    -H "X-Staff-Name: ${STAFF_NAME}" \
    -d "${REQUEST_BODY}")

echo "REGISTER_RESP: ${REGISTER_RESP}"

# ---- Step 2: 验证 loaded（带重试，最多 5 次） ----
LOADED="false"
for i in 1 2 3 4 5; do
    LOADED=$(curl -s \
        -H "X-Staff-Name: ${STAFF_NAME}" \
        "${AGENT_SERVER_URL}/api/agent/${AGENT_NAME}" | \
        python3 -c "import sys,json; print(str(json.load(sys.stdin).get('loaded',False)).lower())" 2>/dev/null || echo "false")
    if test "${LOADED}" = "true"; then
        echo "AGENT_LOADED=true (retry $i)"
        break
    fi
    echo "LOADED=${LOADED}, retry $i/5..."
    sleep 6
done

if test "${LOADED}" != "true"; then
    echo "AGENT_LOADED=false"
    echo "ERROR: Agent loaded=${LOADED}，请检查 Bridge 是否就绪"
    exit 1
fi

# ---- Step 3: 写 boost-state.json ----
# 从 SKILLS_JSON 提取 skill 元数据（name + hasFiles）；NOW 统一时间戳
SKILLS_META=$(SKILLS_JSON="${SKILLS_JSON}" python3 -c "import os,json; print(json.dumps([{'name':s.get('name',''),'hasFiles':bool(s.get('files'))} for s in json.loads(os.environ.get('SKILLS_JSON','[]'))], ensure_ascii=False))" 2>/dev/null || echo "[]")
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
# 保留已有的 bridgePort（生产部署时从 boost-state.json 读取）
BRIDGE_PORT_VAL="${BRIDGE_PORT:-$(python3 -c "import json; print(json.load(open('${PROJECT_DIR}/.agent/boost-state.json')).get('bridgePort',''))" 2>/dev/null || echo "")}"

# 用 Python 写 boost-state.json（重建模式，保留关键字段）
# 重建模式（保留关键字段）：从旧文件读取 createdAt 等已有字段。
STATE_FILE="${PROJECT_DIR}/.agent/boost-state.json" \
AGENT_NAME="${AGENT_NAME}" \
PROJECT_ID="${PROJECT_ID}" \
PROJECT_DIR="${PROJECT_DIR}" \
STAFF_NAME="${STAFF_NAME}" \
SKILLS_META="${SKILLS_META}" \
BRIDGE_PORT_VAL="${BRIDGE_PORT_VAL}" \
NOW="${NOW}" \
MCP_URL="${MCP_URL}" \
python3 << 'PYEOF'
import os, json

state_file = os.environ["STATE_FILE"]

# 读取旧文件，保留 createdAt 等关键字段
old_state = {}
if os.path.isfile(state_file):
    try:
        with open(state_file, 'r') as f:
            old_state = json.load(f)
    except (json.JSONDecodeError, IOError):
        pass

state = {
    "schemaVersion": 1,
    "agentName": os.environ.get("AGENT_NAME", ""),
    "projectId": os.environ.get("PROJECT_ID", ""),
    "projectDir": os.environ.get("PROJECT_DIR", ""),
    "staffName": os.environ.get("STAFF_NAME", ""),
    "state": "deployed",
    "skills": json.loads(os.environ.get("SKILLS_META", "[]")),
    "bridgePort": os.environ.get("BRIDGE_PORT_VAL", ""),
    "widgetVersion": old_state.get("widgetVersion", ""),
    "createdAt": old_state.get("createdAt", ""),
    "registeredAt": os.environ.get("NOW", ""),
    "lastDeployedAt": os.environ.get("NOW", ""),
    "mcpUrl": os.environ.get("MCP_URL", ""),
}
# 保留阶段三写入的授权配置摘要
if "authz" in old_state:
    state["authz"] = old_state["authz"]
# 保留阶段三写入的能力启用清单（能力模块注册表的状态承载）
if "capabilities" in old_state:
    state["capabilities"] = old_state["capabilities"]
with open(state_file, "w") as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF

echo "DONE: Agent ${AGENT_NAME} registered and loaded"
echo "MCP_URL=${MCP_URL}"
