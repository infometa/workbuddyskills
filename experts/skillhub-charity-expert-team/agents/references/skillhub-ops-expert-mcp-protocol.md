# 运维专家 · MCP 直传协议参考（⏸️ MCP 暂停期间归档，恢复时按此还原）

> 本文件是 `skillhub-ops-expert.md` 瘦身时下沉的内容——MCP 暂停期间这部分逻辑不会被执行，为避免主文档常驻这段"当前用不上"的协议细节，整体搬到这里存档。**MCP 恢复上线后，运维专家应参照本文件把对应逻辑原样贴回主文档**（详见文末「恢复操作指引」），本文件本身不需要运维专家在日常打包流程中读取。

## 一、MCP 直传逻辑（原步骤 5 的 ②③ 子步骤）

> 原位置：`skillhub-ops-expert.md` 步骤 5「读取身份 + 提交」，读完 wb_user_id 之后的 ②③ 两步。

2. **① 申请上传地址**：调用 **`ssvSkillHub` MCP 连接器**的 `request_upload` 工具（只传元数据）：

```
request_upload(
  skill_name   = {技能名},
  skill_md5    = {脚本算出的技能包 MD5},
  material_md5 = {脚本算出的材料包 MD5},
  wb_user_id   = {读取到的标识},
  idempotency_key = {wb_user_id + skill_md5 哈希}
)
→ 返回 upload_url（带 token）+ submission_id
```

3. **② 直传即入库**（用 Bash 调 curl，二进制 multipart，**零 base64**）：

```bash
curl -sf -X POST "{upload_url}" \
  -F "skill=@{skill-name}-v{version}.zip" \
  -F "material=@{skill-name}-material-{date}.zip"
# 上传端点同步校验+入库，响应体即结果 { status: "submitted", market_url }
```

> Server 自建上传端点在接收文件时**同步**完成 md5 复核 + 材料三件校验 + 原子入库，HTTP 响应直接返回 `market_url`，**无需第三步 confirm**。
> curl 失败（网络/超时/非 2xx）→ **不重试 base64**，直接走**步骤 5.5 问卷应急通道**。

> 💡 文件经上传地址直传，不走 MCP、不做 base64，天然支持大包。未成功上传入库的草稿会被 Server TTL 过期清理。

## 二、MCP 服务端信息（项目配置）

> 原位置：`skillhub-ops-expert.md`「频率限制规则」章节之后。

> 📖 完整 MCP 协议定义见专家团根目录 `MCP-DESIGN.md`，服务端实现见 `MCP-SERVER-IMPL.md`。
> 提交为**预签名 URL 两步式**（开放共创，无 Token）：`request_upload`（元数据）→ curl multipart 直传即入库（零 base64，响应即返回 market_url）

> 🔌 **MCP 连接器 id：`ssvSkillHub`**。**若用户尚未配置**，运维专家应先引导用户在 WorkBuddy「MCP 服务管理 → 配置 MCP」中添加（名称务必填 `ssvSkillHub`，按下方模板填写），配置完成且显示绿色（已连接）后再发起提交；**若连接器已存在但名称不对**，Agent 会找不到 `request_upload` 工具，需提示用户改名重新添加。本专家团面向**开放共创**，使用者无需注册工具箱平台，直接复用 WorkBuddy 本地身份（`wb_user_id` 读取方式见步骤 5.1）；MCP 不可用时按步骤 5.5/5.6 自动兜底，无需用户额外配置。

用户在「配置 MCP」中需填写的连接器信息（仅列用户实际要填的字段，`wb_user_id` 读取、重试与本地兜底路径等内部逻辑已在步骤 5/5.1/5.5/5.6 说明，不重复列出）：

```yaml
mcp_connector:
  id: "ssvSkillHub"     # ★ 必须与此一致，与 .mcp.json 的 server key 一致
  type: "http"          # Streamable HTTP
  url: ""               # 待平台提供（测试用 http://127.0.0.1:8800/mcp）
  auth:
    type: "none"        # 开放共创：不做 Token 鉴权
  timeout: 30s
```

## 三、恢复操作指引（MCP 建设完成、正式启用后执行）

1. 把上面「一、MCP 直传逻辑」的 ②③ 两步，原样贴回 `skillhub-ops-expert.md` 步骤 5（读完 wb_user_id 之后），删除该处指向本文件的占位说明
2. 把上面「二、MCP 服务端信息」整节，原样贴回 `skillhub-ops-expert.md`「频率限制规则」之后，删除该处指向本文件的占位说明
3. 步骤 5.5 标题与触发条件改回"仅当步骤 5 的 `request_upload` 或直传 curl 失败 1 次后才触发"（非"直接进入"）
4. 步骤 6 回报模板的 `提交结果` 字段恢复为含 `MCP 提交`/`submission_id`/`market_url` 的表述
5. 关键规则 #5、#8、#13、频率限制规则标题，删除其中的 "⏸️ [MCP 暂停中/暂停期间]" 标注，恢复为常态表述
6. frontmatter `description` 删除"⏸️ 当前 MCP 服务端建设放缓…"这句说明
7. 完成后可删除本文件，或保留作为历史记录
