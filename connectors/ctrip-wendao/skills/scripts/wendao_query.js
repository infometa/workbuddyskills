// wendao_query.js
// 携程问道 API 查询脚本
// 兼容：Windows / macOS / Linux (依赖 Node.js v18+)
// query 取值优先级：命令行第一个参数 > 环境变量 WENDAO_QUERY
// token：process.env.WENDAO_API_KEY（由连接器通过 envOverrides 注入）

const TOKEN = (process.env.WENDAO_API_KEY || "").trim();
const USER_QUERY = (process.argv[2] || process.env.WENDAO_QUERY || "").trim();

async function callWendao(token, query) {
  if (!token) {
    console.error(
      "错误：缺少 WENDAO_API_KEY。请在 WorkBuddy 连接器设置中配置携程问道 Token。"
    );
    process.exit(1);
  }
  if (!query) {
    console.error(
      '错误：缺少查询内容。请传入用户的旅行问题作为参数：\n' +
        '  node wendao_query.js "用户关于旅行的完整问题"\n' +
        '或：WENDAO_QUERY="..." node wendao_query.js'
    );
    process.exit(1);
  }

  const payload = {
    inputs: {
      token: token,
      query: query
    }
  };

  try {
    const response = await fetch("https://externalcallback.ctrip.com/skills/api/crew/qclaw/searchInfo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    // 解析响应：提取 result 字段
    let result = data.result || data;
    let content = result;

    if (typeof result === 'object' && result !== null) {
      content = result.content || JSON.stringify(result);
    }

    console.log(content);
  } catch (error) {
    console.error("请求失败:", error.message || error);
    process.exit(1);
  }
}

callWendao(TOKEN, USER_QUERY);
