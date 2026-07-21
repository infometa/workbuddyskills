# 顶会术语库（按领域分册）

按领域加载，三步翻译过程中作为强制参照。

## 加载策略

```
[基础层] general-cs-terms.md   — 总是加载
   ↓
[领域层] {ml-venues | nlp-venues | cv-venues | ir-data-venues}.md   — 按 Preflight P2 用户选择加载
   ↓
[用户层] config/user-glossary.yaml   — 用户上传时加载，**优先级最高**
```

## 文件清单

| 文件 | 适用会议 | 大致术语数 |
|---|---|---|
| general-cs-terms.md | 所有 | ~120 |
| ml-venues.md | NeurIPS / ICLR / ICML / AAAI / IJCAI | ~100 |
| nlp-venues.md | ACL / EMNLP / NAACL / EACL / COLING | ~90 |
| cv-venues.md | CVPR / ICCV / ECCV / WACV / BMVC | ~80 |
| ir-data-venues.md | SIGIR / WWW / KDD / CIKM / WSDM / VLDB / ICDE / SIGMOD | ~80 |

## 术语条目格式

```markdown
| English | 中文（首选） | 中文（备选） | 备注 |
```

- **首选**：本 Skill 默认输出此译法，与全文一致
- **备选**：仅当用户上下文已大量使用备选译法时才用，需在 Self-Check 报告中标注
- **不译保留**：该列模型 / 数据集 / 算法 / 会议名 全文保留英文

## 优先级冲突解决

```
用户 user-glossary.yaml > 领域 *-venues.md > general-cs-terms.md
```

冲突时打印警告：

```
⚠️ 术语 "embedding" 冲突：
  - 内置 ml-venues.md 译为「嵌入」
  - 用户 glossary 译为「嵌入向量」
  - 已采用用户译法，全文将统一为「嵌入向量」。
```

## 用户自定义术语库示例

见 [../../config/user-glossary.template.yaml](../../config/user-glossary.template.yaml)。
