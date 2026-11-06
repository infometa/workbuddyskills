---
name: "scm-material-bom-explorer"
description: "用户查物料档案、物料库存、BOM 结构或资料包核价清单时触发"
version: "1.0.1"
author: "领猫科技"
display_name: "物料与 BOM 查询"
display_name_en: "Material & BOM Explorer"
description_zh: "物料档案与库存、标准与生产资料包 BOM、核价清单查询。"
description_en: "Look up material archives and inventory, standard and production package BOM, and pricing lists."
---

# 物料与 BOM 查询

## 什么时候用

用户问某个物料的档案信息、当前库存、被哪些款用到，或要看一个款的 BOM / 核价清单。

## 会用到的工具

| 工具 | 用途 |
|---|---|
| `op_other_material_list_material_archive` | 物料档案列表【读】 |
| `op_other_material_detail_material_archive` | 物料档案明细【读】 |
| `op_get_material_warehouse_inventory_paged` | 物料库存分页查询【读】 |
| `op_information_package_get_standard_package_bom_data` | 标准资料包 BOM（物料清单）【读】 |
| `op_information_package_get_production_package_bom_data` | 生产资料包 BOM【读】 |
| `op_information_package_get_info_package_nuclear_price_list_data` | 核价清单【读】 |
| `op_purchase_order_get_share_bom_url` | 获取可分享的 BOM 链接【读】 |

## 调用流程

1. 先按物料编码 / 名称在档案里定位，拿到编码后再查库存或 BOM。
2. BOM 分**标准资料包**和**生产资料包**两套，取数接口不同：用户没说清时先问是哪一套，
   不要默认取其中一套当作「BOM」——两者内容会不一致。
3. 输出物料卡：基本信息 + 库存 + 关联款式 / BOM 层级。

## 业务口径从哪来

- 标准资料包与生产资料包的区别、各自什么时候生成；
- 物料库存里各个数量字段的口径（在途、可用、锁定分别怎么算）；
- 核价清单的价格是哪一层的价（款式 / SKC / SKU 三层不互相下带，问错层会拿到空值）。

这些按总纲（`lingmao-scm-cloud/SKILL.md`）的规则调 `ask_knowledge`，不要凭字段名推断。

## 边界

- 全部只读，不涉及写操作。
- 物料库存工具只覆盖**物料**；成品库存开放平台当前没有对应查询接口，
  用户问成品库存时据实说明，不要拿物料库存冒充。
