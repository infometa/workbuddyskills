#!/usr/bin/env python3
"""发起合同签署任务。

调用接口:
- /sign-task/create - 创建签署任务（基于文档）
- /sign-task/create-with-template - 创建签署任务（基于模板）

作用: 接收文件列表和签署方信息，发起签署流程，返回 taskId 和 signUrl

使用方式:
  # 普通发起（传入文件）
  python initiate_sign.py \
    --task-name "劳动合同签署" \
    --file-ids '["file_id"]' \
    --signers '[{"name":"张三","phone":"13800138000","actorType":"person"}]'

  # 模板发起
  python initiate_sign.py \
    --task-name "劳动合同签署" \
    --template-id "template_id" \
    --signers '[{"name":"张三","phone":"13800138000","actorType":"person","participantId":"xxx"}]'

  # 混合签署方（个人 + 企业）
  python initiate_sign.py \
    --task-name "采购合同签署" \
    --file-ids '["file_id"]' \
    --signers '[{"name":"杭州未来科技有限公司","contactName":"李经理","phone":"13800138000","actorType":"corp"},{"name":"王五","phone":"13900139000","actorType":"person"}]'

参数说明:
  --task-name (可选): 签署任务名称，默认"合同签署"
  --file-ids (可选): 文件ID列表JSON数组，普通发起时必填
  --template-id (可选): 模板ID，模板发起时必填
  --signers (必填): 签署方列表JSON数组
  --auto-start (可选): 是否自动提交，默认true
  --sign-deadline (可选): 签署截止时间 (yyyy-MM-dd HH:mm:ss)
  --notice-type (可选): 通知方式 sms/email/all
  --callback-url (可选): 签署结果回调地址
  --debug (可选): 开启调试日志
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List

from utils import (
    FASCClient,
    load_config,
    load_skill_context,
    print_result,
    success_response,
    error_response,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# API 端点
CREATE_TASK_ENDPOINT = "/sign-task/create"
CREATE_WITH_TEMPLATE_ENDPOINT = "/sign-task/create-with-template"
ADD_ACTOR_ENDPOINT = "/sign-task/actor/add"
GET_SIGN_URL_ENDPOINT = "/sign-task/actor/get-url"
SUBMIT_TASK_ENDPOINT = "/sign-task/start"

# 默认任务名称
DEFAULT_TASK_NAME = "合同签署"

# 签署方类型映射
ACTOR_TYPE_MAP = {
    "person": "person",      # 个人
    "corp": "corp",          # 企业
    "individual": "person",  # 别名：个人
    "enterprise": "corp",    # 别名：企业
}


def normalize_actor_type(actor_type: str) -> str:
    """标准化签署方类型。
    
    Args:
        actor_type: 原始类型字符串
        
    Returns:
        标准化后的类型 person/corp
    """
    return ACTOR_TYPE_MAP.get(actor_type.lower(), "person")


def build_files(files_json: str) -> List[Dict[str, Any]]:
    """解析文件列表JSON。
    
    Args:
        files_json: 文件ID列表JSON字符串
        
    Returns:
        文件列表
    """
    if not files_json:
        return []
    
    try:
        files = json.loads(files_json)
    except json.JSONDecodeError:
        raise ValueError("file-ids 格式错误，请提供有效的JSON数组")
    
    if not isinstance(files, list):
        raise ValueError("file-ids 必须是一个数组")
    
    result = []
    for idx, f in enumerate(files):
        if isinstance(f, str):
            result.append({"fileId": f})
        elif isinstance(f, dict):
            result.append(f)
        else:
            raise ValueError(f"file-ids[{idx}] 格式错误")
    
    return result


def build_signers(signers_json: str) -> List[Dict[str, Any]]:
    """解析签署方列表JSON并标准化。
    
    支持的格式:
    - 标准格式: {"name": "...", "phone": "...", "actorType": "person/corp", ...}
    - 兼容格式: {"signerType": "personal/org", "persons": [{"userName": ..., "contact": ...}], ...}
    
    Args:
        signers_json: 签署方列表JSON字符串
        
    Returns:
        标准化的签署方列表
    """
    if not signers_json:
        raise ValueError("signers 参数不能为空")
    
    try:
        signers = json.loads(signers_json)
    except json.JSONDecodeError:
        raise ValueError("signers 格式错误，请提供有效的JSON数组")
    
    if not isinstance(signers, list):
        raise ValueError("signers 必须是一个数组")
    
    result = []
    for idx, signer in enumerate(signers):
        if not isinstance(signer, dict):
            raise ValueError(f"signers[{idx}] 必须是对象")
        
        # 解析签署方类型
        raw_type = signer.get("actorType") or signer.get("type") or "person"
        actor_type = normalize_actor_type(raw_type)
        
        # 解析名称
        # 兼容 signers-data-card 组件格式
        persons = signer.get("persons", [])
        if persons and isinstance(persons, list):
            first_person = persons[0]
            if actor_type == "corp":
                name = first_person.get("orgName") or signer.get("name") or ""
            else:
                name = first_person.get("userName") or signer.get("name") or ""
            contact = first_person.get("contact") or signer.get("contact") or ""
        else:
            if actor_type == "corp":
                name = signer.get("name") or signer.get("orgName") or ""
            else:
                name = signer.get("name") or signer.get("userName") or ""
            contact = signer.get("contact") or ""
        
        # 解析联系方式
        phone = signer.get("phone") or ""
        email = signer.get("email") or ""
        if not phone and not email and contact:
            if "@" in contact:
                email = contact
            else:
                phone = contact
        
        # 解析经办人（企业签署方）
        contact_name = signer.get("contactName") or signer.get("contact_name") or ""
        if not contact_name and actor_type == "corp":
            # 企业签署方如果没有经办人，使用联系人
            contact_name = signer.get("userName") or ""
        
        if not name:
            raise ValueError(f"signers[{idx}] 缺少 name 字段")
        
        if not phone and not email:
            raise ValueError(f"签署方 {name} 必须提供 phone 或 email")
        
        normalized = {
            "name": name,
            "actorType": actor_type,
            "phone": phone,
            "email": email,
        }
        
        if contact_name:
            normalized["contactName"] = contact_name
        
        # 模板发起时需要的 participantId
        participant_id = signer.get("participantId") or signer.get("participant_id") or ""
        if participant_id:
            normalized["participantId"] = participant_id
        
        # 签署要求（企业签署方）
        if actor_type == "corp":
            sign_req = signer.get("sign_requirements") or signer.get("signRequirements") or "1"
            normalized["signRequirements"] = sign_req
        
        result.append(normalized)
    
    return result


def create_sign_task(
    client: FASCClient,
    task_name: str,
    files: List[Dict],
    signers: List[Dict],
    auto_start: bool = True
) -> Dict[str, Any]:
    """创建签署任务（基于文档）。
    
    Args:
        client: FASC 客户端
        task_name: 任务名称
        files: 文件列表 [{"fileId": "xxx"}, ...]
        signers: 签署方列表
        auto_start: 是否自动提交
        
    Returns:
        包含 taskId 等信息
    """
    # 构建 docs 数组
    docs = []
    for idx, f in enumerate(files):
        file_id = f.get("fileId") or f.get("file_id")
        docs.append({
            "docId": f"doc{idx+1}",
            "docName": task_name,
            "docFileId": file_id
        })
    
    # 构建 actors 数组
    actors = []
    for idx, signer in enumerate(signers):
        actor_id = f"signer{idx+1}"
        notification = {}
        if signer.get("phone"):
            notification = {
                "sendNotification": True,
                "notifyWay": "mobile",
                "notifyAddress": signer["phone"]
            }
        elif signer.get("email"):
            notification = {
                "sendNotification": True,
                "notifyWay": "email",
                "notifyAddress": signer["email"]
            }
        
        actors.append({
            "actor": {
                "actorId": actor_id,
                "actorType": signer.get("actorType", "person"),
                "actorName": signer.get("name", ""),
                "permissions": ["sign"],
                "notification": notification
            }
        })
    
    biz_content = {
        "initiator": {
            "idType": "corp",
            "openId": client.open_corp_id
        },
        "signTaskSubject": task_name,
        "signDocType": "contract",
        "autoStart": auto_start,
        "autoFinish": True,
        "docs": docs,
        "actors": actors
    }
    
    logger.info(f"创建签署任务: {task_name}, files={len(files)}, signers={len(signers)}")
    
    result = client.request(CREATE_TASK_ENDPOINT, biz_content)
    
    logger.info(f"创建任务响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def create_sign_task_with_template(
    client: FASCClient,
    task_name: str,
    template_id: str,
    signers: List[Dict],
    auto_start: bool = True
) -> Dict[str, Any]:
    """创建签署任务（基于模板）。
    
    Args:
        client: FASC 客户端
        task_name: 任务名称
        template_id: 模板ID
        signers: 签署方列表（需要包含 participantId）
        auto_start: 是否自动提交
        
    Returns:
        包含 taskId 等信息
    """
    # 构建 actors 数组（使用模板中的 participantId）
    actors = []
    for idx, signer in enumerate(signers):
        actor_id = f"signer{idx+1}"
        participant_id = signer.get("participantId", "")
        
        notification = {}
        if signer.get("phone"):
            notification = {
                "sendNotification": True,
                "notifyWay": "mobile",
                "notifyAddress": signer["phone"]
            }
        elif signer.get("email"):
            notification = {
                "sendNotification": True,
                "notifyWay": "email",
                "notifyAddress": signer["email"]
            }
        
        actor_data = {
            "actor": {
                "actorId": actor_id,
                "actorType": signer.get("actorType", "person"),
                "actorName": signer.get("name", ""),
                "permissions": ["sign"],
            }
        }
        
        # 如果有 participantId，使用模板中的角色
        if participant_id:
            actor_data["actor"]["participantId"] = participant_id
        
        if notification:
            actor_data["actor"]["notification"] = notification
        
        actors.append(actor_data)
    
    biz_content = {
        "initiator": {
            "idType": "corp",
            "openId": client.open_corp_id
        },
        "signTaskSubject": task_name,
        "signDocType": "contract",
        "autoStart": auto_start,
        "autoFinish": True,
        "templateId": template_id,
        "actors": actors
    }
    
    logger.info(f"基于模板创建签署任务: {task_name}, templateId={template_id}")
    
    result = client.request(CREATE_WITH_TEMPLATE_ENDPOINT, biz_content)
    
    logger.info(f"创建任务响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def add_sign_actor(
    client: FASCClient,
    task_id: str,
    signer: Dict[str, Any]
) -> Dict[str, Any]:
    """添加签署参与方。
    
    Args:
        client: FASC 客户端
        task_id: 任务ID（signTaskId）
        signer: 签署方信息
        
    Returns:
        添加结果
    """
    actor_type = signer.get("actorType", "person")
    
    biz_content = {
        "signTaskId": task_id,
        "actorType": actor_type,
        "actorName": signer.get("name", ""),
    }
    
    # 添加联系方式
    if signer.get("phone"):
        biz_content["actorMobile"] = signer["phone"]
    if signer.get("email"):
        biz_content["actorEmail"] = signer["email"]
    
    # 企业签署方
    if actor_type == "corp":
        if signer.get("contactName"):
            biz_content["contactName"] = signer["contactName"]
        if signer.get("openCorpId"):
            biz_content["openCorpId"] = signer["openCorpId"]
    
    # 模板发起时
    if signer.get("participantId"):
        biz_content["participantId"] = signer["participantId"]
    
    logger.info(f"添加签署方: {signer.get('name')}, type={actor_type}")
    
    result = client.request(ADD_ACTOR_ENDPOINT, biz_content)
    
    return result


def add_sign_actors(
    client: FASCClient,
    task_id: str,
    signers: List[Dict[str, Any]]
) -> List[str]:
    """批量添加签署参与方。
    
    Args:
        client: FASC 客户端
        task_id: 任务ID
        signers: 签署方列表
        
    Returns:
        签署方账号列表
    """
    actor_accounts = []
    
    for signer in signers:
        result = add_sign_actor(client, task_id, signer)
        actor_account = result.get("actorAccount") or result.get("actor_account")
        if actor_account:
            actor_accounts.append(actor_account)
    
    return actor_accounts


def get_sign_url(
    client: FASCClient,
    task_id: str,
    actor_id: str = None
) -> Dict[str, Any]:
    """获取签署链接。
    
    Args:
        client: FASC 客户端
        task_id: 任务ID（signTaskId）
        actor_id: 签署方ID（signer1等），不传则获取发起方链接
        
    Returns:
        包含 signUrl 等信息
    """
    biz_content = {"signTaskId": task_id}
    
    if actor_id:
        biz_content["actorId"] = actor_id
    
    logger.info(f"获取签署链接: signTaskId={task_id}, actorId={actor_id}")
    
    result = client.request(GET_SIGN_URL_ENDPOINT, biz_content)
    
    logger.info(f"签署链接响应: {json.dumps(result, ensure_ascii=False)}")
    
    return result


def submit_sign_task(client: FASCClient, task_id: str) -> Dict[str, Any]:
    """提交签署任务。
    
    Args:
        client: FASC 客户端
        task_id: 任务ID（signTaskId）
        
    Returns:
        提交结果
    """
    biz_content = {"signTaskId": task_id}
    
    logger.info(f"提交签署任务: {task_id}")
    
    result = client.request(SUBMIT_TASK_ENDPOINT, biz_content)
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="发起合同签署任务",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--task-name", default=DEFAULT_TASK_NAME, help="签署任务名称")
    parser.add_argument("--file-ids", default="", help="文件ID列表JSON数组")
    parser.add_argument("--template-id", default="", help="模板ID（模板发起时使用）")
    parser.add_argument("--signers", required=True, help="签署方列表JSON数组")
    parser.add_argument("--auto-start", type=lambda x: x.lower() == "true", default=True, help="是否自动提交，默认true")
    parser.add_argument("--sign-deadline", default="", help="签署截止时间")
    parser.add_argument("--notice-type", default="all", help="通知方式: sms/email/all")
    parser.add_argument("--callback-url", default="", help="签署结果回调地址")
    parser.add_argument("--skill-context-json", default="", help="Skill运行时上下文(自动注入)")
    parser.add_argument("--debug", action="store_true", help="开启调试日志")
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        # 1. 解析参数
        files = build_files(args.file_ids)
        signers = build_signers(args.signers)
        
        # 2. 验证参数
        if not files and not args.template_id:
            print_result(error_response("必须提供 --file-ids 或 --template-id"))
            return
        
        if args.template_id and not files:
            # 模板发起模式
            use_template = True
        else:
            use_template = False
        
        logger.info(f"任务名称: {args.task_name}")
        logger.info(f"发起模式: {'模板' if use_template else '普通'}")
        logger.info(f"签署方数量: {len(signers)}")
        
        # 3. 加载配置并创建客户端
        config = load_config()
        client = FASCClient(config)
        
        # 4. 创建签署任务
        if use_template:
            task_result = create_sign_task_with_template(
                client,
                args.task_name,
                args.template_id,
                signers,
                args.auto_start
            )
        else:
            task_result = create_sign_task(
                client,
                args.task_name,
                files,
                signers,
                args.auto_start
            )
        
        task_id = task_result.get("signTaskId") or task_result.get("taskId")
        if not task_id:
            print_result(error_response("创建签署任务失败：未返回任务ID"))
            return
        
        # 5. 如果不是自动提交，添加签署方并提交
        if not args.auto_start:
            # 添加签署方
            actor_accounts = add_sign_actors(client, task_id, signers)
            
            # 提交任务
            submit_sign_task(client, task_id)
        
        # 6. 获取签署链接
        sign_urls = []
        for idx, signer in enumerate(signers):
            # 使用签署方 actorId 获取签署链接
            actor_id = f"signer{idx+1}"
            url_result = get_sign_url(client, task_id, actor_id)
            sign_url = url_result.get("actorSignTaskUrl") or url_result.get("signUrl") or url_result.get("sign_url")
            if sign_url:
                sign_urls.append({
                    "name": signer.get("name"),
                    "actorType": signer.get("actorType"),
                    "signUrl": sign_url
                })
        
        # 如果没有获取到单独的签署链接，尝试获取发起方链接
        if not sign_urls:
            url_result = get_sign_url(client, task_id)
            sign_url = url_result.get("signUrl") or url_result.get("sign_url")
            if sign_url:
                sign_urls.append({
                    "name": "发起方",
                    "signUrl": sign_url
                })
        
        # 7. 返回成功结果
        result = success_response({
            "taskId": task_id,
            "taskName": args.task_name,
            "status": "已发起",
            "signUrls": sign_urls,
            "signerCount": len(signers),
            "files": files if files else [{"templateId": args.template_id}],
        })
        print_result(result)
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        print_result(error_response(str(e)))
    except Exception as e:
        logger.error(f"发起签署失败: {e}")
        print_result(error_response(f"发起签署失败: {e}"))


if __name__ == "__main__":
    main()
