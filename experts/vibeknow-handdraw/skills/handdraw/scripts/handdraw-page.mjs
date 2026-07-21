// handdraw-page.mjs — 对一张图做手绘绘制,并把结果写成「与该图同名同目录」的 .vec.json。
// 关键:输出文件名从**输入图片路径派生**(01.png → 01.vec.json),所以某张图的绘制数据
// 只会落到该图对应的文件 —— 从结构上杜绝「图片和矢量化数据错位」。LLM 不用记编号。
//
// 用法:
//   node handdraw-page.mjs <JOBDIR>/NN.png [--title <主题>]
//   → 生成 <JOBDIR>/NN.vec.json,并打印它的路径。未登录会报错(先用 login 工具)。
import { writeFileSync } from "node:fs";
import { dirname, join, basename, extname } from "node:path";
import { callHanddraw, hasDrawing } from "../../../mcp/server.mjs";

// 由图片路径派生出同名 .vec.json 路径(同目录、同 basename)。
export function vecPathFor(imagePath) {
  const ext = extname(imagePath);
  return join(dirname(imagePath), basename(imagePath, ext) + ".vec.json");
}

// 由图片路径派生【单页】计费元数据:page = 文件名前导数字(NN.png → n)。
// 逐页各扣各的:每页一次冻结→结算,积分明细一页一条(第 n 页)。
export function pageMetaFor(imagePath, extra = {}) {
  const m = basename(imagePath).match(/^(\d+)/);
  return {
    page: m ? parseInt(m[1], 10) : 0,
    title: extra.title || "",
    source: extra.source || "workbuddy",
  };
}

export async function handdrawPage(imagePath, meta = {}) {
  const data = await callHanddraw(imagePath, pageMetaFor(imagePath, meta)); // {coarse, full}
  // 兜底:即便上游没拦住,也绝不把空绘制数据写成 vec.json(会渲染出错且难排查)。批量路径同此防线。
  if (!hasDrawing(data)) {
    throw new Error(`handdraw 结果为空,拒绝写入 ${vecPathFor(imagePath)}(检查登录/额度/服务端日志)`);
  }
  const out = vecPathFor(imagePath);
  writeFileSync(out, JSON.stringify(data));
  return out;
}

// CLI
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const img = args.find((a) => !a.startsWith("--"));
  const ti = args.indexOf("--title");
  const title = ti >= 0 ? args[ti + 1] : undefined;
  if (!img) {
    console.error("Usage: node handdraw-page.mjs <图片路径> [--title <主题>]");
    process.exit(1);
  }
  handdrawPage(img, { title })
    .then((out) => process.stdout.write(out))
    .catch((e) => {
      // 积分不足:结构化输出到 stdout(供 agent 识别 → 引导充值/降级)+ 非0退出。绘制只有 vibeknow 一条路。
      if (e && e.insufficientCredits) { process.stdout.write(JSON.stringify({ error: "insufficient_credits", service: "handdraw" })); process.exit(2); }
      console.error(String((e && e.message) || e)); process.exit(1);
    });
}
