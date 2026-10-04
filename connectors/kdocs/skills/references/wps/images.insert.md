# wps.images.insert

#### 功能说明

在文档、段落或区间插入图片（file_path 为图片 URL）。

| 场景 | 调用顺序 |
| --- | --- |
| 向在线文档插入在线图片 | `wps.images.insert` |
| 向在线文档插入本地图片 | `upload_attachment` → `download_attachment` → `wps.images.insert` |

本地图片先通过 `upload_attachment` 上传，取返回的 `object_id` 作为 `download_attachment.attachment_id`；将 `download_attachment` 返回的 `download_url` 传给 `file_path`，不是 `url`。

> 本地图片插入示例：
1. `upload_attachment(file_id, filename, content_base64, content_type)`，取返回的 `object_id`。
2. `download_attachment(file_id, attachment_id=object_id)`，取返回的 `download_url`。
3. `wps.images.insert(file_id, scope="documents", file_path=download_url)`。

#### 支持功能

| 功能简述 | 详情 |
|--------------|------|
| 按文档插入图片（file_path 为图片 URL） | [images-insert/documents_insert.md](images-insert/documents_insert.md) |
| 按段落插入图片（file_path 为图片 URL） | [images-insert/paragraphs_insert.md](images-insert/paragraphs_insert.md) |
| 按字符区间插入图片（file_path 为图片 URL） | [images-insert/ranges_insert.md](images-insert/ranges_insert.md) |
