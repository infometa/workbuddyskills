// 一站式生成"鹅厂辟谣助手"分享卡片（1080×1080 方图）
// 布局：主体区（标题+结论）垂直居中，footer 固定底部
// 用法:
//   node gen-share-card.js --title "标题" --verdict "fake|true|partial|unverified" --summary "结论摘要" --out card.png
const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROME_PATHS = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
];

const LOGO_PATH = path.join(__dirname, 'assets', 'xiaop-logo-200.png');

function parseArgs() {
  const args = {};
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) {
      const key = argv[i].slice(2);
      args[key] = argv[i + 1];
      i++;
    }
  }
  return args;
}

const VERDICT_MAP = {
  fake:       { color: '#e74c3c', icon: '✗', text: '谣言' },
  true:       { color: '#27ae60', icon: '✓', text: '属实' },
  partial:    { color: '#f39c12', icon: '⚠', text: '部分失实' },
  unverified: { color: '#7f8c8d', icon: '?', text: '待核实' },
};

function buildHTML({ title, verdict, verdictText, summary, logoDataURL }) {
  const v = VERDICT_MAP[verdict] || VERDICT_MAP.unverified;
  const label = verdictText || v.text;
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  *{margin:0;padding:0;box-sizing:border-box;-webkit-font-smoothing:antialiased;}
  html,body{width:1080px;height:1080px;}
  body{
    font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei","Segoe UI Emoji","Apple Color Emoji",sans-serif;
    background:#f0f2f5;
  }
  .card{
    position:relative;
    width:1080px;height:1080px;background:#fff;
    display:flex;flex-direction:column;
  }
  /* 标题区：整图顶部1/4（270px），浅蓝淡透明背景，标题左对齐垂直居中 */
  .title-band{
    height:270px;                 /* 1080 / 4 */
    background:rgba(178,220,252,0.35);  /* 浅蓝高透明 */
    padding:0 88px;
    display:flex;align-items:center;
    position:relative;
  }
  /* 左侧竖线强化"标题感" */
  .title-band::before{
    content:"";
    position:absolute;
    left:44px;top:50%;transform:translateY(-50%);
    width:8px;height:96px;
    background:#0A2540;
    border-radius:4px;
  }
  .title{
    font-weight:900;color:#0A2540;
    letter-spacing:2px;
    overflow:hidden;
    text-align:left;
    width:100%;
    padding-left:24px;
    line-height:1.25;
    /* 字号由JS动态写入 */
  }
  /* 答案区 */
  .answer{
    flex:1;display:flex;flex-direction:column;justify-content:center;
    padding:56px 88px 0 88px;
  }
  .body{
    font-size:48px;line-height:1.85;color:#2c2c2c;
    letter-spacing:1.5px;
    text-align:justify;
  }
  .verdict{
    font-size:58px;font-weight:900;margin-right:8px;
    color:${v.color};
    letter-spacing:1px;
    white-space:nowrap;
  }
  /* 底部固定 */
  .footer-wrap{
    padding:0 88px 56px 88px;
  }
  .divider{height:1px;background:#ececec;margin:0 0 28px 0;}
  .footer{display:flex;align-items:center;gap:24px;}
  .logo{width:80px;height:80px;border-radius:50%;object-fit:cover;flex-shrink:0;}
  .footer-title{font-size:30px;font-weight:700;color:#1a1a1a;margin-bottom:6px;letter-spacing:0.5px;}
  .footer-sub{font-size:22px;color:#999;letter-spacing:0.5px;}
</style>
</head>
<body>
  <div class="card">
    <div class="title-band">
      <div class="title" id="title">${escapeHTML(title)}</div>
    </div>
    <div class="answer">
      <div class="body">
        <span class="verdict">【${v.icon} ${escapeHTML(label)}】</span>${escapeHTML(summary)}
      </div>
    </div>
    <div class="footer-wrap">
      <div class="divider"></div>
      <div class="footer">
        <img class="logo" src="${logoDataURL}" alt="logo">
        <div>
          <div class="footer-title">鹅厂辟谣助手 Skill</div>
          <div class="footer-sub">腾讯相关信息，来这里查真假</div>
        </div>
      </div>
    </div>
  </div>
  <script>
    // 自适应标题字号：保大策略
    // 优先策略——单行能塞下就大字单行；放不下时允许两行（line-height 1.25）
    // 关键约束：标题区高度 270px，padding 上下 0，需保证字号*行数*1.25 <= 240
    (function(){
      const el = document.getElementById('title');
      const maxWidth = 880;       // 1080 - 88*2 - 24
      const maxHeight = 240;      // 在270px标题带内留一点呼吸
      const MAX_FONT = 128;
      const MIN_FONT = 64;        // 字号下限：保证视觉冲击力

      // 第一阶段：尝试单行，从128到72px递减
      el.style.whiteSpace = 'nowrap';
      let size = MAX_FONT;
      el.style.fontSize = size + 'px';
      while (el.scrollWidth > maxWidth && size > 72) {
        size -= 2;
        el.style.fontSize = size + 'px';
      }
      // 如果单行能放下（72px及以上），就用单行
      if (el.scrollWidth <= maxWidth) {
        document.body.dataset.ready = '1';
        return;
      }

      // 第二阶段：单行放不下，允许换行，目标字号尽量大
      el.style.whiteSpace = 'normal';
      el.style.wordBreak = 'break-word';
      size = MAX_FONT;
      el.style.fontSize = size + 'px';
      // 同时控制宽度溢出（不会有，但保险）和高度溢出（两行总高）
      while ((el.scrollHeight > maxHeight || el.scrollWidth > maxWidth) && size > MIN_FONT) {
        size -= 2;
        el.style.fontSize = size + 'px';
      }
      document.body.dataset.ready = '1';
    })();
  </script>
</body>
</html>`;
}

function escapeHTML(s) {
  return String(s || '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

async function main() {
  const args = parseArgs();
  const out = path.resolve(args.out || 'share-card.png');
  const logoDataURL = 'data:image/png;base64,' + fs.readFileSync(LOGO_PATH).toString('base64');
  const html = buildHTML({
    title: args.title || '请提供 --title',
    verdict: args.verdict || 'fake',
    verdictText: args['verdict-text'],
    summary: args.summary || '请提供 --summary',
    logoDataURL,
  });
  const tmpHTML = path.resolve('_tmp_card.html');
  fs.writeFileSync(tmpHTML, html, 'utf8');

  const exe = CHROME_PATHS.find(p => fs.existsSync(p));
  if (!exe) { console.error('No Chrome/Edge found'); process.exit(1); }

  const browser = await puppeteer.launch({
    executablePath: exe,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1080, deviceScaleFactor: 2 });
  await page.goto('file://' + tmpHTML.replace(/\\/g, '/'), { waitUntil: 'networkidle0' });
  await page.waitForFunction('document.body.dataset.ready === "1"', { timeout: 5000 });
  await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1080, height: 1080 } });
  await browser.close();
  fs.unlinkSync(tmpHTML);
  console.log('Saved:', out);
}
main().catch(e => { console.error(e); process.exit(1); });
