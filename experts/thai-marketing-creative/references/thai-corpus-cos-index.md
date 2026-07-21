# ThaiCLI & Thai-H6 语料库索引

## 存储桶信息

- **Bucket**: `indonesian-news-corpus-1257812465`
- **Region**: `ap-beijing`
- **Base Path**: `thai-marketing-creative/thai-corpus/`
- **COS Domain**: `indonesian-news-corpus-1257812465.cos.ap-beijing.myqcloud.com`

## 文件清单

### CLI（泰国文化智力基准）

| COS Key | 说明 | 样本数 |
|---------|------|--------|
| `thai-marketing-creative/thai-corpus/cli/CLI_factoid.parquet` | 文化事实问答（Parquet格式） | 1790 |
| `thai-marketing-creative/thai-corpus/cli/CLI_instruction.parquet` | 文化指令任务（Parquet格式） | 100 |
| `thai-marketing-creative/thai-corpus/cli/CLI_instruction.csv` | 文化指令任务（CSV格式） | 100 |

**CLI主题分布**：
- Factoid: 王室(520) / 宗教(220) / 文化(210) / 经济(210) / 人文(210) / 生活方式(210) / 政治(210)
- Instruction: 王室(25) / 宗教(25) / 文化(10) / 经济(10) / 人文(10) / 生活方式(10) / 政治(10)

### H6（泰语核心能力基准）

| COS Key | 数据集 | 说明 |
|---------|--------|------|
| `thai-marketing-creative/thai-corpus/h6/th_arc_challenge/th_arc_challenge_test.parquet` | th-ARC | 科学推理（1222条） |
| `thai-marketing-creative/thai-corpus/h6/th_gsm8k/th_gsm8k_test.parquet` | th-GSM8K | 数学推理（1324条） |
| `thai-marketing-creative/thai-corpus/h6/th_hellaswag/th_hellaswag_validation.parquet` | th-HellaSwag | 常识推理（10052条） |
| `thai-marketing-creative/thai-corpus/h6/th_truthfulqa/th_truthfulqa_validation.parquet` | th-TruthfulQA | 真实性问答（817条） |
| `thai-marketing-creative/thai-corpus/h6/th_winogrande/th_winogrande_validation.parquet` | th-Winogrande | 指代消解（1272条） |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/marketing/` (3 files) | th-MMLU Marketing | 营销学知识 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/business_ethics/` (1 file) | th-MMLU Business Ethics | 商业伦理 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/public_relations/` (1 file) | th-MMLU PR | 公共关系 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/management/` (1 file) | th-MMLU Management | 管理学 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/high_school_macroeconomics/` (1 file) | th-MMLU Macro | 宏观经济学 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/high_school_microeconomics/` (1 file) | th-MMLU Micro | 微观经济学 |
| `thai-marketing-creative/thai-corpus/h6/th_mmlu/sociology/` (1 file) | th-MMLU Sociology | 社会学 |

### Assets（说明图片）

| COS Key | 说明 |
|---------|------|
| `thai-marketing-creative/thai-corpus/assets/ThaiCLI_annotation.jpg` | CLI标注流程图 |
| `thai-marketing-creative/thai-corpus/assets/ThaiCLI_factoid_culture.jpg` | Factoid示例图 |
| `thai-marketing-creative/thai-corpus/assets/ThaiCLI_instruction_religion.jpg` | Instruction示例图 |
| `thai-marketing-creative/thai-corpus/assets/ThaiH6_annotation.jpg` | H6标注流程图 |

### 文档

| COS Key | 说明 |
|---------|------|
| `thai-marketing-creative/thai-corpus/README.md` | 语料库完整说明文档 |

## 数据格式说明

### Parquet 文件

所有 `.parquet` 文件可用 pandas 读取：
```python
import pandas as pd
df = pd.read_parquet("CLI_factoid.parquet")
```

### CLI 数据字段

- **Factoid**: 包含 `question`, `chosen_answer`, `rejected_answer`, `theme` 等字段
- **Instruction**: 包含 `instruction`, `chosen_response`, `rejected_response`, `theme` 等字段
- `chosen` 代表文化敏感且包容的正确回答
- `rejected` 代表缺乏文化意识的不当回答

## 学术引用

```bibtex
@misc{kim2024representingunderrepresentedculturalcore,
      title={Representing the Under-Represented: Cultural and Core Capability Benchmarks for Developing Thai Large Language Models},
      author={Dahyun Kim and Sukyung Lee and Yungi Kim and Attapol Rutherford and Chanjun Park},
      year={2024},
      eprint={2410.04795},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2410.04795},
}
```
