# testx-case-deacy-skill

智研测试堂「用例腐化治理」Skill，自动诊断并修复测试用例资产中的腐化问题。

## 功能概览

- 批量获取指定目录下的测试用例和目录结构（通过 `item_type` 区分 CASE/FOLDER）
- 构建目录-用例映射关系，维护目录与用例的归属
- 基于约束条件（iwiki/tapd/文本）进行腐化诊断
- 相似用例检测与自动合并
- **批量移动用例到目标目录（调整归属时优先使用）**
- 批量更新用例内容
- **批量删除用例/目录（非空检查 + 降级重命名 + 分批处理）**
- **批量重命名目录/用例（逐个 PATCH 请求）**
- 清理空目录（安全检查 + 优雅降级）
- **生成确认报告，用户审批后再执行实际操作**

## 核心价值

改进前 skill 在用户确认后有 3 类操作无法自动执行（重命名、安全删除目录、批量清理空目录）；改进后**全部 5 种操作均有脚本支持**，且对 API 限制做了优雅降级：

| 操作       | 改进前        | 改进后                       |
| ---------- | ------------- | ---------------------------- |
| 移动用例   | ✅ 脚本支持   | ✅ 脚本支持                  |
| 更新用例   | ✅ 脚本支持   | ✅ 脚本支持                  |
| 删除用例   | ✅ 脚本支持   | ✅ 脚本支持（增加分批+降级） |
| 重命名目录 | ❌ 需手动操作 | ✅ 新增 rename_cases.py      |
| 清理空目录 | ⚠️ 无安全检查 | ✅ 非空检查 + 降级重命名     |

## 智研 API 已知限制

以下为当前智研 API 的已知限制，脚本已做相应处理：

| #   | 限制描述                      | 影响场景             | 脚本处理方式                                                   |
| --- | ----------------------------- | -------------------- | -------------------------------------------------------------- |
| 1   | 无专门的目录重命名接口        | 需要重命名目录时     | `rename_cases.py` 通过 PatchCase 接口更新 Name 字段实现        |
| 2   | batch-delete 无法删除非空目录 | 清理空目录时目录非空 | `delete_cases.py --check-empty --fallback-rename` 降级为重命名 |
| 3   | 单次 batch-delete 有数量上限  | 大批量删除时         | `delete_cases.py` 自动按 BATCH_SIZE(50) 分批处理               |
| 4   | move/patch 接口仅支持逐个请求 | 批量移动/重命名时    | 脚本内置循环编排 + 0.2s 请求间隔避免限流                       |

## 目录结构

```
testx-case-deacy-skill/
├── SKILL.md                    # Skill 完整流程定义与数据模型参考
├── README.md                   # 本文件
└── scripts/
    ├── search_cases.py         # 批量获取用例（支持分页）
    ├── update_cases.py         # 批量更新用例（PatchCase）
    ├── move_cases.py           # 批量移动用例到指定目录（BatchMoveCases批量接口+分批）
    ├── delete_cases.py         # 批量删除用例/目录（非空检查+降级重命名+分批）
    └── rename_cases.py         # 批量重命名目录/用例（目录用UpdateFolder，用例用PatchCase）
```

## 快速开始

### 1. 获取 access_token

进入 [智研访问控制](https://zhiyan.woa.com/permission/#/access-token/private)，创建或复制个人 token。

### 2. 从用例目录链接解析参数

用例目录链接格式：

```
https://zhiyan.woa.com/testx/{namespace}/cases/#/testx/{namespace}/case/repos/{repo_uid}/vers/{repo_version_uid}/folders/{folder_uid}/in-page
```

从中提取 `namespace`、`repo_uid`、`repo_version_uid`、`folder_uid`。

### 3. 使用脚本

```shell
# 获取用例
python scripts/search_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --folder-uid <folder> --token <token> --output cases.json

# 移动用例到目标目录（调整归属时优先使用，先 dry-run）
python scripts/move_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --target-uid <target_folder> --token <token> --uids uid1,uid2 --dry-run

# 更新用例（先 dry-run）
python scripts/update_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input update_list.json --dry-run

# 删除用例/目录（先 dry-run）
python scripts/delete_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input delete_list.json --dry-run

# 删除空目录（带安全检查和降级重命名）
python scripts/delete_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input delete_folders.json \
  --check-empty --fallback-rename --dry-run

# 重命名目录/用例（先 dry-run）
python scripts/rename_cases.py \
  --namespace <ns> --repo-uid <repo> --repo-version-uid <ver> \
  --token <token> --input rename_list.json --dry-run
```

去掉 `--dry-run` 即正式执行。

## 脚本参数说明

### 公共参数

| 参数                 | 必填 | 说明                   |
| -------------------- | ---- | ---------------------- |
| `--namespace`        | 是   | 项目命名空间           |
| `--repo-uid`         | 是   | 用例库 UID             |
| `--repo-version-uid` | 是   | 用例库版本 UID         |
| `--token`            | 是   | 个人 access_token      |
| `--base-url`         | 否   | API 地址，默认测试环境 |
| `--dry-run`          | 否   | 仅预览，不执行         |

### search_cases.py 专有参数

| 参数           | 必填 | 说明                                    |
| -------------- | ---- | --------------------------------------- |
| `--folder-uid` | 是   | 目录 UID                                |
| `--item-type`  | 否   | 过滤类型: CASE/FOLDER/空（默认空=全部） |
| `--output`     | 否   | 输出文件路径                            |
| `--page-size`  | 否   | 每页数量，默认 100                      |

### move_cases.py 专有参数

| 参数           | 必填 | 说明                |
| -------------- | ---- | ------------------- |
| `--target-uid` | 是   | 目标目录 UID        |
| `--uids`       | 否   | 逗号分隔的 UID 列表 |
| `--input`      | 否   | 输入 JSON 文件路径  |

### delete_cases.py 专有参数

| 参数                | 必填 | 说明                                              |
| ------------------- | ---- | ------------------------------------------------- |
| `--uids`            | 否   | 逗号分隔的 UID 列表                               |
| `--input`           | 否   | 输入 JSON 文件路径                                |
| `--check-empty`     | 否   | 删除前检查目录是否为空                            |
| `--fallback-rename` | 否   | 删除失败时降级为重命名（添加 `[空-待删除]` 前缀） |

### rename_cases.py 专有参数

| 参数            | 必填 | 说明                                                       |
| --------------- | ---- | ---------------------------------------------------------- |
| `--uids`        | 否   | 逗号分隔的 UID 列表（配合 --name-prefix 使用）             |
| `--name-prefix` | 否   | 重命名前缀（在原名称前添加）                               |
| `--input`       | 否   | 输入 JSON 文件（包含 uid + new_name 字段，可选 is_folder） |
| `--is-folder`   | 否   | 使用 --uids 时指定为目录（默认，使用 UpdateFolder 接口）   |
| `--is-case`     | 否   | 使用 --uids 时指定为用例（使用 PatchCase 接口）            |

### update_cases.py 专有参数

| 参数      | 必填 | 说明               |
| --------- | ---- | ------------------ |
| `--input` | 否   | 输入 JSON 文件路径 |

## 执行顺序

用户确认调整方案后，按以下顺序执行：

```
移动用例 → 更新用例 → 删除用例 → 重命名目录 → 清理空目录
```

每步均支持 `--dry-run` 预览，确认无误后去掉该参数正式执行。

## 完整流程

详见 [SKILL.md](./SKILL.md)，包含：

- 目录-用例映射关系构建
- 腐化诊断维度与相似度计算
- 确认报告模板（含待重命名目录章节，需用户审批后才执行）
- 空目录清理策略（非空检查 + 降级重命名）
- Case 数据模型参考
