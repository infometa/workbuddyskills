# 生成代码和测试用例的关联关系

从已有的会话信息中，提炼关键信息：

1. 测试设计的完整路径
2. 生成的代码文件路径、函数名或行号
3. 测试用例节点的UID
   并输出关联关系，最后执行脚本保存文件中。

## 保存关联关系脚本

优先使用 `--function` 指定函数名，如果没有函数名则使用 `--line` 指定行号，两者二选一：

```shell
# 方式一：文件路径 + 函数名（优先使用）
python <skills_dir>/scripts/record_code_case_relation.py \
--design-path <design_path> \
--file <file_path> \
--function <function_name> \
--case <node_uid>

# 方式二：文件路径 + 行号
python <skills_dir>/scripts/record_code_case_relation.py \
--design-path <design_path> \
--file <file_path> \
--line <line_number> \
--case <node_uid>
```

**参数说明：**

- `<design_path>`：测试设计的完整路径
- `<file_path>`：代码文件路径，**代码文件为从工作空间目录开始的内部的相对路径，例如完整路径为"<工作空间目录>/path/to/code"，则所需要的代码文件路径为"path/to/code"部分**
- `<function_name>`：函数名。**如果函数是类成员函数，则需要包含类名和函数名，格式如：`<ClassName>.<functionName>`**
- `<line_number>`：行号
- `<node_uid>`：用例节点 UID

**存储格式：**

```json
{
  "<case-uid>": {
    "file": "<path>",
    "function": "<function>",
    "line": "<line>"
  }
}
```

其中 `function` 和 `line` 二选一，未指定的字段不会写入。

如果有多个**代码路径-测试用例**关联关系，则需要多次调用脚本，为每个**代码路径-测试用例**对分别调用一次脚本。**请不要对一个代码路径-测试用例**关联关系调用多次脚本，否则会导致文件中保存的关联关系不正确。

## 注意事项

- <skills_dir>是脚本所在路径的前缀
- **脚本依赖当前工作目录，执行前不要 cd 切换目录**

## 执行步骤

首先，根据以下步骤进行**思考**：

1. 从对话中找到当前正在处理的测试设计，记录其design_uid
2. 找到给定工作空间目录下，测试设计的完整路径，格式为：`<工作空间目录>/.testbuddy/designs/<design_uid>`，design_uid为测试设计Uid，如：`design-Az7SsiL3Ui`，记录为*测试设计的完整路径*，即design_path
3. 从对话中找到当前正在处理的测试用例节点，记录为*测试用例节点的UID*，即node_uid
4. 从对话中找到生成的代码文件路径，代码文件为从工作空间目录开始的内部的相对路径，例如完整路径为"<工作空间目录>/path/to/code"，则所需要的代码文件路径为"path/to/code"部分。记录为 _file_
5. 从对话中找到对应的函数名或行号：
   - 优先记录函数名为 _function_。**如果函数是类成员函数，则需要包含类名和函数名，格式如：`<ClassName>.<functionName>`**
   - 如果没有函数名，则记录行号为 _line_
     **file 部分请按照 vscode.Uri 的格式进行输出，以适配 ssh、devcontainer 等远端开发场景**

接下来，根据以下步骤进行**输出**:

1. 按照以下格式输出所有**代码路径-测试用例**关联关系：
   **代码路径-测试用例关系如下表所示**
   | 文件路径 | 函数名/行号 | 测试用例节点uid |
   |----------|-------------|-----------------|
   | /path/to/code | function_name | node_uid1 |
   | /path/to/code | line | node_uid2 |
2. 根据上一步输出的关联关系表格，**逐行调用脚本**保存关联关系。
3. 保存所有关联关系后，分别输出保存成功的关联关系和保存失败的关联关系。
