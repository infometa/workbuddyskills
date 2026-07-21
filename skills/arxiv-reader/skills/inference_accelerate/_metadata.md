# Inference Acceleration & Efficiency

本分类涵盖与 **模型推理性能优化、计算效率提升及部署技术** 相关的论文，包括但不限于：

* **模型压缩技术**：量化（PTQ/QAT）、权重/激活剪枝、稀疏化（Sparsity）、知识蒸馏（Distillation）。
* **推理算法优化**：投机采样（Speculative Decoding）、早停机制（Early Exit）、并行解码（Parallel Decoding）。
* **显存与带宽优化**：KV Cache 管理（如 PagedAttention）、长文本推理优化、模型并行（TP/PP）调度。
* **系统层与内核优化**：算子融合（Kernel Fusion）、FlashAttention 系列、低比特计算算子、定制化 CUDA Kernel。
* **硬件协同设计**：针对特定硬件（NVIDIA/AMD GPU、端侧 NPU/FPGA）的部署优化及硬件感知架构搜索（NAS）。
* **服务治理与调度**：连续批处理（Continuous Batching）、Prefill 与 Decode 分离、负载均衡。

**典型关键词**: inference, acceleration, latency, throughput, quantization, pruning, distillation, speculative decoding, KV cache, kernel fusion, PagedAttention, FlashAttention, efficiency, hardware-aware
