# 运行态角色与权限

用于管理业务人员的角色、角色成员，以及页面、菜单和数据集权限。

只在目标应用、角色、人员和资源都能唯一确认时执行写入。推荐顺序是：**先读取，再预览，最后确认写入**。

## 开始前

1. 使用明确的 `--appcode <code>`、`--app <name>` 或已经确认的当前应用。
2. 使用 `lovrabet role list` 获取真实角色 ID、`roleCode` 和类型。
3. 写操作先加 `--dry-run` 检查目标和变更内容。
4. 只有用户明确授权后才去掉 `--dry-run` 并加 `--yes`。

角色名称可能重复。命令接受角色名称时，如果不能唯一匹配，应改用角色 ID。

## 角色

### 查询角色

```bash
lovrabet role list --format compress
lovrabet role list --type CUSTOM --name 销售 --format compress
lovrabet role detail --id <roleId> --format compress
```

`role list` 返回内置角色和自定义角色，每个角色都包含稳定业务标识 `roleCode`。`builtin=true` 表示不能通过角色更新或删除命令修改。

### 创建和修改自定义角色

```bash
lovrabet role create --name <roleName> --role-code <roleCode> --remark <remark> --dry-run --format compress
lovrabet role create --name <roleName> --role-code <roleCode> --remark <remark> --yes --format compress

lovrabet role update --id <roleId> --role-code <newRoleCode> --dry-run --format compress
lovrabet role update --id <roleId> --name <newName> --dry-run --format compress
lovrabet role update --id <roleId> --remark <newRemark> --yes --format compress

lovrabet role delete --id <roleId> --dry-run --format compress
lovrabet role delete --id <roleId> --yes --format compress
```

- 只能创建、更新和删除 CUSTOM 角色。
- `--role-code` 最长 64 个字符且全局唯一；创建时省略则由服务端使用角色 ID，更新时可以单独修改。
- 备注只能设置为非空内容，不能用空字符串清除。
- 删除可能影响已有成员和权限；必须先确认角色确实不再使用。

## 角色成员

```bash
lovrabet role user-add --role <roleId|exactName> --user <userId> --expect-user-count <count> --dry-run --format compress
lovrabet role user-add --role <roleId|exactName> --user <userId> --expect-user-count <count> --yes --format compress

lovrabet role user-remove --role <roleId|exactName> --user <userId> --expect-user-count <count> --dry-run --format compress
lovrabet role user-remove --role <roleId|exactName> --user <userId> --expect-user-count <count> --yes --format compress
```

- `--user` 使用数字用户 ID；添加时该人员必须已经属于目标应用。
- `--expect-user-count` 用于防止读取后成员数量已变化，建议每次写入都提供。
- 重复添加已有成员或移出不存在的成员不会重复写入。
- OWNER 成员不能用这些命令调整。
- 如果人员身份不明确，停止写入并要求用户确认数字用户 ID。

## 页面权限

先读取页面权限：

```bash
lovrabet permit page-get --menu-id <menuId> --format compress
```

只设置明确指定的权限槽位，其他槽位保持不变：

```bash
lovrabet permit page-set --menu-id <menuId> --menu-roles <roleIdsOrNames> --dry-run --format compress
lovrabet permit page-set --menu-id <menuId> --row-roles SELF --yes --format compress
```

可用参数：

- `--menu-roles`
- `--create-roles`
- `--update-roles`
- `--delete-roles`
- `--detail-roles`
- `--export-roles`
- `--row-roles`

多个角色用英文逗号分隔。`SELF` 只用于 `--row-roles`。

## 菜单权限

查看一个角色的菜单访问结果：

```bash
lovrabet permit role-menus --role <roleId|exactName> --format compress
```

授权或撤权：

```bash
lovrabet permit role-menus-set --role <roleId|exactName> --grant --menus <menuIds> --dry-run --format compress
lovrabet permit role-menus-set --role <roleId|exactName> --revoke --menus <menuIds> --yes --format compress
```

`--grant` 与 `--revoke` 必须且只能选择一个。多个菜单 ID 用英文逗号分隔。

## 数据集权限

查看一个角色的数据集权限：

```bash
lovrabet permit dataset-get --role <roleId|exactName> --format compress
```

授权或撤权：

```bash
lovrabet permit dataset-set --role <roleId|exactName> --grant --datasets <datasetCodes> --actions <actions> --dry-run --format compress
lovrabet permit dataset-set --role <roleId|exactName> --revoke --datasets <datasetCodes> --actions <actions> --yes --format compress
```

动作值：

- `DATA_CREATE`
- `DATA_UPDATE`
- `DATA_DELETE`
- `DATA_DETAIL`
- `DATA_EXPORT`
- `DATA_ROW`

多个数据集或动作使用英文逗号分隔。

## 安全边界

- 只有 ADMIN 或 OWNER 可以执行页面、菜单和数据集权限写入。
- ADMIN 和 OWNER 拥有完整运行权限，不作为页面、菜单或数据集权限调整目标。
- 权限设置只修改显式选择的页面槽位、菜单或数据集动作。
- 菜单或数据集权限不能撤销最后一个角色；需要先为另一个角色授权，再执行撤权。
- dry-run 只预览请求，不代表已经获得授权，也不代表变更已经生效。
- 写入后重新执行对应读取命令，核对角色、成员或权限结果。
- 遇到权限不足、目标不存在、成员数量变化或候选不唯一时停止，不更换身份、不猜测目标。
