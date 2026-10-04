# 读取多维表云文档元信息

> 从多维表记录中提取云文档字段的 file_id，再调用 get_file_info 获取元信息（文件名、大小、类型、修改时间等）

**适用场景**：用户要求查看多维表记录中引用的云文档的基本属性

**触发词**：云文档、文档信息、多维表文档、文件信息

- 场景涉及多维表记录中的云文档

**工具链**：dbsheet.list_records → drive.get_file_info

## 涉及工具

| 工具 | 服务 | 用途 |
|------|------|------|
| `dbsheet.list_records` | dbsheet | 查询多维表记录，获取包含云文档字段的记录数据 |
| `drive.get_file_info` | drive | 用提取到的 file_id 调用 get_file_info 获取文档元信息 |

## 执行流程

多维表记录中的云文档字段可能以不同形式返回文件标识：
- Url 类型字段：值含 `address`（可能是分享链接），需先用 `resolve_file` 转为 file_id
- 其他字段中直接包含 fileId 或文件 ID 字符串

取到 file_id 后：
- 单个文档：`drive.get_file_info(file_id="xxx")` 获取名称、大小、类型、修改时间
- 多个文档：`drive.batch_get_file_info(file_ids=["id1", "id2"])` 批量获取

注意：此流程仅返回云文档的元信息，不返回文档内容。如需读取内容，需根据文档类型选择对应工具（.otl 用 `otl.block_query`，.docx 用 `read_file_content` 等）。
