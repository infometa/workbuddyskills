# 云文档导入幻灯片

> 将外部 PPTX 文件中的指定幻灯片导入到已有演示文稿中

**适用场景**：用户希望将一个 PPTX 文件（通过 URL 获取）中的指定页面导入到当前演示文稿的指定位置。

**触发词**：导入幻灯片、导入PPT、导入演示文稿、插入幻灯片、合并PPT、合并幻灯片、导入PPT页面、把PPT导入、幻灯片导入

## 执行流程

> 通过 `wpp.import_slides` 将外部 PPTX 文件中的指定幻灯片导入到已有演示文稿中。

### 前置条件

- 目标演示文稿必须已存在于云文档中（需要 `link_id`）
- 源 PPTX 文件需通过可访问的 URL 提供（`object_url`）

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `link_id` | string | 是 | 目标演示文稿的 link_id（URL 路径参数） |
| `object_url` | string | 是 | 源 PPTX 文件的下载 URL |
| `slide_idx` | integer | 是 | 插入位置（目标文稿中的幻灯片索引，从 0 开始；用户说"第 n 页"时传 n-1；导入页面占据该位置，原页面后移；超出范围自动尾插） |
| `source_idxs` | integer[] | 是 | 要导入的源文件幻灯片索引数组（从 0 开始） |

### 执行流程

```
步骤 0: 获取目标演示文稿 link_id
        ├─ 用户提供了云文档链接 → 从 URL 路径末尾提取 link_id
        ├─ 用户提供了 link_id → 直接使用
        └─ 用户指定了文件名 → search_files(keyword=...) → 取 link_id

步骤 1: 获取源 PPTX 文件的 object_url
        ├─ 用户提供了外部 URL → 直接使用
        └─ 用户提供了云文档中的 PPTX → download_file(file_id) → 取下载 URL 作为 object_url

步骤 2: 确认导入参数
        → 向用户确认：插入位置（slide_idx）、要导入的源页面（source_idxs）
        → 用户说"第 n 页"时，slide_idx 传 n-1（索引从 0 开始）
        → 若用户未指定，默认 slide_idx=0，source_idxs=[0]（导入第一页到第一个位置）

步骤 3: 调用导入接口
        wpp.import_slides(
            link_id=<目标文件>,
            object_url=<源PPTX的URL>,
            slide_idx=<插入位置>,
            source_idxs=<源页面索引数组>
        )
        → 成功返回 HTTP 200 + JSON（与 core/execute 响应一致）
        → 展示导入结果给用户

步骤 4: 返回目标文档链接
        → get_file_link(link_id=...) → 展示在线编辑链接
```

### 错误处理

| 错误特征 | 说明 |
|----------|------|
| `validate_object_url` | object_url 域名不在白名单内，需更换为允许的 URL |
| 400 参数校验失败 | 检查 link_id、object_url 格式是否正确 |
