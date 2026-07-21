# 腾讯安全产品命名规范 (TODO 待用户填)

> ⚠️ **本文件是 TODO 占位**, 需要你对照腾讯官方的产品命名文档 (https://doc.weixin.qq.com/sheet/e3_ATgAjQbNAKYCNw7VJug3XRtCeyHNx) 把正式产品名填进来。
> 当前的 `product code` (yujie / cwp 等) 是基于公开资料的**合理推断**, L0 parser 里的 `PRODUCT` 常量等你确认后改。

## 一、命名对照表 (草案, 待确认)

| 中文正式名 | 英文缩写 | 产品代号 (parser 用) | 旧名/营销名 | 所属大类 | 文档里的写法 (待你查) |
|---|---|---|---|---|---|
| **腾讯主机安全** | CWP (Cloud Workload Protection) | `cwp` | 云镜 / YunJing / 骑士版 | 主机安全 | TODO: 填入官方文档原文 |
| 腾讯容器安全服务 | TCSS | `tcss` | (无) | 容器安全 | TODO |
| **腾讯高级威胁检测 (御界)** | NDR / NTA | `yujie` (待确认) | 御界 / InTA | 流量检测 | TODO |
| 腾讯 Web 应用防火墙 | WAF | `waf` | 玄武 | 应用安全 | TODO |
| 腾讯云防火墙 | CFW | `cfw` | (无) | 网络安全 | TODO |
| 腾讯 SOC | SOC | `soc` | 安全运营中心 | 安全管理 | TODO |

## 二、待用户确认的 4 个关键问题

### Q1: 主机安全的产品代号

当前推断:
- 英文缩写: **CWP** (Cloud Workload Protection)
- parser 里的 PRODUCT 常量: `cwp`
- 旧称: 云镜 / YunJing

**需要确认**:
- (a) 官方文档里"主机安全"的英文名是 CWP 吗?
- (b) 还有没有"主机安全 Pro" / "CWP 增强版" 这类细分子产品? (决定是否要拆多个 parser)
- (c) 容器安全和主机安全是同一个 CWP 大类下, 还是独立产品 (TCSS)? (决定 parser 是否要分开)

### Q2: 御界的产品代号

当前推断:
- 中文正式名: 腾讯高级威胁检测 (御界)
- 英文缩写: 不确定, 可能是 NDR / NTA / InTA 之一
- parser 里的 PRODUCT 常量: `yujie` (我选了"御界"拼音)
- 数据中告警规则名带"INTA", 说明底层引擎是 InTA

**需要确认**:
- (a) 御界在文档里的英文缩写是 NDR / NTA / InTA 哪个?
- (b) "御界"是独立产品, 还是"腾讯 SOC"自带的检测模块?
- (c) parser 的 PRODUCT 常量用哪个? (我倾向 `yujie`, 但如果你想和英文缩写一致可以改)

### Q3: parser 拆分粒度

一个**待你拍板**的设计问题:

**方案 A (推荐)**: 按产品大类拆
- 1 个 `cwp_parser.py` 处理"主机安全"所有变体
- 1 个 `yujie_parser.py` 处理"高级威胁检测"所有变体
- 优点: parser 数量少, 维护简单
- 缺点: 同名 parser 处理不同变体, 内部要写 if-else

**方案 B**: 按具体产品拆
- `cwp_linux_parser.py` / `cwp_windows_parser.py` / `cwp_web_parser.py`
- `yujie_nta_parser.py` / `yujie_dns_parser.py` ...
- 优点: 职责单一
- 缺点: parser 数量爆炸, 数据量不大时过度设计

**我的建议**: 现阶段用方案 A, 但 parser 内部留好扩展点 (支持子类型 dispatch)。等数据量增长再做方案 B 的拆分。

### Q4: 产品代号的命名风格

parser 的 PRODUCT 常量用什么风格?
- (a) 中文拼音: `yujie`, `cwp` (我当前用的, 易读)
- (b) 官方英文缩写: `ndr`, `cwp` (更标准, 但御界缩写不明确)
- (c) 混合: 文档里有明确英文缩写的用英文, 没有的用拼音

## 三、修改指南

确认命名后, 需要改的地方:

1. **parser 里的 PRODUCT 常量**:
   ```python
   # scripts/parsers/cwp_parser.py
   class CwpParser(BaseParser):
       PRODUCT = "cwp"  # ← 改这里
   ```

2. **registry 里会自动生效** (因为 registry 是 `YujieParser.PRODUCT` 引用)

3. **统一 schema 的 vendor_product 字段** 也跟着改

4. **L1 skill 的命名**: 当前是 `cwp-analyzer` / `yujie-analyzer`, 如果产品代号变了, 目录名也要改 (但 skill 的 `name` 字段保持不变, 避免破坏引用)

## 四、其他产品的预留

L0 框架设计为**注册式**, 新增产品只需:
1. 在 `scripts/parsers/` 加 `xxx_parser.py`
2. 在 `parsers/registry.py` 注册
3. 在本文件补充命名对照

**未来可能要加的 parser** (按你可能的数据源):
- `waf_parser.py` - WAF 告警 (攻击载荷)
- `cfw_parser.py` - 云防火墙 (流量拦截)
- `tcss_parser.py` - 容器安全 (运行时事件)
- `soc_parser.py` - SOC 自带检测 (关联告警)

## 五、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-06 | 初版, TODO 标记 | 等用户填官方产品命名 |
