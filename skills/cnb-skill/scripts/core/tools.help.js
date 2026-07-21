"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.showToolHelp = showToolHelp;
var _util = _interopRequireDefault(require("util"));
var _schemaToJson = require("./schemaToJson");
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
/**
 * 显示工具帮助文档
 * @param helpData 帮助数据
 * @param moduleName 模块名称
 * @param tool 工具名称
 */
function showToolHelp(helpData, moduleName, tool) {
  const toolHelpData = helpData.modulesHelp[moduleName][tool];
  if (!toolHelpData) {
    console.error(`工具 ${tool} 不存在`);
    process.exit(1);
  }
  const {
    summary,
    description,
    help
  } = toolHelpData;
  const {
    parameter
  } = help;
  const {
    path,
    query,
    body
  } = parameter;

  // path参数说明
  let pathMsg = '';
  const pathParamsExample = {};
  if (path) {
    pathMsg = `--path参数详细说明：
${Object.keys(path).map(key => {
      if (path[key].required) {
        pathParamsExample[key] = `<${path[key].type}>`;
      }
      return `  - ${key} (${path[key].type}) - ${path[key].description}(${path[key].required ? '必填' : '选填'})`;
    }).join('\n')}
`;
  }

  // query参数说明
  let queryMsg = '';
  const queryParamsExample = {};
  if (query) {
    queryMsg = `--query详细参数：
${Object.keys(query).map(key => {
      if (query[key].required) {
        queryParamsExample[key] = `<${query[key].type}>`;
      } else if (query[key].default !== undefined) {
        queryParamsExample[key] = query[key].default;
      }
      return `  - ${key} (${query[key].type}) - ${query[key].description}(${query[key].required ? '必填' : '选填'})${query[key].enum ? `, [枚举: ${query[key].enum.join(', ')}]` : ''}`;
    }).join('\n')}
`;
  }

  // data参数说明
  let bodyMsg = '';
  let bodyParamsExample = {};
  if (body) {
    const {
      type,
      description,
      required,
      schema
    } = body;
    if (schema) {
      bodyParamsExample = (0, _schemaToJson.schemaToJson)(schema, {});
      bodyMsg = `--data参数详细说明：
${_util.default.inspect(schema, {
        showHidden: false,
        depth: null
      })}`;
    } else {
      bodyMsg = `--data参数详细说明：
  - ${type} - ${description}(${required ? '必填' : '选填'})
`;
    }
  }
  const exampleMsg = [`node ./skills/scripts/core ${moduleName} ${tool}`];
  if (Object.keys(pathParamsExample).length > 0) {
    exampleMsg.push(`--path '${JSON.stringify(pathParamsExample)}'`);
  }
  if (Object.keys(queryParamsExample).length > 0) {
    exampleMsg.push(`--query '${JSON.stringify(queryParamsExample)}'`);
  }
  if (Object.keys(bodyParamsExample).length > 0) {
    exampleMsg.push(`--data '${JSON.stringify(bodyParamsExample)}'`);
  }
  const helpMeg = `
工具${tool}帮助文档\n
工具说明：
  1. ${summary}
  2. ${description}
\n参数说明：
  <module> (必须) 模块名称 (例如: issues)，可直接配合 --help 查看该模块帮助
  <tool>   (必须) 工具/动作名称 (例如: list-issues)
  --path   (可选) 路径参数，JSON字符串
  --query  (可选) 查询参数，JSON字符串
  --data   (可选) 数据参数，JSON字符串
  --help   (可选) 显示此帮助文档
${pathMsg && `\n${pathMsg}`}${queryMsg && `\n${queryMsg}`}${bodyMsg && `\n${bodyMsg}`}
\n使用示例：
  ${exampleMsg.join(' ')}
`;
  console.log(helpMeg);
}