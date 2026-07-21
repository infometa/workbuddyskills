#!/usr/bin/env node
"use strict";

Object.defineProperty(exports, "__esModule", {
  value: true
});
exports.parseArguments = parseArguments;
var _fs = _interopRequireDefault(require("fs"));
var _path = _interopRequireDefault(require("path"));
var _modules = require("./modules.help");
var _tools = require("./tools.help");
var _util = _interopRequireDefault(require("util"));
function _interopRequireDefault(e) { return e && e.__esModule ? e : { default: e }; }
const helpFileContent = _fs.default.readFileSync(_path.default.join(__dirname, 'help.json'), 'utf8');
if (!helpFileContent) {
  console.error('help.json not found');
  process.exit(1);
}
const helpData = JSON.parse(helpFileContent);
/**
 * 解析命令行参数
 * @returns 解析后的参数对象
 */
// function parseArguments(): Record<string, string | boolean | undefined> {
//   const args = process.argv.slice(2);
//   const result: Record<string, string | boolean | undefined> = {};

//   for (let i = 0; i < args.length; i++) {
//     const arg = args[i];

//     // 检查是否是参数名（以--开头）
//     if (arg.startsWith('--')) {
//       const paramName = arg.slice(2);

//       // 检查下一个参数是否是值（不是以--开头）
//       if (i + 1 < args.length && !args[i + 1].startsWith('--')) {
//         result[paramName] = args[i + 1];
//         i++; // 跳过下一个参数（值）
//       } else {
//         result[paramName] = paramName === 'help' ? true : undefined;
//       }
//     }
//   }
//   return result;
// }

function parseArguments() {
  const args = process.argv.slice(2);
  const result = {};
  let positionalCount = 0;
  let i = 0;
  while (i < args.length) {
    const arg = args[i];
    if (arg.startsWith('--')) {
      // --- 处理命名参数 (Options) ---
      const fullKey = arg.slice(2);

      // 支持 key=value 格式 (e.g., --config=file.json)
      if (fullKey.includes('=')) {
        const [key, ...valueParts] = fullKey.split('=');
        result[key] = valueParts.join('=');
        i++;
        continue;
      }
      const key = fullKey;

      // 检查下一个参数是否是值
      const nextArg = args[i + 1];
      const isNextArgValue = i + 1 < args.length && !nextArg.startsWith('--') && !nextArg.startsWith('-'); // 也防止捕获短参数作为值

      if (isNextArgValue) {
        result[key] = nextArg;
        i += 2; // 跳过 key 和 value
      } else {
        // 没有值，视为布尔标志 (flag)
        // 特殊处理：如果用户显式想要 undefined 行为，可以在这里调整，但通常 CLI 中 flag 存在即为 true
        result[key] = true;
        i++;
      }
    } else if (arg.startsWith('-') && arg.length > 1 && !/^-?\d+$/.test(arg)) {
      // --- 处理短参数 (Short flags, e.g., -h, -v) ---
      // 注意：排除负数数字的情况
      const key = arg.slice(1);

      // 简单处理：短参数通常不带长值，或者支持 -f value
      const nextArg = args[i + 1];
      const isNextArgValue = i + 1 < args.length && !nextArg.startsWith('--') && !nextArg.startsWith('-');
      if (isNextArgValue && key.length === 1) {
        // 只有单字符短参才自动吞并下一个值 (如 -o output.txt)，多字符连写 (如 -abc) 通常视为多个布尔旗标
        result[key] = nextArg;
        i += 2;
      } else {
        result[key] = true;
        i++;
      }
    } else {
      // --- 处理位置参数 (Positional Args) ---
      if (positionalCount === 0) {
        result.module = arg;
      } else if (positionalCount === 1) {
        result.tool = arg;
      }
      positionalCount++;
      i++;
    }
  }
  return result;
}

/**
 * 验证必须参数是否存在
 * @param params 解析后的参数对象
 * @returns 验证结果
 */
function validateRequiredParams(params) {
  if (!params.tool || params.help) {
    return false;
  }
  return true;
}

/**
 * 尝试解析JSON字符串
 * @param str 要解析的字符串
 * @returns 解析后的对象或原始字符串
 */
function tryParseJSON(str) {
  if (typeof str !== 'string') return str;

  // 先将真实控制字符转义为 JSON 合法形式，处理 shell/AI 传入的原始换行等情况
  const escaped = str.replace(/[\x00-\x1F\x7F]/g, ch => {
    const map = {
      '\n': '\\n',
      '\r': '\\r',
      '\t': '\\t',
      '\b': '\\b',
      '\f': '\\f'
    };
    return map[ch] || '\\u' + ch.charCodeAt(0).toString(16).padStart(4, '0');
  });
  try {
    return JSON.parse(escaped);
  } catch (error) {
    return str;
  }
}

/**
 * 格式化参数对象
 * @param params 原始参数对象
 * @returns 格式化后的参数对象
 */
function formatParams(params) {
  const formatted = {};

  // 处理每个参数
  for (const [key, value] of Object.entries(params)) {
    if (typeof value === 'string') {
      formatted[key] = tryParseJSON(value);
    } else if (typeof value === 'boolean') {
      formatted[key] = value;
    }
  }

  // 当没有传递query时，要判断当前tool是否支持query
  if (!formatted.query) {
    const {
      module,
      tool
    } = formatted;
    const toolsHelp = helpData.modulesHelp[module][tool];
    const toolsParam = toolsHelp?.help?.parameter || {};
    if (toolsParam.query) {
      formatted.query = {};
    }
  }
  return formatted;
}

/**
 * 显示帮助文档
 * @param moduleName 模块名称，如果指定则显示模块帮助
 */
function showHelp(moduleName, tool) {
  if (moduleName && tool) {
    (0, _tools.showToolHelp)(helpData, moduleName, tool);
  } else if (moduleName) {
    (0, _modules.showModuleHelp)(helpData, moduleName);
  } else {
    let moduleListMsg = ``;
    for (const [module, count] of Object.entries(helpData.mainHelp)) {
      moduleListMsg += `- ${module}, tool数量(${count})\n  `;
    }
    const helpMeg = `
CNB OpenAPI CLI 工具\n
可用模块：
  ${moduleListMsg}
参数说明：
  <module> (必须) 模块名称 (例如: issues)，可直接配合 --help 查看该模块帮助
  <tool>   (必须) 工具/动作名称 (例如: list-issues)
  --path   (可选) 路径参数，JSON字符串
  --query  (可选) 查询参数，JSON字符串
  --data   (可选) 数据参数，JSON字符串
  --help   (可选) 显示此帮助文档

使用示例：
  ${"cnb"} --help
  ${"cnb"} issues --help
  ${"cnb"} issues list-issues --help
  ${"cnb"} issues list-issues --path '{"repo": "my-project"}' --query '{"page": 1, "pageSize": 10}'
`;
    console.log(helpMeg);
  }
}

/**
 * 主函数
 */
async function main() {
  // 解析命令行参数
  const params = parseArguments();

  // 验证必须参数（当没有请求帮助时）
  if (!validateRequiredParams(params)) {
    showHelp(params.module, params.tool);
    process.exit(0);
  }

  // 格式化参数
  const formattedParams = formatParams(params);

  // 动态引入模块
  const toolPath = _path.default.join(__dirname, '../modules', `${formattedParams.module}/${formattedParams.tool}.js`);
  if (!_fs.default.existsSync(toolPath)) {
    console.error(`工具文件不存在: ${toolPath}`);
    process.exit(1);
  }
  const toolModule = require(toolPath);
  const toolFunction = toolModule.default;
  if (!toolFunction) {
    console.error(`工具函数不存在`);
    process.exit(1);
  }
  const toolsParam = [];
  let pathAndQueryParams = null;
  if (formattedParams.path && Object.keys(formattedParams.path).length === 1 && !formattedParams.query) {
    pathAndQueryParams = formattedParams.path[Object.keys(formattedParams.path)[0]];
  } else {
    if (formattedParams.path) {
      pathAndQueryParams = {
        ...formattedParams.path
      };
    }
    if (formattedParams.query) {
      pathAndQueryParams = {
        ...pathAndQueryParams,
        ...formattedParams.query
      };
    }
  }
  if (pathAndQueryParams) {
    toolsParam.push(pathAndQueryParams);
  }
  if (formattedParams.data) {
    toolsParam.push(formattedParams.data);
  }
  const data = await toolFunction(...toolsParam);
  console.log(_util.default.inspect(data, {
    showHidden: false,
    depth: null
  }));
}
main();