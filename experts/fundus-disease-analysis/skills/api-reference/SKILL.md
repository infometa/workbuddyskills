---
name: api-reference
description: Internal reference skill providing the complete Tencent Miying Fundus Multi-Disease AI API specification AND an executable CLI client (bin/fundus_ai.py) that performs real API calls. Not triggered by user directly; loaded as supporting context by the fundus-disease-analysis expert.
user-invocable: false
---

# 眼底多病种AI API 参考与调用工具

本 Skill 为「眼底彩照疾病分析专家」提供两部分能力：

## 1. 可执行客户端（真正调用 API）

专家包根目录 `bin/fundus_ai.py` 是真正调用眼底 AI 接口的命令行工具，负责：
- HMAC-SHA256 签名鉴权
- 图片上传（单张大图 form-data / 批量小图 JSON base64）
- 结果查询与轮询（直到 status 完成）
- gzip+base64 压缩的检测结果解码
- 47 维体征、22 种推测诊断的中文映射
- 结构化结果输出

**凭证（普角/超广角权限互斥，已内置，安装即用）**：

| 类型 | appId | token | hospitalId | aiType |
|------|-------|-------|-----------|--------|
| 普角 | `12708` | `69842f96c5b14c0ca8042fc309f3f087` | `12708` | 0/1/2 |
| 超广角 | `12719` | `7b131f5c5a3e4af080fb9e70382244ba` | `12719` | 12 |

- 同一凭证只有普角或超广角之一权限，**不能混用**。CLI 按 `--ai-type` 自动选对凭证。
- 可用 `--token`/`--app-id` 或环境变量 `FUNDUS_TOKEN`/`FUNDUS_APPID` 覆盖为自有正式凭证。

**一站式命令**（凭证自动选择）：
```bash
# 超广角
python3 bin/fundus_ai.py --env prod run --file <图> --ai-type 12 \
  --study-id study_xxx --desc-position 1 --camera-type 1 --out r.json
# 普角
python3 bin/fundus_ai.py --env prod run --file <图> --ai-type 0 \
  --study-id study_xxx --desc-position 0 --out r.json
```

子命令：`upload`（上传，≤5M自动Base64）、`query`（查询/轮询，30008=处理中）、`run`（一站式）、`decode`（离线解析返回JSON，普角+超广角结构通用）。

## 2. 接口规范参考

完整 API 接口规范见 `references/api-spec.md`，含：
- 三个接口的协议、地址、参数
- 普角青光眼/多病种结果字段
- 超广角 47 维体征表、22 种推测诊断表
- 状态码与错误码对照
- aiType 使用场景对照
