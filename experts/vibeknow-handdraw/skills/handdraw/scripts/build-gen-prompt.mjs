// build-gen-prompt.mjs — 确定性拼出「出图 prompt」，把「锁画风尾巴」固化进代码,
// 不靠 LLM 记忆。等价于 figlens 的 buildHandDrawGenPrompt:
//   <style_prompt>，<画面描述>。<锁画风尾巴>
// 用法:
//   node build-gen-prompt.mjs --style "<style_prompt>" --visual "<画面描述>"
//   → 打印整串,直接喂给 ImageGen。
//
// 锁画风尾巴(verbatim 来自 figlens handdraw_gen.go 的 handDrawAntiPhotoTail):
// 把所选画风作用到人物面部/身体,避免生图模型按「照片先验」画出真人脸(剪纸身体配照片脸)。
// 刻意不含「文字」二字(生图无 negative prompt,提「文字」反诱发画字)。
export const HANDDRAW_ANTI_PHOTO_TAIL =
  "整幅画面是风格统一的手绘插画作品，包括人物的面部与身体在内的所有元素都以该手绘画风绘制，并非真人照片，没有写实人脸。";

// buildGenPrompt: style 与 visual 拼接,去掉 visual 结尾多余标点,再补句号 + 锁画风尾巴。
export function buildGenPrompt(style, visual) {
  const s = String(style || "").trim();
  const v = String(visual || "").trim().replace(/[。.，,、\s]+$/u, "");
  const head = s ? s + "，" + v : v;
  return head + "。" + HANDDRAW_ANTI_PHOTO_TAIL;
}

// CLI
if (process.argv[1] && import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const get = (flag) => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : undefined; };
  const style = get("--style");
  const visual = get("--visual");
  if (visual === undefined) {
    console.error('Usage: node build-gen-prompt.mjs --style "<style_prompt>" --visual "<画面描述>"');
    process.exit(1);
  }
  process.stdout.write(buildGenPrompt(style, visual));
}
