// wendao_query.js
// 兼容：Windows / macOS / Linux (依赖 Node.js v18+)
// query 取值优先级：命令行第一个参数 > 环境变量 WENDAO_QUERY（勿使用占位符，须为用户的真实问话）
// token：仅 process.env.WENDAO_API_KEY（平台配置或用户在对话中提供后在本次命令中设置）
const TOKEN = (process.env.WENDAO_API_KEY || "").trim();
const USER_QUERY = (process.argv[2] || process.env.WENDAO_QUERY || "").trim();

async function callWendao(token, query) {
  if (!token || !query) {
    console.error(
      "错误：缺少 token 或 query。请设置环境变量 WENDAO_API_KEY（process.env.WENDAO_API_KEY），并以如下方式传入用户问话：\n" +
        '  node wendao_query.js "用户关于旅行的完整问题"\n' +
        "或：WENDAO_QUERY=\"...\" node wendao_query.js"
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
    const response = await fetch("https://externalcallback.ctrip.com/skills/api/crew/workbuddy/searchInfo", {
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
    console.error("请求失败:", error);
    process.exit(1);
  }
}

callWendao(TOKEN, USER_QUERY);