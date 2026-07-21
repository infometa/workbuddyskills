# 第七步：用户确认与执行

**必须等待用户确认后才能执行**。向用户展示第六步生成的 HTML 确认报告，等待用户回复「确认执行」后按以下顺序操作：

> **执行顺序**：先移动 → 再更新 → 删除用例 → 重命名目录 → 清理空目录

## 7.1 移动用例（优先执行）

```shell
# 先dry-run确认
python scripts/move_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --target-uid <target_folder> --token <token> \
  --uids uid1,uid2,uid3 --dry-run

# 确认无误后正式执行（去掉 --dry-run）
```

如果有多个目标目录，分批执行，每批指定不同的 `--target-uid`。

## 7.2 更新用例

```shell
python scripts/update_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input .testbuddy/case-decay/update_cases.json [--dry-run]
```

## 7.3 删除多余用例

> 仅当用例完全失效或已合并到其他用例时才执行删除。

```shell
python scripts/delete_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input .testbuddy/case-decay/delete_cases.json [--dry-run]
```

## 7.4 重命名目录

```shell
python scripts/rename_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input .testbuddy/case-decay/rename_folders.json [--dry-run]
```

## 7.5 清理空目录

> 空目录删除必须在用例移动/删除/重命名全部完成后再执行。

```shell
python scripts/delete_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input .testbuddy/case-decay/delete_folders.json \
  --check-empty --fallback-rename [--dry-run]
```

# 第八步：结果验证与执行报告

执行完成后，重新获取数据进行验证：

```shell
python scripts/search_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --folder-uid <folder> --token <token> \
  --output .testbuddy/case-decay/verified_cases.json
```

验证要点：

1. 确认移动后的用例已在目标目录下
2. 确认更新后的用例内容正确
3. 确认已删除用例不再存在
4. 确认空目录已被清理

输出最终执行报告（markdown 格式）：

```markdown
## 用例防腐执行报告

### 执行结果

| 操作       | 计划数 | 成功数 | 失败数 |
| ---------- | ------ | ------ | ------ |
| 移动用例   | M      | m      | m'     |
| 更新用例   | X      | x      | x'     |
| 删除用例   | Y      | y      | y'     |
| 重命名目录 | R      | r      | r'     |
| 清理空目录 | E      | e      | e'     |

### 当前目录结构

（调整后的目录-用例结构概览）

### 失败项（如有）

| 操作 | UID | 名称 | 失败原因 |
| ---- | --- | ---- | -------- |
```
