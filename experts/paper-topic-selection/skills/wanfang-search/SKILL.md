---
name: wanfang-search
description: 直接调用万方选题 API 检索论文与学者、推荐选题、评估新颖性、生成标题、产出领域报告。当用户说"用万方搜一下""/wanfang-search""直接调万方 API"或需要绕过专家团直接获取万方选题数据时启用。
---

# 万方选题 CLI 调用（wanfang-search）

本 skill 封装了 `bin/wanfang_topic_cli.py`，把万方选题 API 的 30+ 接口收敛为一组易用的命令行动作，支持单接口调用与两步联动（find Data → cluster → Paper）。

## 前置条件

- 包内 `bin/wanfang_topic_cli.py` 已内置万方 AppKey，开箱即可直接调用，无需设置环境变量（如需对外分发，请注意密钥随包暴露）。
  > 仅在你做了密钥外部化（将脚本改为从 `${APP_KEY}` 读取）时才需要设置以下环境变量：
  ```bash
  export APP_KEY="你的真实AppKey"
  ```
- 运行环境需有 Python 3。

## 调用方式

统一命令格式：

```bash
python bin/wanfang_topic_cli.py --keyword "<关键词>" --action <动作> [可选参数]
```

### 常用动作

| 动作 | 说明 | 关键参数 |
|------|------|----------|
| `read_paper` | 检索某方向的论文 | `--type HIGH/NEW/DEGREE/REVIEW` |
| `read_scholar` | 检索某方向的学者 | `--sort HINDEX/RELATIVITY/CITED` |
| `find_all` | 一键联动四个维度（学术/前沿/交叉/新主题）的 Data→Paper | `--type HIGH` |
| `assess` | 三维度新颖性评估（新颖性/主题延伸/学科渗透） | `--title` `--abstract` |
| `title_recommend` | 推荐标题模板 | — |
| `report_novelty` | 新颖性领域报告 | — |
| `report_periodical` | 期刊指南报告 | — |
| `pool_listpapers` | 按学科分类码浏览论文 | `--classCode B` |

### 示例

```bash
# 检索"帮信罪"高相关论文
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action read_paper --type HIGH

# 一键联动四个维度的知识脉络论文
python bin/wanfang_topic_cli.py --keyword "帮信罪" --action find_all

# 评估选题新颖性（标题/摘要可选，缺省用关键词兜底）
python bin/wanfang_topic_cli.py --keyword "帮信罪" \
  --title "帮助信息网络犯罪活动罪认定研究" \
  --abstract "本文研究帮助信息网络犯罪活动罪的司法认定难点" \
  --action assess
```

## 输出与相关性

- 脚本对 `read_paper` / `title_recommend` 自动附加 `_relevance` 字段（`OK` / `PARTIAL` / `SUSPICIOUS` / `EMPTY`），用于快速判断返回是否与关键词相关。
- 若返回 `SUSPICIOUS` 或 `EMPTY`，应先核对关键词是否准确，再决定是否重试；不要直接当成有效结果呈现给用户。
- 完整接口参数与返回结构见 `references/api.md`。

## 注意

- 本 skill 是专家团（team 型）之外的一个轻量直调入口，适合用户明确要"直接查万方"时使用；常规选题咨询仍走专家团 SOP 路线。
