"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.showModuleHelp = showModuleHelp;
/**
 * 显示模块帮助文档
 * @param helpData 帮助数据
 * @param moduleName 模块名称
 */
function showModuleHelp(helpData, moduleName) {
  const moduleHelpData = helpData.modulesHelp[moduleName];
  if (!moduleHelpData) {
    console.error(`模块 ${moduleName} 不存在`);
    process.exit(1);
  }
  let toolListMsg = ``;
  for (const [tool, info] of Object.entries(moduleHelpData)) {
    toolListMsg += `- ${info.filename}, ${info.summary}\n  `;
  }
  const helpMeg = `
模块${moduleName}帮助文档\n
可用工具：
  ${toolListMsg}
参数说明：
  <module> (必须) 模块名称 (例如: issues)，可直接配合 --help 查看该模块帮助
  <tool>   (必须) 工具/动作名称 (例如: list-issues)
  --path   (可选) 路径参数，JSON字符串
  --query  (可选) 查询参数，JSON字符串
  --data   (可选) 数据参数，JSON字符串
  --help   (可选) 显示此帮助文档

使用示例：
  ${"cnb"} issues --help
  ${"cnb"} issues list-issues --help
  ${"cnb"} issues list-issues --path '{"repo": "my-project"}' --query '{"page": 1, "pageSize": 10}'
`;
  console.log(helpMeg);
}