# 历史全文草稿校验（不再用于正常交付）

当前专家流程已取消复制全文、写回复草稿和指纹检查。程序校验快照、资源引用与行程显式冲突后，生成精选 reply.md、完整 full-result.md、HTML 和 delivery-manifest.json。

按主 Agent 读取精选正文并展示 HTML 即可。回执缺字段只读完整 manifestFilePath；不要调用旧 check-delivery.js，也不要查找旧 deliveryCheck。旧脚本仅留作历史产物的手动诊断兼容，不是新流程步骤。
