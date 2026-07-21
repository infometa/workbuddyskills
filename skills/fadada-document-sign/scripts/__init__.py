"""法大大电子签发起签署 Skill 脚本包。

提供以下脚本：
- upload_file.py: 上传合同文件到法大大平台
- initiate_sign.py: 发起合同签署任务
- list_templates.py: 查询签署模板列表
- get_template_detail.py: 查询签署模板详情
- query_sign_status.py: 查询签署任务状态
- utils.py: 公共工具函数

使用示例：
    # 上传文件
    python scripts/upload_file.py --file-path "/path/to/contract.pdf" --file-name "合同.pdf"

    # 发起签署
    python scripts/initiate_sign.py --task-name "劳动合同签署" --file-ids '["file_id"]' --signers '[{"name":"张三","phone":"13800138000","actorType":"person"}]'

    # 查询模板
    python scripts/list_templates.py
    python scripts/get_template_detail.py --template-id "xxx"

    # 查询状态
    python scripts/query_sign_status.py --task-id "xxx"
"""

__version__ = "1.0.0"
__author__ = "WorkBuddy"
