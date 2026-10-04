# 工具组合参考

先按主文档判断能力，确认当前工具可见且输入可用，再选择组合。这里的调用是参数示意；执行时使用当前 schema 和前一步的真实返回值，不把示例 ID 或时间戳当作实际数据。

## 通用约定

- “上传”指 `create_upload` → 按返回信息上传二进制 → `complete_upload`；已有有效 file_id 时省略。
- “交付”按用户保存偏好和最终产物类型决定：本地实际下载、云文档创建或两者。拿到下载链接不代表本地保存成功。
- 每一步检查 MCP 错误、isError 和下一步所需字段；失败时不继续传递空 ID。
- 中间 file_id 可直接供下一工具使用，无需反复上传下载，不默认创建中间云文档。

## 格式转换与处理

| 用户需求 | 处理链（之后按主文档交付） |
|----------|--------------------------|
| 单图转 Word/Excel/Markdown/TXT | 上传 → convert_image(file_id=输入, source_type="image", target_type=目标) |
| 单图转 PDF | 上传 → convert_image_to_pdf(file_id=输入) |
| 多图生成 PDF/Word/Excel | 逐图上传 → convert_images_to_pdf/word/excel(file_ids=有序图片ID数组) |
| 多图 OCR 合并文字 | 逐图上传 → convert_images_to_text(file_ids=有序图片ID数组, target_type="txt"或"md")；Markdown 可存云端，TXT 不可 |
| PDF 转 Word/Excel/Markdown/TXT | 上传 → convert_pdf(file_id=输入, source_type="pdf", target_type=目标) |
| TXT 转 Word | 上传 → convert_txt(file_id=输入, source_type="txt", target_type="word") |
| 增强后转 Word | 上传 → enhance_image(file_id=输入, enhance_mode=所需模式) → convert_image(file_id=增强结果, source_type="image", target_type="word") |
| 高清化/老照片修复 | 上传 → image_hd / restore_photo |
| 图片翻译 | 上传 → translate_image(file_id=输入, to=目标语言) |
| 图片加水印 | 上传 → watermark_image(file_id=输入, text=文字) |
| PDF 加水印 | 上传 → watermark_file(file_id=输入, file_type="pdf", text=文字) |
| 去水印 | 图片用 enhance_image(enhance_mode=10)，PDF 用 remove_watermark_pdf |
| 公式裁剪 | 上传 → extract_image(file_id=输入, extract_mode="formula")；交付公式图片，不承诺 LaTeX 文本 |
| 发票结构化识别 | 上传 → extract_receipt(file_id=输入) → 读取实际 bills_list；仅有文件引用时下载 JSON 后解析 |
| 篡改/AI 生成检测 | 上传 → validate_image(file_id=输入, validate_mode=1或2) → 展示检测 JSON |
| Word 转 PDF | 上传 → convert_word(file_id=输入, source_type="word", target_type="pdf") |
| Excel 转 PDF | 上传 → convert_excel(file_id=输入, source_type="excel", target_type="pdf") |
| PPT 转 PDF | 上传 → convert_ppt(file_id=输入, source_type="ppt", target_type="pdf") |
| 旧格式升级（DOC→DOCX） | 上传 → convert_word(file_id=输入, source_type="word", target_type="docx") |
| 旧格式升级（XLS→XLSX） | 上传 → convert_excel(file_id=输入, source_type="excel", target_type="xlsx") |
| 旧格式升级（PPT→PPTX） | 上传 → convert_ppt(file_id=输入, source_type="ppt", target_type="pptx") |

## 多图生成一个 PDF：默认双保存

用户要求将已提供且顺序明确的图片生成一个 PDF，没有指定保存方式：

1. 核对图片数量 ≤100，按指定顺序上传或复用有效 ID。
2. `convert_images_to_pdf(file_ids=[图片1的ID, 图片2的ID, ...])`。
3. 检查真实结果；用结果中的可用 download_url，或通过 download_file 获取地址，实际下载并核验 PDF 页数、顺序和本地路径。
4. `create_cloud_doc(file_ids=[PDF结果ID], file_type="pdf", title="扫描图片合并")`。
5. 按两端实际成功状态反馈。云端失败保留本地结果；不能为了补存而重新合成已成功的 PDF。

云端明确要求时可省略本地下载；仅本地要求时不创建云文档。

## 图片文字编辑

1. `scan_image_edit(file_id=图片ID)`，读取实际返回的 `result.urls` 和版面结构。
2. 在版面中定位用户要求的文字或区域；多处匹配且无法判断时询问位置。
3. OSS 模式调用 `edit_image(input_image=返回的input_image, document_info=返回的document_info地址, use_oss=1, edit_request=编辑对象)`。`update` 使用真实 start_char_idx/end_char_idx 和 target_text；移动/删除的字段见图片参考。
4. 检查实际返回的图片文件或业务 JSON，按主文档交付。不得使用不存在的 `edit_data` 参数。

## PDF 页面处理的边界

`convert_pdf_to_images` 返回按页序排列的图片 ID。用户明确要处理这些页面时，可对每页执行图片操作；只有用户接受结果是图像化 PDF 时才用 `convert_images_to_pdf` 组装处理后的页面。开始前说明不保留原文本层、书签、表单和签名语义，核对总页数 ≤100，最终校验页数和顺序。无法确认页数时先获取页面列表，超限就停止后续组装。

该流程不适用于把多个已有 PDF 合并的请求，不能作为原 PDF 合并的默认替代。不需要增强或重建时，不额外转换页面。

## 独立上传与云文档管理

| 用户需求 | 工具链 |
|----------|--------|
| 将现有 PDF/Word 等文件存入账号 | 上传完成 → create_cloud_doc(file_ids=[上传结果ID], file_type=实际类型)；不先转换 |
| 搜索云文档 | search_cloud_doc(keyword=关键词, start_time=按当前日期与时区计算的起始时间, end_time=结束时间) → 展示匹配结果 |
| 下载云文档 | 已有明确 cs_doc_id 或搜索确定目标 → download_cloud_doc(doc_id=cs_doc_id) → 实际下载到目标路径 |
| 查看文件夹 | query_cloud_dir() → 展示目录树 |
| 移动到文件夹 | 确定文档 cs_doc_id → 必要时 query_cloud_dir 解析目标 → move_cloud_doc(doc_ids=[已确定ID], dir_id=目标ID) |
| 移到根目录 | move_cloud_doc(doc_ids=[已确定ID], root=true)，不需要查询目录 |
| 保存到指定文件夹 | create_cloud_doc(file_ids=[真实文件ID], file_type=实际类型, dir_name=明确名称)，或使用已明确的 dir_id |

搜索有多个匹配或目录名称存在歧义时，不选择第一项冒充已确定目标。用户已提供明确 ID、选择或顺序时，不重复确认。云文档链接与临时下载链接不同；保存多个 PDF 是多个云文档，不是一个合并文件。

## 批量与数量限制

- 单次多图合并最多 100 张。用户要求一个文件而输入超过上限时，明确当前不能完成，不自动减少页面或分卷。
- 只有用户接受多个分卷时才按 ≤100 张分批，标明卷号；不能承诺之后把分卷再次合成一个文件。
- 独立文件逐项处理并记录成功、失败和未处理项。相同故障连续影响多个输入时停止受影响流程，避免无意义重复；不取消已经成功的结果。
- ID 或地址过期时按错误参考恢复，不假定固定 24 小时有效。
