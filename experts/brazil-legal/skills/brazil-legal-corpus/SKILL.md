---
name: brazil-legal-corpus
description: |
  Brazilian legal, compliance, business development and finance/taxation reference corpus.
  Provides structured access to the brazil-legal-compliance COS bucket via manifest.json.
read_when:
  - 用户查询巴西法律法规或合规要求
  - 用户查询巴西公司注册、合同、知识产权、行业准入、产品认证
  - 用户查询巴西税务、投资激励、中巴税收协定
  - 巴西法务法规专家需要引用语料库内容
---

# 巴西法律与商业语料库 (Brazil Legal & Business Corpus)

## 概述

本语料库为**巴西法务合规专家**的强制性数据入口。当用户提出任何与巴西法律、合规、公司注册、税务、投资或商业环境相关的问题时，必须优先通过本语料库获取权威信息，再组织回答。

所有基础语料统一存储在 COS 存储桶中，通过 manifest.json 索引访问。

## 存储桶访问策略（manifest.json）

### 核心机制

存储桶采用**单文件 public-read + 桶级 list 关闭**策略。这意味着：
- ✅ 知道精确 URL 可以直接读取文件
- ❌ 无法通过 COS API 或浏览器枚举文件清单

因此通过 `manifest.json` 作为文件索引，AI 读取索引后再按需读取文件，无需密钥即可访问。

### 唯一入口

```
https://brazil-legal-compliance-1448789884.cos.ap-shanghai.myqcloud.com/manifest.json
```

### manifest.json 字段

```json
{ "url": "https://...full-path", "title": "...", "size": 12345 }
```

- `url`：文件的完整 COS 访问链接，直接用 WebFetch 读取
- `title`：文件中文名称
- `size`：文件大小（bytes）

## 使用流程

1. **读取 manifest**：从入口 URL 读取 manifest.json
2. **匹配需求**：根据用户问题，从 manifest 中筛选相关文件
3. **按需读取**：使用 manifest 中提供的 `url` 字段直接读取文件内容
4. **来源标注**：测试模式下必须标注实际使用的 URL

## 注意事项

- **禁止编造链接**：所有 URL 必须来自 manifest.json
- **manifest 缺失处理**：如果 manifest.json 不存在或为空，告知用户语料库索引暂不可用，无法访问桶内文件
- **时效性提示**：引用法律文件时注明版本日期；巴西联邦、州、市三级法规更新频繁

## 测试模式规则

当用户开启"语料库测试"或"测试模式"时：

1. 每个段落/表格后必须附加引用来源：
   ```
   【引用链接】
   https://xxxxx
   ```
2. 仅展示实际使用的数据来源，禁止编造
3. 每次回答末尾附加：
   ```
   【内容来源占比】
   语料库内容：XX%
   API实时数据：XX%
   其它推理与分析：XX%
   ```
