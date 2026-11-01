#!/usr/bin/env node
/**
 * yidea-http.js — 易点 MCP HTTP 直连通用调用工具
 *
 * 用法:
 *   node yidea-http.js <toolName> [argsJson]           # 直接传 JSON 字符串
 *   node yidea-http.js <toolName> --stdin              # 从 stdin 读取 JSON（推荐，避免 Shell 编码问题）
 *   node yidea-http.js <toolName> --file <path>        # 从文件读取 JSON
 *
 * 示例:
 *   # 直接传参
 *   node yidea-http.js get_yidea_func_list '{ "menuArray": "招采管理" }'
 *
 *   # stdin 模式（推荐，支持任意复杂嵌套 + 中文）
 *   @'{ "menuArray": "招采管理" }'@ | node yidea-http.js get_yidea_func_list --stdin
 *   ConvertTo-Json -Compress | node yidea-http.js get_yidea_func_list --stdin
 *
 *   # 文件模式
 *   node yidea-http.js get_yidea_func_list --file ./args.json
 *
 *   node yidea-http.js yidea_table_search '{ "request": { "formId": "xxx", "pageIndex": "1", "take": "10" } }'
 *   node yidea-http.js get_yidea_table_def '{ "tableId": "xxx" }'
 */

const fs = require("fs");
const path = require("path");

const SKILL_DIR = path.resolve(__dirname, "..");
const CONFIG_PATH = path.join(SKILL_DIR, "config", "config.json");

function extractErrorMessage(text, fallback) {
  if (!text || !text.trim()) {
    return fallback;
  }

  const trimmed = text.trim();
  try {
    const json = JSON.parse(trimmed);
    return json.message || json.error?.message || json.title || trimmed;
  } catch (_) {
    const match = trimmed.match(/data:\s*(\{.*\})\s*(?:\n|$)/);
    if (match) {
      try {
        const json = JSON.parse(match[1]);
        const textContent = json.result?.content?.find(c => c.type === "text");
        return json.error?.message || textContent?.text || trimmed;
      } catch (_) {
        return trimmed;
      }
    }

    return trimmed;
  }
}

async function yideaCall(toolName, args) {
  // 读取配置
  if (!fs.existsSync(CONFIG_PATH)) {
    throw new Error("未找到配置文件，请先执行登录 (yidea-provision.js)");
  }
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  const { YIDEA_API_BASE_URL, YIDEA_API_TOKEN } = config;

  const mcpUrl = `${YIDEA_API_BASE_URL}/mcp`;

  // 构造 MCP 请求
  const body = {
    jsonrpc: "2.0",
    id: 1,
    method: "tools/call",
    params: {
      name: toolName,
      arguments: args || {},
    },
  };

  const res = await fetch(mcpUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream",
      Authorization: `Bearer ${YIDEA_API_TOKEN}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    const message = extractErrorMessage(text, res.statusText);
    throw new Error(`HTTP ${res.status}: ${message}`);
  }

  // 解析 SSE 格式响应
  const text = await res.text();
  const match = text.match(/data:\s*(\{.*\})\s*\n/);
  if (!match) {
    throw new Error(`无法解析响应: ${text.slice(0, 200)}`);
  }

  const jsonRpcResult = JSON.parse(match[1]);

  // 提取工具返回的 text 内容
  if (jsonRpcResult.result && jsonRpcResult.result.content) {
    const textContent = jsonRpcResult.result.content.find(c => c.type === "text");
    if (textContent) {
      try {
        return JSON.parse(textContent.text);
      } catch (_) {
        if (jsonRpcResult.result.isError) {
          throw new Error(textContent.text);
        }

        return textContent.text;
      }
    }
  }

  if (jsonRpcResult.error) {
    throw new Error(jsonRpcResult.error.message || JSON.stringify(jsonRpcResult.error));
  }

  return jsonRpcResult;
}

// CLI 入口
if (require.main === module) {
  const argv = process.argv.slice(2);
  const toolName = argv[0];
  if (!toolName || toolName.startsWith('--')) {
    console.error("用法: node yidea-http.js <toolName> [argsJson|--stdin|--file <path>]");
    process.exit(1);
  }
  const rest = argv.slice(1);

  async function run() {
    let args = {};

    if (rest.includes('--stdin')) {
      // stdin 模式 — 从标准输入读取完整 JSON，无长度/编码限制
      const chunks = [];
      for await (const chunk of process.stdin) chunks.push(chunk);
      const buf = Buffer.concat(chunks);
      if (buf.length > 0) {
        try {
          args = JSON.parse(buf.toString('utf8').trim());
        } catch (e) {
          console.error(`stdin JSON 解析失败: ${e.message}`);
          process.exit(1);
        }
      }
    } else if (rest.includes('--file')) {
      // 文件模式 — 从文件读取 JSON
      const fileIdx = rest.indexOf('--file');
      const filePath = rest[fileIdx + 1];
      if (!filePath) {
        console.error('--file 需要指定文件路径');
        process.exit(1);
      }
      try {
        const content = fs.readFileSync(filePath, 'utf8');
        args = JSON.parse(content.trim());
      } catch (e) {
        console.error(`文件读取/解析失败: ${e.message}`);
        process.exit(1);
      }
    } else if (rest.length > 0) {
      // 传统模式 — 从命令行参数解析 JSON
      try {
        args = JSON.parse(rest[0]);
      } catch (e) {
        console.error(`参数 JSON 解析失败: ${e.message}`);
        process.exit(1);
      }
    }

    const data = await yideaCall(toolName, args);
    console.log("\n---YIDEA_RESULT_START---");
    console.log(JSON.stringify(data, null, 2));
    console.log("---YIDEA_RESULT_END---");
  }

  run().catch(e => {
    console.error(`\n❌ 调用失败: ${e.message}`);
    process.exit(1);
  });
}

module.exports = { yideaCall };
