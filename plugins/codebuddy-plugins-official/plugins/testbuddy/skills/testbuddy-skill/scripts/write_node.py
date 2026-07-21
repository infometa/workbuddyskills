#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# write_node_from_file.py：从文件读取节点并操作
# 用法: python3 write_node_from_file.py <action> <file_path> [--design_uid <design_uid>]
# 支持格式: JSON (.json), YAML (.yaml/.yml), Markdown (.md)
import json
import os
import re
import sys

try:
    import ssl
    import urllib.error as urllib_error
    import urllib.request as urllib_request
except ImportError:
    urllib_request = None
    urllib_error = None
    ssl = None

# 强制使用 Python 3
if sys.version_info[0] < 3:
    print("错误：此脚本需要 Python 3，请使用 python3 运行", file=sys.stderr)
    sys.exit(1)

# 尝试导入 yaml 库
try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# 确保脚本所在目录在 sys.path 中，以便正确导入同目录模块
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

# 导入 get_session 模块，复用 session 加载逻辑
from get_session import _find_workspace_root, load_session  # noqa: E402

# 工作区根目录（自动查找，避免因 cd 到错误目录导致路径错误）
WORKSPACE_ROOT = _find_workspace_root()
TESTBUDDY_DIR = os.path.join(WORKSPACE_ROOT, ".testbuddy", "assets")

DEFAULT_SERVER = "http://testbuddy.woa.com"

# 内网环境跳过 SSL 证书验证
if ssl:
    SSL_CONTEXT = ssl.create_default_context()
    SSL_CONTEXT.check_hostname = False
    SSL_CONTEXT.verify_mode = ssl.CERT_NONE
else:
    SSL_CONTEXT = None


def get_server():
    return os.environ.get("TESTBUDDY_SERVER", DEFAULT_SERVER).rstrip("/")


def _load_session_data():
    """通过 get_session.load_session 加载 session 数据，返回 session dict 或 None（加载失败）"""
    data = load_session()
    if isinstance(data, dict) and data.get("status") == "error":
        return None
    return data


def get_token():
    """通过 get_session 获取 token"""
    data = _load_session_data()
    if data:
        return data.get("token", "").strip()
    return ""


def get_session_id():
    """通过 get_session 获取 session_id"""
    data = _load_session_data()
    if data:
        return data.get("session_id", "").strip()
    return ""


def get_mode():
    """通过 get_session 获取 mode（mindmap / chat）"""
    data = _load_session_data()
    if data:
        return data.get("mode", "").strip()
    return ""


def get_source():
    """从 session 的 env 字段获取节点来源标识
    codebuddy -> CB_PLUGIN_AGENT（枚举值 13，cb插件），其他（other 等）-> OPEN_CLAW（枚举值 15，open claw ai生成）
    """
    data = _load_session_data()
    env = data.get("env", "other").strip() if data else "other"
    if env == "codebuddy":
        return "CB_PLUGIN_AGENT"
    return "OPEN_CLAW"


def get_namespace():
    """通过 get_session 获取 namespace，为空时调用 server 的 session/check 接口获取 username 作为兜底"""
    data = _load_session_data()
    if data:
        namespace = data.get("namespace", "").strip()
        if namespace:
            return namespace
        # namespace 为空，调用 session/check 接口从 server 获取 username
        session_id = data.get("session_id", "").strip()
        if session_id:
            token = get_token()
            resp = _post("/api/tb/v1/cb-plugin/session/check", token, {"session_id": session_id})
            username = resp.get("username", "").strip()
            if username:
                return username
    return ""


def _get_testbuddy_origin():
    """根据 session 中的 env 字段返回 x-testbuddy-origin 值
    codebuddy -> cb-plugin，其他 -> openclaw
    """
    data = _load_session_data()
    if data:
        env = data.get("env", "other").strip()
        if env == "codebuddy":
            return "cb-plugin"
    return "openclaw"


def _post(path, token, body):
    """发送 POST 请求，返回解析后的 JSON 响应。校验状态码必须为200，否则返回错误。"""
    if not urllib_request:
        return {"error": "urllib 不可用"}
    url = get_server() + path
    data = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "x-testbuddy-origin": _get_testbuddy_origin(),
    }
    if token:
        headers["Authorization"] = "token {}".format(token)
    virtual_env = os.environ.get("TESTBUDDY_VIRTUAL_ENV")
    if virtual_env:
        headers["X-Virtual-Env"] = virtual_env
    req = urllib_request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=10, context=SSL_CONTEXT) as resp:
            status_code = resp.getcode()
            raw = resp.read().decode("utf-8")
            if status_code != 200:
                return {"error": "请求失败(HTTP {}): {}".format(status_code, raw[:500])}
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return {"error": "服务端返回了非预期格式: {}".format(raw[:500])}
            return parsed
    except urllib_error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else ""
        return {"error": "请求失败(HTTP {}): {}".format(e.code, raw[:500])}
    except Exception as e:
        return {"error": str(e)}


def check_session_alive(session_id):
    """检查 session_id 是否存活，返回 (alive: bool, err_msg: str)"""
    token = get_token()
    resp = _post("/api/tb/v1/cb-plugin/session/check", token, {"session_id": session_id})
    if "error" in resp:
        return False, "session 检查失败: {}".format(resp["error"])
    if not resp.get("alive"):
        return False, "TestBuddy 面板连接已断开，请刷新页面后重试"
    return True, ""


def call_save_node(design_uid):
    """调用 save_node.py 脚本，将 update.json 中的节点批量保存到服务端"""
    namespace = get_namespace()

    save_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save_node.py")
    if not os.path.exists(save_script):
        return {"status": "error", "msg": "save_node.py 不存在: {}".format(save_script)}

    import subprocess

    cmd = [
        sys.executable,
        save_script,
        "--clear_after_save",
    ]
    if namespace:
        cmd.extend(["--namespace", namespace])
    if design_uid:
        cmd.extend(["--design_uid", design_uid])
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        output = proc.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except Exception:
                pass
        if proc.returncode != 0:
            err = proc.stderr.strip() or output
            return {"status": "error", "msg": "save_node 执行失败: {}".format(err)}
        return {"status": "success"}
    except subprocess.TimeoutExpired:
        return {"status": "error", "msg": "save_node 执行超时"}
    except Exception as e:
        return {"status": "error", "msg": "save_node 调用异常: {}".format(str(e))}


def call_show_node(design_uid, node_uids):
    """调用 show_node 接口，向前端下发展示节点指令（仅 mindmap 模式使用）。
    内部会校验 mode 和 session 存活状态，非 mindmap 模式静默跳过。
    """
    # 防御性检查：仅 mindmap 模式才需要下发展示指令
    mode = get_mode()
    if mode != "mindmap":
        return {"status": "success"}

    session_id = get_session_id()
    if not session_id:
        return {"status": "error", "msg": "未找到 session_id，请确认 .testbuddy/env/session.json 文件存在"}

    alive, err_msg = check_session_alive(session_id)
    if not alive:
        return {"status": "error", "msg": err_msg}

    token = get_token()
    body = {
        "session_id": session_id,
        "design_uid": design_uid,
        "node_uids": node_uids,
    }
    resp = _post("/api/tb/v1/cb-plugin/node/show", token, body)
    if "error" in resp or not resp.get("success"):
        return {
            "status": "error",
            "msg": "节点展示失败，请刷新页面后重试。详情：{}".format(resp.get("error", str(resp))),
        }
    return {"status": "success"}


def generate_uid(kind):
    """生成节点的唯一ID"""
    import random
    import string

    chars = string.ascii_letters + string.digits
    random_str = "".join(random.choice(chars) for _ in range(10))
    return "{}-{}".format(kind.lower().replace("_", "_"), random_str)


def parse_yaml_content(content):
    """解析 YAML 内容"""
    if not HAS_YAML:
        return None, "缺少 yaml 库，请安装: pip install pyyaml"

    try:
        data = yaml.safe_load(content)
        return data, None
    except Exception as e:
        return None, "YAML 解析失败: {}".format(str(e))


def parse_structured_markdown(content):
    """解析结构化的 Markdown 格式（## 模块，### 场景，#### 测试点，##### 用例）"""
    lines = content.split("\n")
    nodes = []
    current_module = None
    current_scene = None
    current_point = None
    current_case = None

    # 用于临时存储当前节点的信息
    temp_data = {}
    in_steps = False
    steps = []

    def save_current_case():
        """保存当前用例节点"""
        if current_case and temp_data:
            current_case["instance"] = {
                "preconditions": temp_data.get("前置条件", ""),
                "priority": temp_data.get("优先级", "P1"),
                "steps": steps,
            }
            nodes.append(current_case)

    def save_current_point():
        """保存当前测试点节点"""
        if current_point:
            nodes.append(current_point)

    def save_current_scene():
        """保存当前场景节点"""
        if current_scene:
            nodes.append(current_scene)

    def save_current_module():
        """保存当前模块节点"""
        if current_module:
            nodes.append(current_module)

    for line in lines:
        line = line.rstrip()

        # 解析标题行
        if line.startswith("## "):
            # 保存之前的所有层级
            save_current_case()
            save_current_point()
            save_current_scene()
            save_current_module()

            # 新建模块
            title = line[3:].strip()
            current_module = {"name": title, "kind": "FEATURE", "description": "", "instance": None}
            current_scene = None
            current_point = None
            current_case = None
            temp_data = {}
            steps = []
            in_steps = False

        elif line.startswith("### "):
            # 保存之前的用例和测试点
            save_current_case()
            save_current_point()
            save_current_scene()

            # 新建场景
            title = line[4:].strip()
            current_scene = {"name": title, "kind": "SCENE", "description": "", "instance": None}
            current_point = None
            current_case = None
            temp_data = {}
            steps = []
            in_steps = False

        elif line.startswith("#### "):
            # 保存之前的用例和测试点
            save_current_case()
            save_current_point()

            # 新建测试点
            title = line[5:].strip()
            current_point = {"name": title, "kind": "TEST_POINT", "description": "", "instance": None}
            current_case = None
            temp_data = {}
            steps = []
            in_steps = False

        elif line.startswith("##### "):
            # 保存之前的用例
            save_current_case()

            # 新建用例
            title = line[6:].strip()
            current_case = {"name": title, "kind": "CASE", "description": "", "instance": None}
            temp_data = {}
            steps = []
            in_steps = False

        # 解析字段
        elif line.startswith("**PARENT_UID：**") or line.startswith("**PARENT_UID:**"):
            match = re.search(r"\*\*PARENT_UID[：:]\*\*\s*(.+)", line)
            if match:
                target = current_case or current_point or current_scene or current_module
                if target:
                    target["parent_uid"] = match.group(1).strip()

        elif line.startswith("**UID：**") or line.startswith("**UID:**"):
            match = re.search(r"\*\*UID[：:]\*\*\s*(.+)", line)
            if match:
                target = current_case or current_point or current_scene or current_module
                if target:
                    target["uid"] = match.group(1).strip()

        elif line.startswith("**功能描述：**") or line.startswith("**功能描述:**"):
            match = re.search(r"\*\*功能描述[：:]\*\*\s*(.+)", line)
            if match and current_module:
                current_module["description"] = match.group(1).strip()

        elif line.startswith("**场景描述：**") or line.startswith("**场景描述:**"):
            match = re.search(r"\*\*场景描述[：:]\*\*\s*(.+)", line)
            if match and current_scene:
                current_scene["description"] = match.group(1).strip()

        elif line.startswith("**描述：**") or line.startswith("**描述:**"):
            match = re.search(r"\*\*描述[：:]\*\*\s*(.+)", line)
            if match and current_point:
                current_point["description"] = match.group(1).strip()

        elif line.startswith("**用例描述：**") or line.startswith("**用例描述:**"):
            match = re.search(r"\*\*用例描述[：:]\*\*\s*(.+)", line)
            if match and current_case:
                current_case["description"] = match.group(1).strip()

        elif line.startswith("**前置条件：**") or line.startswith("**前置条件:**"):
            match = re.search(r"\*\*前置条件[：:]\*\*\s*(.+)", line)
            if match:
                temp_data["前置条件"] = match.group(1).strip()

        elif line.startswith("**优先级：**") or line.startswith("**优先级:**"):
            match = re.search(r"\*\*优先级[：:]\*\*\s*(.+)", line)
            if match:
                temp_data["优先级"] = match.group(1).strip()

        elif line.startswith("**执行步骤：**") or line.startswith("**执行步骤:**"):
            in_steps = True
            steps = []

        elif in_steps and line.startswith("- 步骤"):
            # 解析步骤：- 步骤1：操作描述；预期结果：结果描述
            match = re.search(r"-\s*步骤\d+[：:]\s*(.+?)[；;]\s*预期结果[：:]\s*(.+)", line)
            if match:
                steps.append({"action": match.group(1).strip(), "expected": match.group(2).strip()})

        elif line.strip() == "" or not line.startswith("-"):
            in_steps = False

    # 保存最后剩余的所有节点
    save_current_case()
    save_current_point()
    save_current_scene()
    save_current_module()

    # 为没有 uid 的节点生成 uid
    for node in nodes:
        if "uid" not in node or not node["uid"]:
            node["uid"] = generate_uid(node["kind"])
        if "parent_uid" not in node:
            node["parent_uid"] = None

    return nodes


def parse_markdown_content(content):
    """从 Markdown 中提取 YAML/JSON 代码块或解析结构化格式"""
    # 匹配 ```yaml 或 ```json 代码块
    yaml_pattern = r"```(?:yaml|yml)\s*\n(.*?)\n```"
    json_pattern = r"```json\s*\n(.*?)\n```"

    yaml_matches = re.findall(yaml_pattern, content, re.DOTALL)
    json_matches = re.findall(json_pattern, content, re.DOTALL)

    # 优先尝试 YAML 代码块
    if yaml_matches:
        if not HAS_YAML:
            return None, "缺少 yaml 库，请安装: pip install pyyaml"
        try:
            data = yaml.safe_load(yaml_matches[0])
            return data, None
        except Exception as e:
            return None, "Markdown 中的 YAML 解析失败: {}".format(str(e))

    # 尝试 JSON 代码块
    if json_matches:
        try:
            data = json.loads(json_matches[0])
            return data, None
        except Exception as e:
            return None, "Markdown 中的 JSON 解析失败: {}".format(str(e))

    # 尝试解析结构化 Markdown 格式
    try:
        nodes = parse_structured_markdown(content)
        if nodes and len(nodes) > 0:
            return nodes, None
    except Exception:
        pass

    # 如果都不行，尝试直接解析整个内容为 YAML
    if HAS_YAML:
        try:
            data = yaml.safe_load(content)
            if data:
                return data, None
        except Exception:
            pass

    return None, "Markdown 文件中未找到有效的 YAML/JSON 代码块或结构化格式"


def flatten_tree_to_list(nodes, parent_uid=None):
    """将树形结构的节点展平为列表，并生成 uid"""
    result = []

    if not isinstance(nodes, list):
        nodes = [nodes]

    for node in nodes:
        if not isinstance(node, dict):
            continue

        # 生成 uid（如果没有）
        if "uid" not in node:
            node["uid"] = generate_uid(node.get("kind", "feature"))

        # 设置 parent_uid
        if parent_uid:
            node["parent_uid"] = parent_uid

        # 确保 instance 字段存在
        if "instance" not in node:
            node["instance"] = None

        # 提取 children
        children = node.pop("children", [])

        # 添加当前节点
        result.append(node)

        # 递归处理子节点
        if children:
            child_results = flatten_tree_to_list(children, node["uid"])
            result.extend(child_results)

    return result


def load_file_data(file_path):
    """根据文件扩展名加载并解析文件"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # JSON 格式
    if ext == ".json":
        try:
            data = json.loads(content)
            # 如果是树形结构（包含children），展平为列表
            if isinstance(data, (list, dict)):
                data = flatten_tree_to_list(data)
            return data, None
        except Exception as e:
            return None, "JSON 解析失败: {}".format(str(e))

    # YAML 格式
    elif ext in [".yaml", ".yml"]:
        data, error = parse_yaml_content(content)
        if error:
            return None, error
        # 如果是树形结构，展平为列表
        if isinstance(data, (list, dict)):
            data = flatten_tree_to_list(data)
        return data, None

    # Markdown 格式
    elif ext == ".md":
        data, error = parse_markdown_content(content)
        if error:
            return None, error
        # 如果已经是列表，直接返回（结构化 Markdown 已经是扁平列表）
        if isinstance(data, list):
            return data, None
        # 如果是树形结构，展平为列表
        if isinstance(data, dict):
            data = flatten_tree_to_list(data)
        return data, None

    else:
        return None, "不支持的文件格式: {}，支持的格式: .json, .yaml, .yml, .md".format(ext)


def load_update_file(design_uid):
    """加载现有的 update 文件，如果不存在则返回空结构"""
    filename = "{}-update.json".format(design_uid) if design_uid else "pending-update.json"
    target_file = os.path.join(TESTBUDDY_DIR, filename)
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"added": [], "updated": [], "deleted": []}


def save_update_file(design_uid, data):
    """保存 update 文件"""
    filename = "{}-update.json".format(design_uid) if design_uid else "pending-update.json"
    target_file = os.path.join(TESTBUDDY_DIR, filename)
    target_dir = os.path.dirname(target_file)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_node_structure(node, index=None):
    """校验单个节点的数据结构"""
    prefix = "节点[{}]".format(index) if index is not None else "节点"

    if not isinstance(node, dict):
        return False, "{}: 必须是对象(dict)，当前类型：{}".format(prefix, type(node).__name__)

    # 检查必填字段
    required_fields = ["uid", "name", "kind", "parent_uid"]
    for field in required_fields:
        if field not in node:
            return False, "{}: 缺少必填字段 '{}'".format(prefix, field)

    # uid 校验
    uid = node["uid"]
    if not isinstance(uid, str) or not uid.strip():
        return False, "{}: uid 必须是非空字符串".format(prefix)

    # kind 校验
    valid_kinds = ["STORY", "BUG", "FEATURE", "SCENE", "TEST_POINT", "CASE"]
    if node["kind"] not in valid_kinds:
        return False, "{}: kind 必须是 {} 之一，当前值：{}".format(prefix, valid_kinds, node["kind"])

    kind = node["kind"]

    # instance 字段校验（仅对 CASE、STORY、BUG 类型强制要求）
    if kind in ["CASE", "STORY", "BUG"]:
        if "instance" not in node:
            return False, "{}: {} 类型缺少必填字段 'instance'".format(prefix, kind)
        instance = node["instance"]
    else:
        # FEATURE/SCENE/TEST_POINT 类型 instance 可以为 null 或不存在
        instance = node.get("instance")

    # CASE 类型 instance 校验
    if kind == "CASE":
        if instance is None or not isinstance(instance, dict):
            return False, "{}: CASE 类型的 instance 必须是对象，不能为 null".format(prefix)

        # CASE 必填字段
        case_required = ["preconditions", "priority", "steps"]
        for field in case_required:
            if field not in instance:
                return False, "{}: CASE 类型的 instance 缺少必填字段 '{}'".format(prefix, field)

        # priority 校验
        valid_priorities = ["P0", "P1", "P2", "P3"]
        if instance["priority"] not in valid_priorities:
            return False, "{}: priority 必须是 {} 之一，当前值：{}".format(
                prefix, valid_priorities, instance["priority"]
            )

        # steps 校验
        steps = instance["steps"]
        if not isinstance(steps, list) or len(steps) == 0:
            return False, "{}: steps 必须是非空数组".format(prefix)

        for step_idx, step in enumerate(steps):
            if not isinstance(step, dict):
                return False, "{}: steps[{}] 必须是对象".format(prefix, step_idx)
            if "action" not in step:
                return False, "{}: steps[{}] 缺少必填字段 'action'".format(prefix, step_idx)
            if "expected" not in step:
                return False, "{}: steps[{}] 缺少必填字段 'expected'".format(prefix, step_idx)

    # STORY/BUG 类型 instance 校验
    elif kind in ["STORY", "BUG"]:
        if instance is None or not isinstance(instance, dict):
            return False, "{}: {} 类型的 instance 必须是对象，不能为 null".format(prefix, kind)

        # STORY/BUG 必填字段
        issue_required = ["workspace", "issue_id"]
        for field in issue_required:
            if field not in instance:
                return False, "{}: {} 类型的 instance 缺少必填字段 '{}'".format(prefix, kind, field)

    # 其他类型（FEATURE/SCENE/TEST_POINT）instance 可以为 null
    elif kind in ["FEATURE", "SCENE", "TEST_POINT"]:
        if instance is not None and not isinstance(instance, dict):
            return False, "{}: {} 类型的 instance 必须是 null 或对象".format(prefix, kind)

    return True, ""


def _validate_parent_uids(design_uid, data, story_uid):
    """验证 data 中节点的 parent_uid 是否有效，无效的指向 story_uid。
    收集 data 子树中所有外部祖先 uid（即 parent_uid 不在 data 自身 uid 集合中的），
    调用 search_node 验证这些外部祖先是否在脑图中真实存在，不存在的则修正为 story_uid。
    当 design_uid 为空时（创建 design 场景），跳过外部祖先验证，但仍修复无效的 parent_uid。
    """
    if not story_uid:
        return

    # 收集 data 自身的所有 uid
    data_uids = {n.get("uid") for n in data if n.get("uid")}

    # 收集所有外部祖先 uid（parent_uid 不为空且不在 data 自身中的）
    external_parent_uids = set()
    for node in data:
        p_uid = node.get("parent_uid")
        if p_uid and p_uid not in data_uids:
            external_parent_uids.add(p_uid)

    if not external_parent_uids:
        # 没有外部祖先需要验证，只需修复 parent_uid 为空的节点
        for node in data:
            if node.get("uid") != story_uid and not node.get("parent_uid"):
                node["parent_uid"] = story_uid
        return

    # 有 design_uid 时才调用 search_node 验证外部祖先 uid 是否有效
    valid_external_uids = set()
    if design_uid:
        try:
            from search_node import search_local

            matched, found = search_local(design_uid, list(external_parent_uids))
            if found and matched:
                valid_external_uids = {n.get("uid") for n in matched if n.get("uid")}
        except Exception:
            pass

        # 如果本地查不到，尝试远程查询
        if not valid_external_uids:
            try:
                search_script = os.path.join(_SCRIPT_DIR, "search_node.py")
                if os.path.exists(search_script):
                    import subprocess as sp

                    session_data = _load_session_data() or {}
                    namespace = session_data.get("namespace", "").strip()
                    cmd = (
                        [
                            sys.executable,
                            search_script,
                            "--design_uid",
                            design_uid,
                            "--uids",
                        ]
                        + list(external_parent_uids)
                        + ["--no-descendant"]
                    )
                    if namespace:
                        cmd.extend(["--namespace", namespace])
                    proc = sp.run(cmd, capture_output=True, text=True, timeout=30)
                    if proc.returncode == 0 and proc.stdout.strip():
                        search_result = json.loads(proc.stdout.strip())
                        if search_result.get("status") == "success":
                            remote_data = search_result.get("data", [])
                            valid_external_uids = {n.get("uid") for n in remote_data if n.get("uid")}
            except Exception:
                pass

    # 合并有效 uid 集合：data 自身 + 验证通过的外部祖先
    all_valid_uids = data_uids | valid_external_uids

    # 修正无效的 parent_uid
    for node in data:
        if node.get("uid") == story_uid:
            continue
        p_uid = node.get("parent_uid")
        if not p_uid or p_uid not in all_valid_uids:
            node["parent_uid"] = story_uid


def _check_and_create_story_node(design_uid, data):
    """检查 STORY/BUG 节点是否存在，不存在则自动创建并插入到 data 列表最前面。
    通过 search_node 模块的 flatten_nodes 从本地文件查询，或通过 subprocess 调用 search_node.py 远程查询。
    从 session.json 的 story_info 字段读取需求信息来构造节点。

    参数：
        design_uid: 设计文件 UID（可能为空）
        data: 待写入的节点列表（会被原地修改）

    返回：
        (story_node_uid, story_node_created): story 节点的 uid 和是否新创建
    """
    from search_node import flatten_nodes

    # 从 session 读取 story_info
    session_data = _load_session_data()
    if not session_data:
        return None, False

    story_info = session_data.get("story_info")
    if not story_info or not isinstance(story_info, dict):
        return None, False

    issue_type = story_info.get("issue_type", "STORY").upper()
    kind_upper = issue_type if issue_type in ("STORY", "BUG") else "STORY"
    current_issue_id = story_info.get("issue_id", "").strip()

    def _get_node_issue_id(node):
        """从节点 instance 中获取 issue_id，兼容大驼峰(IssueUid)和小写(issue_id)两种格式"""
        inst = node.get("instance") or {}
        return str(inst.get("IssueUid", "") or inst.get("issue_id", "")).strip()

    # 策略1：有 design_uid 时，从本地 assets 文件查询是否已存在 STORY/BUG 节点
    if design_uid:
        local_file = os.path.join(TESTBUDDY_DIR, "{}.json".format(design_uid))
        if os.path.exists(local_file):
            try:
                with open(local_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                all_nodes = flatten_nodes(raw)
                matched = [
                    n
                    for n in all_nodes
                    if n.get("kind", "").upper() == kind_upper
                    and (not current_issue_id or _get_node_issue_id(n) == current_issue_id)
                ]
                if matched:
                    # 已存在且 issue_id 一致，返回第一个匹配节点的 uid
                    return matched[0].get("uid"), False
            except Exception:
                pass

        # 本地文件不存在或没找到，尝试通过 subprocess 调用 search_node.py 远程查询
        search_script = os.path.join(_SCRIPT_DIR, "search_node.py")
        if os.path.exists(search_script):
            try:
                import subprocess as sp

                namespace = session_data.get("namespace", "").strip()
                cmd = [
                    sys.executable,
                    search_script,
                    "--design_uid",
                    design_uid,
                    "--uids",
                    design_uid,
                    "--kind",
                    kind_upper,
                ]
                if namespace:
                    cmd.extend(["--namespace", namespace])
                proc = sp.run(cmd, capture_output=True, text=True, timeout=30)
                if proc.returncode == 0 and proc.stdout.strip():
                    search_result = json.loads(proc.stdout.strip())
                    if search_result.get("status") == "success":
                        remote_data = search_result.get("data", [])
                        matched = [
                            n
                            for n in remote_data
                            if n.get("kind", "").upper() == kind_upper
                            and (not current_issue_id or _get_node_issue_id(n) == current_issue_id)
                        ]
                        if matched:
                            return matched[0].get("uid"), False
            except Exception:
                pass

    # 策略3：检查当前 data 列表中是否已存在相同 issue_id 的 STORY/BUG 节点（AI 可能已生成）
    for node in data:
        if node.get("kind", "").upper() == kind_upper:
            node_issue_id = _get_node_issue_id(node)
            if not current_issue_id or node_issue_id == current_issue_id:
                # data 中已存在匹配的 STORY/BUG 节点，复用它
                existing_uid = node.get("uid")
                if existing_uid:
                    # 验证 data 子树中外部祖先 uid 的有效性，无效的指向复用的 STORY 节点
                    _validate_parent_uids(design_uid, data, existing_uid)
                return existing_uid, False

    # 节点不存在，需要创建
    workspace = story_info.get("workspace", "")
    issue_id = story_info.get("issue_id", "")
    issue_name = story_info.get("issue_name", "")
    issue_url = story_info.get("issue_url", "")

    if not issue_id and not issue_name:
        # 没有足够的信息来创建 STORY 节点
        return None, False

    story_uid = generate_uid(kind_upper)
    source = get_source()

    story_node = {
        "uid": story_uid,
        "name": issue_name or "需求-{}".format(issue_id),
        "description": "",
        "kind": kind_upper,
        "parent_uid": "",
        "instance": {
            "workspace": workspace,
            "issue_id": issue_id,
            "issue_name": issue_name,
            "issue_source": "TAPD",
            "issue_url": issue_url,
        },
        "source": source,
    }

    # 将 STORY 节点插入到 data 列表最前面
    data.insert(0, story_node)

    # 验证 data 子树中外部祖先 uid 的有效性，无效的指向新建的 STORY 节点
    _validate_parent_uids(design_uid, data, story_uid)

    return story_uid, True


def handle_add(data, design_uid):
    """处理添加节点操作"""
    if not isinstance(data, list):
        return {"status": "error", "msg": "输入必须是节点数组，当前类型：{}".format(type(data).__name__)}

    # ── 自动检查并创建 STORY/BUG 节点 ──
    # 在校验之前执行，因为可能需要插入新的 STORY 节点到 data 中
    try:
        story_uid, story_created = _check_and_create_story_node(design_uid, data)
    except Exception:
        story_uid, story_created = None, False

    # ── story 节点处理完成后，清理 session.json 中的 story_info，避免后续请求重复创建 ──
    if story_uid:
        try:
            from get_session import save_session

            session_data = _load_session_data() or {}
            if "story_info" in session_data:
                del session_data["story_info"]
                save_session(session_data)
        except Exception:
            pass

    # ── 没有 story 节点时，将 parent_uid 为空的节点自动挂载到 design_uid ──
    if not story_uid and design_uid:
        for node in data:
            if not node.get("parent_uid"):
                node["parent_uid"] = design_uid

    # 校验每个节点
    for idx, node in enumerate(data):
        is_valid, msg = validate_node_structure(node, idx)
        if not is_valid:
            return {"status": "error", "msg": "节点校验失败: {}".format(msg)}

    # 补充 source 字段（未指定时从环境变量读取，默认为 CB_PLUGIN）
    source = get_source()
    for node in data:
        if not node.get("source"):
            node["source"] = source

    # 覆盖写入（不累积旧数据，避免失败重试时节点重复）
    update_data = {"added": data, "updated": [], "deleted": []}

    # 保存文件
    save_update_file(design_uid, update_data)

    # 根据模式决定处理方式
    mode = get_mode()
    node_uids = [node["uid"] for node in data if node.get("uid")]

    if mode == "mindmap":
        # mindmap 模式：调用 show_node 接口直接渲染到脑图上
        if design_uid:
            show_result = call_show_node(design_uid, node_uids)
            if show_result and show_result.get("status") == "error":
                return show_result

        result = {
            "status": "success",
            "action": "add",
            "design_uid": design_uid,
            "stats": {
                "added": len(data),
                "total_added": len(update_data["added"]),
                "total_updated": len(update_data["updated"]),
                "total_deleted": len(update_data["deleted"]),
            },
            "msg": "节点已渲染至脑图上",
        }

        # 附加 story 节点信息到返回值
        if story_uid:
            result["story_node_uid"] = story_uid
            result["story_node_created"] = story_created

        return result

    # chat 模式：调用 save_node.py 保存到服务端
    save_result = call_save_node(design_uid)
    if save_result.get("status") == "error":
        return save_result

    # 服务端可能返回新创建的 design_uid（当传入为空时由服务端自动创建）
    actual_design_uid = save_result.get("design_uid", design_uid)
    # 从 batch-save 接口返回值中获取 namespace（服务端通过 token 解析得到）
    namespace = save_result.get("namespace", "") or ""

    filename = "{}-update.json".format(actual_design_uid) if actual_design_uid else "pending-update.json"
    target_file = os.path.join(TESTBUDDY_DIR, filename)

    result = {
        "status": "success",
        "action": "add",
        "design_uid": actual_design_uid,
        "target_file": target_file,
        "stats": {
            "added": len(data),
            "total_added": len(update_data["added"]),
            "total_updated": len(update_data["updated"]),
            "total_deleted": len(update_data["deleted"]),
        },
    }

    # 附加 story 节点信息到返回值
    if story_uid:
        result["story_node_uid"] = story_uid
        result["story_node_created"] = story_created

    session_data = _load_session_data()
    env = session_data.get("env", "other").strip() if session_data else "other"

    if actual_design_uid and namespace:
        server = get_server()
        design_url = "{}/tencent/tb/workbench#/testx/{}/design/{}".format(server, namespace, actual_design_uid)
        if env == "codebuddy":
            # codebuddy 环境：提示使用 preview_url 工具打开页面
            result["design_url"] = design_url
            result["open_action"] = "preview_url"
            result["msg"] = "节点添加成功，请使用 preview_url 工具打开测试设计页面：{}".format(design_url)
        else:
            # 会话模式：返回 testbuddy 测试设计链接
            result["design_url"] = design_url
            result["msg"] = "节点添加成功，可通过以下链接查看测试设计：{}".format(design_url)

    return result


def handle_update(data, design_uid):
    """处理更新节点操作"""
    if not isinstance(data, list):
        return {"status": "error", "msg": "输入必须是节点数组，当前类型：{}".format(type(data).__name__)}

    # 校验每个节点
    for idx, node in enumerate(data):
        is_valid, msg = validate_node_structure(node, idx)
        if not is_valid:
            return {"status": "error", "msg": "节点校验失败: {}".format(msg)}

    # 补充 source 字段（未指定时从环境变量读取，默认为 CB_PLUGIN）
    source = get_source()
    for node in data:
        if not node.get("source"):
            node["source"] = source

    # 覆盖写入（不累积旧数据，避免失败重试时节点重复）
    update_data = {"added": [], "updated": data, "deleted": []}

    # 保存文件
    save_update_file(design_uid, update_data)

    # 根据模式决定处理方式
    mode = get_mode()
    node_uids = [node["uid"] for node in data if node.get("uid")]

    if mode == "mindmap":
        # mindmap 模式：调用 show_node 接口直接渲染到脑图上
        if design_uid:
            show_result = call_show_node(design_uid, node_uids)
            if show_result and show_result.get("status") == "error":
                return show_result

        return {
            "status": "success",
            "action": "update",
            "design_uid": design_uid,
            "stats": {
                "updated": len(data),
                "total_added": len(update_data["added"]),
                "total_updated": len(update_data["updated"]),
                "total_deleted": len(update_data["deleted"]),
            },
            "msg": "节点已渲染至脑图上",
        }

    # chat 模式：调用 save_node.py 保存到服务端
    save_result = call_save_node(design_uid)
    if save_result.get("status") == "error":
        return save_result

    # 服务端可能返回新创建的 design_uid（当传入为空时由服务端自动创建）
    actual_design_uid = save_result.get("design_uid", design_uid)
    # 从 batch-save 接口返回值中获取 namespace（服务端通过 token 解析得到）
    namespace = save_result.get("namespace", "") or ""

    filename = "{}-update.json".format(actual_design_uid) if actual_design_uid else "pending-update.json"
    target_file = os.path.join(TESTBUDDY_DIR, filename)

    result = {
        "status": "success",
        "action": "update",
        "design_uid": actual_design_uid,
        "target_file": target_file,
        "stats": {
            "updated": len(data),
            "total_added": len(update_data["added"]),
            "total_updated": len(update_data["updated"]),
            "total_deleted": len(update_data["deleted"]),
        },
    }

    session_data = _load_session_data()
    env = session_data.get("env", "other").strip() if session_data else "other"

    if actual_design_uid and namespace:
        server = get_server()
        design_url = "{}/tencent/tb/workbench#/testx/{}/design/{}".format(server, namespace, actual_design_uid)
        if env == "codebuddy":
            # codebuddy 环境：提示使用 preview_url 工具打开页面
            result["design_url"] = design_url
            result["open_action"] = "preview_url"
            result["msg"] = "节点更新成功，请使用 preview_url 工具打开测试设计页面：{}".format(design_url)
        else:
            # 会话模式：返回 testbuddy 测试设计链接
            result["design_url"] = design_url
            result["msg"] = "节点更新成功，可通过以下链接查看测试设计：{}".format(design_url)

    return result


def handle_delete(data, design_uid):
    """处理删除节点操作"""
    if not isinstance(data, list):
        return {"status": "error", "msg": "输入必须是 uid 数组，当前类型：{}".format(type(data).__name__)}

    # 校验每个 uid
    for idx, uid in enumerate(data):
        if not isinstance(uid, str) or not uid.strip():
            return {"status": "error", "msg": "[{}]: uid 必须是非空字符串".format(idx)}

    # 覆盖写入（不累积旧数据，避免失败重试时节点重复）
    update_data = {"added": [], "updated": [], "deleted": data}

    # 保存文件
    save_update_file(design_uid, update_data)

    # 根据模式决定处理方式
    mode = get_mode()

    if mode == "mindmap":
        # mindmap 模式：调用 show_node 接口直接渲染到脑图上
        if design_uid:
            show_result = call_show_node(design_uid, data)
            if show_result and show_result.get("status") == "error":
                return show_result

        return {
            "status": "success",
            "action": "delete",
            "design_uid": design_uid,
            "stats": {
                "deleted": len(data),
                "total_added": len(update_data["added"]),
                "total_updated": len(update_data["updated"]),
                "total_deleted": len(update_data["deleted"]),
            },
            "msg": "节点已渲染至脑图上",
        }

    # chat 模式：调用 save_node.py 保存到服务端
    save_result = call_save_node(design_uid)
    if save_result.get("status") == "error":
        return save_result

    # 从 batch-save 接口返回值中获取 namespace（服务端通过 token 解析得到）
    namespace = save_result.get("namespace", "") or ""

    filename = "{}-update.json".format(design_uid) if design_uid else "pending-update.json"
    target_file = os.path.join(TESTBUDDY_DIR, filename)

    result = {
        "status": "success",
        "action": "delete",
        "target_file": target_file,
        "stats": {
            "deleted": len(data),
            "total_added": len(update_data["added"]),
            "total_updated": len(update_data["updated"]),
            "total_deleted": len(update_data["deleted"]),
        },
    }

    session_data = _load_session_data()
    env = session_data.get("env", "other").strip() if session_data else "other"

    if design_uid and namespace:
        server = get_server()
        design_url = "{}/tencent/tb/workbench#/testx/{}/design/{}".format(server, namespace, design_uid)
        if env == "codebuddy":
            # codebuddy 环境：提示使用 preview_url 工具打开页面
            result["design_url"] = design_url
            result["open_action"] = "preview_url"
            result["msg"] = "节点删除成功，请使用 preview_url 工具打开测试设计页面：{}".format(design_url)
        else:
            # 会话模式：返回 testbuddy 测试设计链接
            result["design_url"] = design_url
            result["msg"] = "节点删除成功，可通过以下链接查看测试设计：{}".format(design_url)

    return result


def handle_validate(data, file_path):
    """处理校验操作，不写入文件"""
    if not isinstance(data, list):
        return {
            "status": "error",
            "action": "validate",
            "file_path": file_path,
            "msg": "输入必须是节点数组，当前类型：{}".format(type(data).__name__),
        }

    # 校验每个节点
    for idx, node in enumerate(data):
        is_valid, msg = validate_node_structure(node, idx)
        if not is_valid:
            return {
                "status": "error",
                "action": "validate",
                "file_path": file_path,
                "msg": "节点校验失败: {}".format(msg),
            }

    return {
        "status": "success",
        "action": "validate",
        "file_path": file_path,
        "stats": {"total_nodes": len(data), "valid_nodes": len(data)},
    }


if __name__ == "__main__":
    # Windows 下设置标准输出编码为 UTF-8
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "status": "error",
                    "msg": "用法:\n"
                    "  python write_node_from_file.py validate <file_path>\n"
                    "  python write_node_from_file.py <action> <design_uid> <file_path>\n"
                    "  action: add | update | delete | validate\n"
                    "  design_uid: 设计文件的唯一标识（validate 模式不需要）\n"
                    "  file_path: 包含节点数据的文件路径\n"
                    "  支持格式: JSON (.json), YAML (.yaml/.yml), Markdown (.md)",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    action = sys.argv[1]

    # 校验 action 参数
    if action not in ["add", "update", "delete", "validate"]:
        print(
            json.dumps(
                {"status": "error", "msg": "action 必须是 add/update/delete/validate 之一，当前值：{}".format(action)},
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    # validate 模式：python write_node_from_file.py validate <file_path>
    if action == "validate":
        if len(sys.argv) < 3:
            print(
                json.dumps(
                    {"status": "error", "msg": "用法: python write_node_from_file.py validate <file_path>"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)
        file_path = sys.argv[2]
        if not os.path.exists(file_path):
            print(
                json.dumps(
                    {"status": "error", "action": "validate", "msg": "文件不存在: {}".format(file_path)},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)
        try:
            data, error = load_file_data(file_path)
            if error:
                print(
                    json.dumps(
                        {"status": "error", "action": "validate", "file_path": file_path, "msg": error},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                sys.exit(1)
            result = handle_validate(data, file_path)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(0 if result.get("status") == "success" else 1)
        except Exception as e:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "action": "validate",
                        "file_path": file_path,
                        "msg": "脚本执行异常: {}".format(str(e)),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)

    # add/update/delete 模式：python write_node_from_file.py <action> <file_path> [--design_uid <design_uid>]
    # 兼容旧格式：python write_node_from_file.py <action> <design_uid> <file_path>
    remaining_args = sys.argv[2:]
    design_uid = ""
    file_path = ""

    # 解析 --design_uid 参数
    if "--design_uid" in remaining_args:
        idx = remaining_args.index("--design_uid")
        if idx + 1 < len(remaining_args):
            design_uid = remaining_args[idx + 1]
            remaining_args = remaining_args[:idx] + remaining_args[idx + 2 :]
        else:
            print(
                json.dumps(
                    {"status": "error", "msg": "--design_uid 参数缺少值"},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            sys.exit(1)

    # 剩余参数作为 file_path（兼容旧格式：可能是 <design_uid> <file_path> 或 <file_path>）
    if len(remaining_args) == 2 and not design_uid:
        # 旧格式：<design_uid> <file_path>
        design_uid = remaining_args[0]
        file_path = remaining_args[1]
    elif len(remaining_args) == 1:
        # 新格式：<file_path>（design_uid 可能通过 --design_uid 传入，也可能为空）
        file_path = remaining_args[0]
    else:
        print(
            json.dumps(
                {
                    "status": "error",
                    "msg": "用法: python write_node_from_file.py <action> <file_path> [--design_uid <design_uid>]\n"
                    "  action: add | update | delete\n"
                    "  file_path: 包含节点数据的文件路径\n"
                    "  --design_uid: 设计文件的唯一标识（可选，不传则由服务端自动创建）",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(1)

    # 校验文件是否存在
    if not os.path.exists(file_path):
        print(json.dumps({"status": "error", "msg": "文件不存在: {}".format(file_path)}, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        # 加载并解析文件
        data, error = load_file_data(file_path)
        if error:
            print(json.dumps({"status": "error", "msg": error}, ensure_ascii=False, indent=2))
            sys.exit(1)

        # 根据 action 执行对应操作
        if action == "add":
            result = handle_add(data, design_uid)
        elif action == "update":
            result = handle_update(data, design_uid)
        elif action == "delete":
            result = handle_delete(data, design_uid)

        # 输出结果
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result.get("status") == "success" else 1)

    except Exception as e:
        print(json.dumps({"status": "error", "msg": "脚本执行异常: {}".format(str(e))}, ensure_ascii=False, indent=2))
        sys.exit(1)
