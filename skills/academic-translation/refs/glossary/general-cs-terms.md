# 通用 CS 术语库

> 应用范围：所有领域均加载。在用户未指定具体会议时作为唯一术语库使用。

## 数据结构与算法

| 英文 | 中文（首选） | 中文（备选） | 说明 |
|---|---|---|---|
| algorithm | 算法 | — | |
| array | 数组 | — | |
| linked list | 链表 | — | |
| stack | 栈 | — | |
| queue | 队列 | — | |
| tree | 树 | — | |
| binary tree | 二叉树 | — | |
| graph | 图 | — | |
| hash table | 哈希表 | 散列表 | 优先"哈希表" |
| heap | 堆 | — | |
| time complexity | 时间复杂度 | — | |
| space complexity | 空间复杂度 | — | |

## 系统 / 工程

| 英文 | 中文（首选） | 中文（备选） | 说明 |
|---|---|---|---|
| latency | 延迟 | 时延 | |
| throughput | 吞吐量 | 吞吐率 | |
| benchmark | 基准 | 基准测试 | 作为名词时 |
| pipeline | 流水线 | 管道 | 系统语境用"流水线"；数据语境可"管道" |
| scalability | 可扩展性 | 伸缩性 | |
| availability | 可用性 | — | |
| reliability | 可靠性 | — | |
| consistency | 一致性 | — | |
| fault tolerance | 容错性 | 容错 | |
| concurrency | 并发 | — | |
| parallelism | 并行 | — | |

## 机器学习通用

| 英文 | 中文（首选） | 中文（备选） | 说明 |
|---|---|---|---|
| model | 模型 | — | |
| training | 训练 | — | |
| inference | 推理 | — | |
| dataset | 数据集 | — | 不译为"数据组" |
| sample / instance | 样本 / 实例 | — | |
| feature | 特征 | — | |
| label | 标签 | — | |
| loss | 损失 | 损失函数 | |
| objective | 目标 | 目标函数 | |
| gradient | 梯度 | — | |
| optimization | 优化 | — | |
| hyperparameter | 超参数 | — | 不译为"超级参数" |
| overfitting | 过拟合 | — | |
| underfitting | 欠拟合 | — | |
| regularization | 正则化 | — | |
| evaluation | 评估 | — | |
| metric | 指标 | 度量 | |
| accuracy | 准确率 | 准确度 | 0-1 区间用"准确率" |
| precision | 精确率 | 精度 | 信息检索 / 分类用"精确率" |
| recall | 召回率 | — | |
| F1 score | F1 分数 | F1 值 | 不译，保留 F1 |
| baseline | 基线 | 基线方法 | |

## 模型架构

| 英文 | 中文（首选） | 中文（备选） | 说明 |
|---|---|---|---|
| neural network | 神经网络 | — | |
| deep learning | 深度学习 | — | |
| layer | 层 | — | |
| neuron | 神经元 | — | |
| activation | 激活 | 激活函数 | 上下文 |
| weight | 权重 | — | |
| bias | 偏置 | — | |
| embedding | 嵌入 | 嵌入向量 / 嵌入表示 | 全文统一选"嵌入" |
| representation | 表示 | 表征 | 优先"表示" |
| feature map | 特征图 | 特征映射 | |
| backbone | 骨干网络 | 主干网络 | |
| head | 头 | 分支 | 上下文 |
| encoder | 编码器 | — | |
| decoder | 解码器 | — | |
| attention | 注意力 | — | |
| self-attention | 自注意力 | — | |
| cross-attention | 交叉注意力 | — | |

## 模型类型（**保留英文**）

下列**不翻译**，全文保留英文：

- BERT, GPT, T5, LLaMA, Qwen, ChatGLM
- Transformer, RNN, LSTM, GRU, CNN
- ResNet, VGG, EfficientNet, ViT, Swin Transformer
- Adam, SGD, AdamW, RMSprop
- ReLU, GELU, Swish, Softmax

## 数据集 / Benchmark（**保留英文**）

- ImageNet, CIFAR-10, CIFAR-100, COCO
- GLUE, SuperGLUE, MMLU, BIG-bench
- MS-MARCO, TREC, BEIR
- SQuAD, RACE, ARC
- WikiText, C4, Pile

## 训练相关

| 英文 | 中文（首选） | 中文（备选） | 说明 |
|---|---|---|---|
| epoch | 轮次 | 周期 | |
| batch | 批 / 批次 | — | |
| mini-batch | 小批 | mini-batch | 常保留英文 |
| learning rate | 学习率 | — | |
| weight decay | 权重衰减 | — | |
| dropout | dropout | — | 一般保留英文 |
| batch normalization | 批归一化 | BN | |
| layer normalization | 层归一化 | LN | |
| fine-tuning | 微调 | — | |
| pre-training | 预训练 | — | |
| zero-shot | 零样本 | zero-shot | 视风格 |
| few-shot | 少样本 | few-shot | 视风格 |
| in-context learning | 上下文学习 | 情境学习 | 优先"上下文学习" |
| prompt | 提示 | 提示词 | 视语境 |
| prompting | 提示 | 提示工程 | |
| chain-of-thought | 思维链 | CoT | |

## 评估范式

| 英文 | 中文（首选） | 备注 |
|---|---|---|
| ablation study | 消融实验 | 不译"切除研究" |
| state-of-the-art | 最先进 / SOTA | 上下文，正式文写"最先进"，缩写用 SOTA |
| out-of-distribution (OOD) | 分布外 | OOD 缩写常保留 |
| in-distribution | 分布内 | |
| generalization | 泛化 | 不译"一般化" |

## 输入输出

| 英文 | 中文（首选） | 备注 |
|---|---|---|
| input | 输入 | |
| output | 输出 | |
| prediction | 预测 | |
| target | 目标 | |
| ground truth | 真值 | 真实标签 |
| query | 查询 | |
| key | 键 | （注意力机制语境） |
| value | 值 | （注意力机制语境） |

## 写作 / 论文相关

| 英文 | 中文（首选） |
|---|---|
| ablation | 消融 |
| baseline | 基线 |
| benchmark | 基准 |
| empirical | 经验性 |
| extensive experiments | 大量实验 |
| qualitative | 定性 |
| quantitative | 定量 |
| state-of-the-art | 最先进 |
| trade-off | 权衡 |
| visualization | 可视化 |

## 不要翻译的 LaTeX 命令名

`\cite, \ref, \eqref, \autoref, \label, \begin, \end, \textbf, \emph, \underline, \mathbf, \mathit, \mathcal, \mathbb, \mathrm`
