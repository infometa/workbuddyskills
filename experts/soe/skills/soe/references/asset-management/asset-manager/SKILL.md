---
name: asset-manager
version: 1.0.0
role: infrastructure
triggers:
  - 资产查询
  - 主机资产
  - IP归属
  - 资产纳管
  - 主机映射
description: |
  主机资产纳管 skill — 为其他安全分析 skill 提供统一的资产查询能力

  从 CSV (platform_cvm_list.csv / tenant_cvm_list.csv) 加载主机资产,
  构建 (IP, AppID) / (IP, VPCID) 联合索引, 供 L0 解析时关联告警 IP 到具体主机。

  适用场景:
  - 告警 IP → 主机名 / 业务系统 / 重要性 映射
  - 按 AppID / VPCID 列出所有主机
  - 其他 skill 通过 Python import 调用 AssetResolver API

  不适用:
  - 告警解析 → 用 soc-alert-pipeline
  - 威胁判定 → 用 cwp-analyzer / yujie-analyzer
---

# 主机资产纳管 (asset-manager)

## 一、定位

独立的**资产数据层 skill**, 不包含任何告警分析逻辑。

```
asset-manager (本 skill)
    ├── 加载 CSV → AssetResolver
    ├── 提供查询 API (IP/AppID/VPCID)
    └── 数据存储在 $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/
         ↑
    ┌────┴─────────────────┐
    │                      │
soc-alert-pipeline    cwp/yujie-analyzer
(L0 解析时调 API)     (消费 L0 输出的 asset 字段)
```

## 二、目录结构

```
asset-manager/
├── SKILL.md
├── scripts/
│   └── asset_resolver.py           # Asset + AssetResolver + load_default_assets + import_assets
└── references/                     # (预留)
```

> **数据存储**: 资产 CSV 存放在 `$CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/`，不随 skill 分发。

## 三、API

### 3.1 加载资产库

```python
import os, sys
from pathlib import Path

# 从 asset-manager skill 导入
manager_dir = Path(os.environ["CODEBUDDY_PLUGIN_ROOT"]) / "skills/soe/references/asset-management/asset-manager/scripts"
sys.path.insert(0, str(manager_dir))
from asset_resolver import load_default_assets

# 两级 fallback:
#   1. $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/  (用户数据, 最高优先级)
#   2. <project_root>/host-资产/                                (项目根自定义资产)
#   3. 都不存在 → 空库 (不报错)
resolver = load_default_assets(Path.cwd())
print(resolver.stats())
```

### 3.2 导入资产 CSV

```python
from asset_resolver import import_assets

# 将 CSV 导入到 $CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/
import_assets("/path/to/platform_cvm_list.csv", layer="platform")
import_assets("/path/to/tenant_cvm_list.csv", layer="tenant")
# 导入后下次 load_default_assets 自动加载
```

### 3.3 查询资产

```python
# 按 IP 查 (第一个匹配)
asset = resolver.lookup("10.0.0.4")

# 精确联合查询 (主机安全场景)
asset = resolver.lookup_by_ip_and_appid("10.0.0.4", "1251316161")

# 精确联合查询 (御界场景)
asset = resolver.lookup_by_ip_and_vpcid("172.16.114.119", 67334)

# 列出某租户所有主机
hosts = resolver.list_by_appid("1251316161")

# 列出某 VPC 所有主机
hosts = resolver.list_by_vpcid(67334)
```

### 3.4 按产品关联告警

```python
# 自动识别 (IP + AppID) 或 (IP + VPCID) 联合查询
result = resolver.enrich_event(parsed_dict, product="cwp")
# result = {"victim_asset": {...}, "src_asset": {...}, "match_method": "ip_appid", ...}
```

### 3.5 CLI 查询 (脚本内)

```python
# asset_resolver.py 末尾有 __main__ 可直接打印统计
python3 scripts/asset_resolver.py
```

## 四、资产更新

> **推荐方式**：用户只需提供资产文件（CSV/Excel/JSON/纯文本 IP 列表），由 AI 后台自动调用通用导入脚本 `scripts/import_assets_flexible.py` 完成识别和入库（三段降级：标准 CSV 列名优先 → 智能列名映射兜底），**无需用户执行任何命令**。

资产 CSV 存放在 `$CODEBUDDY_PLUGIN_DATA/soe-skill/asset-manager/assets/`，通过 `import_assets()` 函数导入（标准列名 CSV 直接使用，非标准格式请用上面的通用导入脚本）：

```python
from asset_resolver import import_assets

# 导入平台层资产
import_assets("/path/to/new_platform.csv", layer="platform")

# 导入租户层资产
import_assets("/path/to/new_tenant.csv", layer="tenant")
```

导入后下次 `load_default_assets()` 自动加载新数据。

如果项目根有 `host-资产/` 目录，也会作为 fallback 加载 (方便在不修改 PLUGIN_DATA 的情况下临时更新资产)。

## 五、字段约定

### platform_cvm_list.csv

| 列名 | 说明 |
|---|---|
| 主机ID | 平台统一 ID |
| 主机名 | hostname |
| IP地址 | 内网 IP |
| 宿主机内网IP | 物理机 IP |
| 可用区 | zone |
| 操作系统名称 | OS |
| CPU / 内存(GB) | 规格 |
| 创建者账号ID | owner |

### tenant_cvm_list.csv

| 列名 | 说明 |
|---|---|
| UUID | 整机 UUID |
| 实例ID | ins-xxx |
| 主机名 | hostname |
| 内网地址IP | 内网 IP (主查询键) |
| 公网IP地址 | 公网 IP |
| AppID | 租户 AppID |
| 网络 | 格式 "网络名(vpcid)", 如 "tsf-default(67334)" |
| 可用区 | zone |
| 镜像名称 | OS |
| 创建者账号ID | owner |
