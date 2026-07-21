# 勒索病毒应急响应分析报告

## 1. 概述

| 项目 | 内容 |
|------|------|
| 报告时间 | {{timestamp}} |
| 受影响系统 | {{affected_systems}} |
| 加密文件扩展名 | {{extension}} |
| 勒索信文件名 | {{note_filename}} |

## 2. 家族识别结果

**识别家族**: {{family_name}}
**置信度**: {{confidence}}
**匹配维度**: {{matched_dimensions}}

### 匹配详情
{{match_details}}

### 家族简介
{{family_description}}

## 3. IOC 指标

{{ioc_table}}

## 4. 入侵路径分析

**最可能入口**: {{likely_entry_point}}

### 家族已知入侵向量
{{known_vectors}}

### 环境特征匹配
{{environment_matches}}

### 横向传播路径
{{lateral_movement}}

## 5. 数据恢复评估

**解密工具可用性**: {{recovery_status}}

{{recovery_details}}

### 数据恢复建议
{{recovery_recommendations}}

## 6. 在线情报（零 Key 查询）

> 本章节内容由 `online_query.py` 从 Ransomware.live、ransomwatch、mthcht/awesome-lists、NoMoreRansom 四个免费数据源实时获取，无需 API Key。

### 6.1 家族活跃度

| 指标 | 数值 |
|------|------|
| 近 7 天受害者数 | {{victims_7d}} |
| 近 30 天受害者数 | {{victims_30d}} |
| 数据源更新时间 | {{threat_updated_at}} |

### 6.2 近期受害者（示例）
{{recent_victims}}

### 6.3 Tor 站点 / 团伙元数据
{{tor_sites}}

### 6.4 扩展名反查结果（mthcht CSV）
{{extension_lookup}}

### 6.5 解密工具在线状态（NoMoreRansom）
{{online_decryptor_status}}

## 7. 应急响应建议

### 立即处置
1. **隔离受影响系统**：断开网络连接，防止横向传播
2. **保留证据**：不要关机，保留内存和磁盘镜像
3. **确定影响范围**：排查其他受影响系统

### 溯源调查
1. **检查入侵路径**：依据上述分析，排查对应日志
2. **时间线还原**：从初始入侵到加密发生的时间线
3. **数据泄露评估**：判断是否发生数据外传

### 恢复重建
1. **系统重建**：从可信镜像重建受影响系统
2. **补丁修复**：修复入侵路径涉及的漏洞
3. **加固防护**：针对入侵路径实施防护措施

### 建议联动分析
{{recommended_correlations}}

## 8. 附录

### 家族 IOC 完整列表
{{full_ioc_list}}

### 参考资料
- NoMoreRansom: https://www.nomoreransom.org/
- ID Ransomware: https://id-ransomware.malwarehunterteam.com/
- MITRE ATT&CK: https://attack.mitre.org/

---
*本报告由 ransomware-analysis Skill 自动生成，供应急响应参考。*
