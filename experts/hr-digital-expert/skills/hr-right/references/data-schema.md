2026年4月29日# 权限业务数据结构说明

本文件包含 `SKILL.md` 中引用的所有数据结构定义，供 AI 在需要查看表结构或接口定义时参考。

---

## 权限业务明细数据结构说明

以下是 HR 权限系统中各表的 CREATE TABLE 语句，用于理解字段含义和表结构。

### ai_role_def — 角色信息表

```sql
CREATE TABLE `ai_role_def` (
  `id` int NOT NULL AUTO_INCREMENT,
  `domain_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '所属领域',
  `role_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色名称',
  `role_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色类型',
  `role_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色编码',
  `role_owner` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色负责人',
  `role_division_dim` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '角色分工维度',
  `member_source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色成员来源',
  `role_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色描述',
  `follow_default_auth` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否遵循数据默认授权原则',
  `approve_flow_setting` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审批流程设置',
  `approve_source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色负责人审批环节审批人来源',
  `approve_role_pkg_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '负责审批的角色/权限包名称',
  `approve_match_dim` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审批匹配维度',
  `approve_match_obj` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '审批匹配对象',
  `apply_qualification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请资格',
  `apply_rule_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请资格规则说明',
  `apply_rule_config_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请规则配置类型',
  `apply_rule_dim` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '申请规则维度',
  `apply_complex_rule_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请规则复杂规则名称',
  `apply_complex_rule` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '申请资格复杂规则',
  `member_gen_rule_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '成员生成规则类型',
  `member_rule_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '成员规则描述',
  `member_rule_dim_config` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '成员规则维度配置',
  `member_rule_config_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '成员规则配置名称',
  `temp_block_rule` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '临时屏蔽规则',
  `block_target` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '屏蔽对象 - del',
  `block_persons` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '屏蔽指定人员 - del',
  `block_person_scope` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '屏蔽名单 - 按人员',
  `block_division_scope` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '屏蔽名单-按分工维度',
  `creator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建人',
  `create_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建时间',
  `updater` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后操作人',
  `update_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后操作时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3423 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='角色信息';
```

**关键字段说明**：
- `role_division_dim`：角色分工维度，逗号分隔的维度名称列表，全部为必填
- `member_source`：角色成员来源（`规则生成` / `自主申请`）
---

### ai_role_rightpackage — 角色与权限包关系表

```sql
CREATE TABLE `ai_role_rightpackage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pkg_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包名称',
  `pkg_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包编码',
  `pkg_domain` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包所属领域',
  `role_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '关联的角色名称',
  `role_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色编码',
  `role_domain` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色所属领域',
  `pkg_ctrl_dim` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包所需控权维度',
  `role_division_dim` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色分工维度',
  `pkg_required_ctrl_dim` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包的必选控权维度',
  `pkg_optional_ctrl_dim` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包的可选控权维度',
  `pkg_follow_default_auth` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包是否遵循数据默认授权原则',
  `pkg_member_owner` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包成员负责人',
  `pkg_member_rule_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包成员规则ID',
  `role_follow_default_auth` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色是否遵循数据默认授权原则',
  `role_owner` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色负责人',
  `pkg_member_source` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包成员来源',
  `sub_rule_id` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '小规则ID',
  `rule_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则编码',
  `rule_member_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-成员规则描述',
  `rule_member_source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-成员规则来源',
  `rule_config` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '规则生成-规则配置',
  `rule_calc_scope` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-规则计算的范围',
  `rule_default_scope` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '规则生成-规则的默认范围',
  `rule_temp_block_flag` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-是否启用临时屏蔽规则-del',
  `rule_block_persons` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-屏蔽人员（整个人屏蔽）',
  `rule_block_scope_persons` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-屏蔽人员（按控权范围屏蔽）',
  `rule_block_scope` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '规则生成-屏蔽范围-del',
  `apply_qualification` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '自主申请-申请资格',
  `apply_rule_desc` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '自主申请-申请规则描述',
  `apply_rule_config` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '自主申请-申请规则配置',
  `apply_rule_config_detail` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '自主申请-规则配置明细',
  `has_pkg_default_scope` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否设置权限包默认范围',
  `has_perm_default_scope` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否设置权限项默认范围',
  `has_dim_apply_template` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '是否设置维度申请模板',
  `creator` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建人',
  `create_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '创建时间',
  `updater` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后操作人',
  `update_time` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '最后操作时间',
  `max_member_expiration` int DEFAULT NULL COMMENT '可申请最大有效期，对应枚举值：9999：不限制,12:一年,6：六个月,3：3个月,1：一个月',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30009 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='角色与权限包关系-基本信息';
```

**关键字段说明**：
- `pkg_member_source`：权限包成员来源（`规则生成` / `自主申请`）
- `pkg_required_ctrl_dim`：必选控权维度，逗号分隔
- `pkg_optional_ctrl_dim`：可选控权维度，逗号分隔
- `max_member_expiration`：可申请最大有效期（枚举值：9999=不限制，12=一年，6=六个月，3=三个月，1=一个月）

---

### ai_rightpackage_data_rule — 权限包绑定的数据规则

```sql
CREATE TABLE `ai_rightpackage_data_rule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pkg_name` varchar(50) NOT NULL COMMENT '权限包名称',
  `pkg_code` varchar(50) NOT NULL COMMENT '权限包编码',
  `pkg_domain` varchar(20) NOT NULL COMMENT '权限包所属领域',
  `rule_dir` varchar(100) NOT NULL COMMENT '规则目录',
  `rule_id` varchar(30) NOT NULL COMMENT '规则ID',
  `rule_cn_name` varchar(100) NOT NULL COMMENT '规则中文名',
  `rule_owner` varchar(50) NOT NULL COMMENT '规则属主',
  PRIMARY KEY (`id`),
  KEY `idx_pkg_code` (`pkg_code`),
  KEY `idx_rule_id` (`rule_id`),
  KEY `idx_pkg_domain` (`pkg_domain`)
) ENGINE=InnoDB AUTO_INCREMENT=640295 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='权限包绑定的数据规则';
```

---

### ai_rightpackage_sys_right — 权限包绑定的权限项

```sql
CREATE TABLE `ai_rightpackage_sys_right` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pkg_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包名称',
  `pkg_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包编码',
  `pkg_domain` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包所属领域',
  `sys_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '系统名称',
  `sys_code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '系统编码',
  `right_level` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项层级',
  `parent_right_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '父级权限项编码',
  `parent_right_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '父级权限项名称',
  `parent_right_path` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '父级权限项路径',
  `right_code` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项编码',
  `right_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项名称',
  `right_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项类型',
  `right_owner` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项负责人',
  `right_required_dim` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项必选控权维度',
  `right_optional_dim` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限项可选控权维度',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=552754 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='权限包绑定的权限项';
```

---

### ai_role_rightpackage_default_scope — 角色与权限包关系-权限包默认范围

```sql
CREATE TABLE `ai_role_rightpackage_default_scope` (
  `id` int NOT NULL AUTO_INCREMENT,
  `pkg_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包名称',
  `pkg_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包编码',
  `pkg_domain` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '权限包所属领域',
  `role_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '关联的角色名称',
  `role_code` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '角色编码',
  `ctrl_dim` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '控权维度',
  `default_scope` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci COMMENT '默认授权范围',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=287550 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='角色与权限包关系-权限包默认范围';
```

---

### v_ai_data_scope — 维度明细数据表

```sql
CREATE TABLE `v_ai_data_scope` (
  `dim_type_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '维度类型',
  `dim_type_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '维度类型名称',
  `dim_item_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '维度码值',
  `dim_item_parent_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '维度上一层级码值',
  `dim_item_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '维度名称',
  `dim_item_full_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL COMMENT '维度名称全路径'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='维度明细数据表';
```

**关键字段说明**：
- `dim_type_code` / `dim_type_name`：维度类型编码/名称（如 `Org` / `组织范围`）
- `dim_item_code` / `dim_item_name`：维度项编码/名称（如 `CSIG-xxx` / `xxx中心`）
- `dim_item_parent_code`：父级维度项编码，用于构建树形结构
- `dim_item_full_name`：维度项全路径（如 `腾讯/CSIG/xxx中心`）

---

## 权限业务MCP接口数据结构说明

以下是 `submit_apply_form` 接口使用的 Java DTO 类定义，用于组装 JSON 参数。

### RoleRightApplyFormDTO — 角色申请表单

```java
// 角色申请表单
@Data
public class RoleRightApplyFormDTO {
    List<RoleFormItemDTO> roleFormItemList;  // 申请的角色信息列表
    String applyReason;  // 申请原因
    Map<String, Boolean> confirmResultMap;  // 弱校验场景，提示用户是否确认操作，key:后端校验给出的提示信息，value:用户是否确认操作
}
```

---

### RoleFormItemDTO — 申请的角色信息

```java
// 申请的角色信息
@Data
public class RoleFormItemDTO {
    String roleCode;  // 角色编码
    String roleName;  // 角色名称
    List<DataScopeDimGroupDTO> roleDataScopes;  // 角色申请维度
    List<RightPackageItemDTO> rightPackageList;  // 角色关联的权限包列表
    Object checkData;  // 申请资格校验数据; 资格校验接口返回此字段
    Boolean isNewApply;  // 是否是新增申请
}
```

---

### RightPackageItemDTO — 申请的角色权限包信息

```java
// 申请的角色权限包信息
@Data
public class RightPackageItemDTO {
    String packageCode;  // 权限包编码
    String packageName;  // 权限包名称
    List<DataScopeDimGroupDTO> packageDataScopes;  // 权限包数据范围
    Integer maxExpire;  // 权限包最大有效期：对应枚举值：9999：不限制,12:一年,6：六个月,3：三个月,1：一个月
    Object checkData;  // 申请资格校验数据; 资格校验接口返回此字段
}
```

---

### DataScopeDimGroupDTO — 一组数据范围/分工维度

```java
// 一组数据范围|分工维度
@Data
public class DataScopeDimGroupDTO {
    List<DataScopeDimTypeItemDTO> dataScopeDimItems;  // 数据范围|分工维度明细（按维度类型分组）
    String memberFrom;  // 成员来源, rule:规则生产，apply:自主申请, 新申请均默认设置为apply
    String startDate;  // 开始日期
    String endDate;  // 结束日期，根据权限包有效期设置，最大值为maxExpire=9999则设置，9999-12-31 23:59:59，其它根据当前日期+权限包maxExpire(最大有效期)的值
    Integer rowId;  // 分工维度行ID，变更场景下，如果是新增一组数据范围|分工维度，则设置为null
    String operationType;  // 操作类型，新增：Add、修改:Update、删除:Delete
}
```

---

### DataScopeDimTypeItemDTO — 一组数据范围/分工维度

```java
// 一组数据范围|分工维度
@Data
public class DataScopeDimTypeItemDTO {
    String dimTypeCode;  // 维度类型|数据范围类型编码：如：Org,WorkPlace
    String dimTypeName;  // 维度类型名称|数据范围类型名称：如：组织,工作地
    List<DataScopeDimItemDTO> items;  // 该维度类型下的维度项列表
}
```

---

### DataScopeDimItemDTO — 数据范围/分工维度明细

```java
// 数据范围|分工维度明细
@Data
public class DataScopeDimItemDTO {
    String dimItemCode;  // 维度项编码：如：001,002,不能设置为空
    String dimItemName;  // 维度项名称：如：总部,北京
}
```

---

## 使用说明

1. **查看表结构**：当需要了解某个字段含义时，在本文件中搜索表名（如 `ai_role_def`）
2. **组装 JSON**：参考接口数据结构说明中的 DTO 定义，确保字段名和类型正确
3. **SQL 查询**：参考表结构中的字段名和注释，编写正确的 SQL 语句
4. **维度解析**：`v_ai_data_scope` 是维度码表，用于解析维度名称和码值
