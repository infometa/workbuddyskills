---
name: cos-storage
description: |
  访问腾讯云 COS 存储桶 (uae-marketing-1448789884)，提供文件列表、读取、搜索操作。
  用于读取阿联酋市场营销相关的知识库文件：市场数据、消费者报告、广告投放指南、pre-production-checklist 等。
  支持 public-read manifest.json 免密访问；如 manifest 不可访问，可回退到 AWS SigV4 签名访问。
user-invocable: false
---

# COS 存储桶访问

## 存储桶信息

- 存储桶：`uae-marketing-1448789884`
- 区域：`ap-shanghai`
- 终端节点：`cos.ap-shanghai.myqcloud.com`
- 公开索引：`https://uae-marketing-1448789884.cos.ap-shanghai.myqcloud.com/manifest.json`（public-read）

## 实际目录结构（以 manifest 为准）

```
cos://uae-marketing-1448789884/
├── china-round/        # 中文采集的营销数据（24 个文件）
├── japan-round/        # 日文/日本视角补充数据
├── marketing/          # 核心营销指南与清单
│   ├── pre-production-checklist.md    # 视频/图片生成前置清单
│   ├── uae-consumer-profiles.md
│   └── ...
├── sources/            # 原始网页备份
├── textbooks/          # 教材与法规原文
└── uae-round/          # 阿拉伯语/本地视角数据
```

## 使用方法

通过 `scripts/cos_client.py` 脚本访问存储桶，工作目录为脚本所在目录：

```bash
cd skills/cos-storage/scripts

# 查看 manifest 摘要（无需密钥）
python cos_client.py manifest

# 列出所有文件
python cos_client.py list

# 列出指定前缀下的文件
python cos_client.py list china-round/

# 读取文件内容
python cos_client.py read marketing/pre-production-checklist.md

# 搜索文件名包含关键字的文件
python cos_client.py search tiktok marketing/

# 检查文件是否存在
python cos_client.py exists marketing/pre-production-checklist.md
```

## 认证说明

1. **默认免密**：当前存储桶已开启 `manifest.json` 及对象文件的 public-read，`cos_client.py` 默认通过公开 URL 读取，无需配置密钥。
2. **密钥回退**：若后续关闭 public-read，可在脚本同级目录创建 `config.py`，或设置环境变量 `COS_SECRET_ID` / `COS_SECRET_KEY`，脚本将自动切换到 AWS SigV4 签名访问。

## AI 使用说明

1. **优先从 COS 读取权威数据**：当用户询问阿联酋市场相关问题，且 COS 中存在对应数据时，优先通过本脚本读取
2. **读取方式**：使用 `cd skills/cos-storage/scripts && python cos_client.py read <key>` 获取文件内容
3. **搜索方式**：不确定文件名时，先用 `search` 命令查找，再用 `read` 命令读取
4. **数据优先级**：`china-round/` / `marketing/` 优先用于中文场景；`uae-round/` 用于本地视角；`textbooks/` 用于法规与学术原文
