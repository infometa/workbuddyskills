#!/usr/bin/env node
const fs = require("fs");
const path = require("path");

async function provision(userName, password) {
  const SKILL_DIR = path.resolve(__dirname, "..");
  const CONFIG_PATH = path.join(SKILL_DIR, "config", "config.json");
  const HELPER_PATH = path.join(__dirname, "yidea-http.js");

  // 1. 读取 API 地址
  let API_BASE;
  try { API_BASE = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8")).YIDEA_API_BASE_URL; } catch {}
  if (!API_BASE) API_BASE = process.env.YIDEA_API_BASE_URL;
  if (!API_BASE) throw new Error("未找到 YIDEA_API_BASE_URL 配置");

  // 2. 登录
  console.log(`[1/3] 登录: ${userName}...`);
  const loginRes = await fetch(`${API_BASE}/api/v1.2/Credential/YideaLogin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userName, password }),
  });
  if (!loginRes.ok) throw new Error(`HTTP ${loginRes.status}`);
  const loginData = await loginRes.json();
  if (!loginData.success) throw new Error(`登录失败: ${loginData.message || "未知错误"}`);
  const token = loginData.accessToken;
  console.log("✅ 登录成功");

  // 3. 写入配置文件
  console.log(`[2/3] 写入配置: ${CONFIG_PATH}`);
  const configDir = path.dirname(CONFIG_PATH);
  if (!fs.existsSync(configDir)) fs.mkdirSync(configDir, { recursive: true });
  const configData = { YIDEA_API_TOKEN: token, YIDEA_API_BASE_URL: API_BASE };
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(configData, null, 2), "utf8");

  // 4. 验证 HTTP 直连
  console.log("[3/3] 验证 HTTP 直连...");
  const mcpUrl = `${API_BASE}/mcp`;
  try {
    const pingRes = await fetch(mcpUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ method: "tools/list", jsonrpc: "2.0", id: 1 }),
    });
    if (pingRes.ok) {
      console.log("✅ HTTP 直连验证通过");
    } else {
      console.warn("⚠️ HTTP 直连响应非 200，但继续");
    }
  } catch (e) {
    console.warn(`⚠️ HTTP 直连验证失败: ${e.message}，但 Token 已保存`);
  }

  // 5. 获取工具列表（通过 HTTP 直连）
  console.log("[optional] 获取工具列表...");
  let tools = [];
  try {
    const toolsRes = await fetch(mcpUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json, text/event-stream",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ method: "tools/list", jsonrpc: "2.0", id: 1 }),
    });
    if (toolsRes.ok) {
      const text = await toolsRes.text();
      const m = text.match(/data:\s*(\{.*?\})\s*\n/s);
      if (m) tools = JSON.parse(m[1]).result?.tools || [];
      console.log(`  共 ${tools.length} 个工具`);
    }
  } catch {}

  return {
    status: "success",
    details: {
      token_last4: token.slice(-4),
      config_path: CONFIG_PATH,
      mcp_service: "yidea-http",
      tools,
    },
  };
}

// 命令行入口
const [u, p] = process.argv.slice(2);
if (!u || !p) { console.error("用法: node yidea-provision.js <userName> <password>"); process.exit(1); }

provision(u, p)
  .then(r => { console.log("\n---TASK_RESULT_START---\n" + JSON.stringify(r) + "\n---TASK_RESULT_END---"); })
  .catch(e => { console.error("\n❌ " + e.message); process.exit(1); });
