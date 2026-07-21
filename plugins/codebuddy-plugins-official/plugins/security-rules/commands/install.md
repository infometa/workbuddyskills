---
description: 安装安全产品三部的安全规则包
allowed-tools: Bash,AskUserQuestion
---

即将为您安装安全产品三部-安全 rules

注意事项：
- 规则文件从插件本地目录复制，无需网络连接
- 环境变量 `${THIS_PLUGIN_DIR}` 指向 **当前插件目录**

`rules` 是后缀名为 `.mdc` 的文件，优先从插件的 `rules` 目录寻找，如果找不到，按照以下方式寻找：

环境信息： 
- `${THIS_PLUGIN_DIR}` 当前插件目录：`~/.codebuddy/plugins/marketplaces/codebuddy-plugins-official/plugins/security-rules`

**重要（important）** 
1. 请不要展示任何寻找 rules 目录的过程，一切都在后台运行
2. 请不要展示任何分析安全 rules mdc 文件的过程，一切都在后台运行

执行以下步骤：

1. 检查目标目录 `.codebuddy/rules/` 是否已存在规则文件：
   - 使用 Bash 工具执行：`ls .codebuddy/rules/*.mdc 2>/dev/null`
   
2. 如果存在 .mdc 文件：
   - 使用 AskUserQuestion 工具询问用户："检测到 .codebuddy/rules/ 目录已存在规则文件，是否覆盖安装？"
   - 提供选项："是，覆盖安装" 和 "否，取消安装"
   - 如果用户选择"否"，停止安装并提示"已取消安装"

3. 创建目标目录并复制规则文件：
   - 使用 Bash 工具执行：`mkdir -p .codebuddy/rules && cp "${THIS_PLUGIN_DIR}/rules/"*.mdc .codebuddy/rules/`

4. 验证并显示安装结果：
   - 使用 Bash 工具执行：`ls -lh .codebuddy/rules/*.mdc`
   - 显示安装成功信息，包括已安装的规则文件列表
