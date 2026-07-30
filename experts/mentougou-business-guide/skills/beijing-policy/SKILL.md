---
name: beijing-policy
version: 1.0.0
description: 北京市级政策知识库。当用户涉及北京市级小微企业、OPC创业、科技创新、人才引进等政策查询时使用。门头沟区是北京市下辖区，市级政策同样适用。
---

# 北京市级政策知识库

## 角色定位

作为北京市级营商政策的知识库，补充门头沟区级政策未覆盖的场景。门头沟区是北京市下辖区，北京市级政策对门头沟注册企业同样有效。

## 使用场景

当 `mentougou-policy` 未命中时，自动降级到本 Skill 检索北京市级政策。

## 政策分类

### 参考文件目录

| 文件 | 覆盖范围 |
|------|---------|
| `references/北京市OPC政策.md` | 北京市针对一人公司/OPC的专项政策 |
| `references/小微企业政策.md` | 北京市小微企业普惠性税收优惠、财政补贴 |
| `references/创新创业政策.md` | 北京市科技创新、创业孵化、人才引进政策 |

## 工作流程

1. **本地知识库检索**：查对应 references 文件
   - 命中 → 输出政策卡片，标注 `[北京市级]`
   - 未命中 → 步骤2
2. **联网补充检索**：使用 `multi-search-engine`，`site:beijing.gov.cn` 限定
   - 命中 → 更新本地知识库 → 输出
   - 未命中 → 步骤3
3. **降级到全国通用**：使用 `multi-search-engine`，`site:gov.cn` 限定

## 关键域名

- 北京市人民政府：www.beijing.gov.cn
- 北京市税务局：beijing.chinatax.gov.cn
- 北京市人社局：rsj.beijing.gov.cn
- 北京市科委：kw.beijing.gov.cn
- 北京政务服务网：banshi.beijing.gov.cn

## 时效维护

- 政策缓存超30天自动失效
- 北京市OPC政策更新较快（2026年密集出台），建议每月检查更新
