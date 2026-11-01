#!/usr/bin/env node
/**
 * html2pdf.js — 将 HTML 报告转换为单页长图 PDF（fullpage 模式）
 *
 * 专为电商数据分析报告设计，内置 Chart.js 图表等待和字体加载。
 * 生成不分页的矢量长图 PDF，保留完整报告样式。
 *
 * 用法:
 *   node html2pdf.js <input.html> [-o output.pdf]
 *
 * 选项:
 *   -o, --output <path>   输出 PDF 路径（默认同名 .pdf）
 *   --width <px>          视口宽度（默认 1280）
 *   --wait <ms>           额外等待时间，毫秒（默认 2000）
 *   --scale <n>           设备像素比（默认 2）
 *   --margin <mm>         页边距，毫米（默认 10）
 *
 * 示例:
 *   node html2pdf.js report.html
 *   node html2pdf.js report.html -o /tmp/report.pdf
 *   node html2pdf.js report.html --width 1400 --wait 3000
 *
 * 依赖:
 *   已有 puppeteer-core 或 puppeteer 和 Chromium；不会自动安装
 */

// Dependency detection only; no package installation or global shell commands.
function loadPuppeteer() {
  for (const moduleName of ["puppeteer-core", "puppeteer"]) {
    try { return require(moduleName); } catch {}
  }
  throw new Error("PDF unavailable: puppeteer-core/puppeteer missing; retain HTML.");
}

// Executed in the page: canvas default dimensions do not prove Chart.js rendered.
function chartsReady() {
  const canvases = [...document.querySelectorAll("canvas")];
  if (canvases.length === 0) return true;
  return typeof Chart !== "undefined" && typeof Chart.getChart === "function" &&
    canvases.every(canvas => {
      const chart = Chart.getChart(canvas);
      return chart && chart.canvas === canvas && chart.width > 0 && chart.height > 0;
    });
}

const path = require("path");
const fs = require("fs");

// ─── 查找系统 Chromium（puppeteer-core 需要显式指定路径）──────
function findSystemChromium() {
  const candidates = [
    process.env.CHROME_PATH,
    process.env.PROGRAMFILES && require("path").join(process.env.PROGRAMFILES, "Google/Chrome/Application/chrome.exe"),
    process.env.LOCALAPPDATA && require("path").join(process.env.LOCALAPPDATA, "Google/Chrome/Application/chrome.exe"),
    // All-In-One 沙箱常见路径
    "/usr/bin/chromium-browser",
    "/usr/bin/chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    // Snap 安装
    "/snap/bin/chromium",
    // macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ];
  for (const p of candidates) {
    if (p && fs.existsSync(p)) return p;
  }
  return null;
}

// ─── 参数解析 ──────────────────────────────────────────────
function parseArgs(argv) {
  const args = {
    input: null,
    output: null,
    width: 1280,
    wait: 2000,
    scale: 2,
    margin: 10,
  };

  let i = 2;
  while (i < argv.length) {
    const arg = argv[i];
    switch (arg) {
      case "-o":
      case "--output":
        args.output = argv[++i];
        break;
      case "--width":
        args.width = parseInt(argv[++i], 10);
        break;
      case "--wait":
        args.wait = parseInt(argv[++i], 10);
        break;
      case "--scale":
        args.scale = parseFloat(argv[++i]);
        break;
      case "--margin":
        args.margin = parseInt(argv[++i], 10);
        break;
      case "-h":
      case "--help":
        console.log(
            `用法: node html2pdf.js <input.html> [-o output.pdf] [--width 1280] [--wait 2000] [--scale 2] [--margin 10]`
        );
        process.exit(0);
        break;
      default:
        if (arg.startsWith("-")) {
          console.error(`未知参数: ${arg}`);
          process.exit(1);
        }
        args.input = arg;
    }
    i++;
  }

  if (!args.input) {
    console.error("错误: 请提供输入 HTML 文件路径");
    process.exit(1);
  }

  return args;
}

// ─── 核心转换函数 ──────────────────────────────────────────
/**
 * 将 HTML 转换为 fullpage（不分页长图）PDF
 *
 * @param {string} htmlPath  输入 HTML 文件路径
 * @param {object} options   选项
 * @param {string} [options.outputPath]  输出 PDF 路径（默认同名 .pdf）
 * @param {number} [options.width=1280]  视口宽度 px
 * @param {number} [options.wait=2000]   额外等待时间 ms
 * @param {number} [options.scale=2]     设备像素比
 * @param {number} [options.margin=10]   页边距 mm
 * @returns {Promise<string>} 输出 PDF 的绝对路径
 */
async function htmlToPdf(htmlPath, options = {}) {
  const {
    outputPath = null,
    width = 1280,
    wait = 2000,
    scale = 2,
    margin = 10,
  } = options;

  const absHtmlPath = path.resolve(htmlPath);
  if (!fs.existsSync(absHtmlPath)) {
    throw new Error(`文件不存在: ${absHtmlPath}`);
  }

  const pdfPath = outputPath
      ? path.resolve(outputPath)
      : absHtmlPath.replace(/\.html?$/i, ".pdf");

  // 确保输出目录存在
  const outDir = path.dirname(pdfPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  let browser;
  try {
    const launchOptions = {
      headless: "new",
      args: [],
    };
    // puppeteer-core 需要显式指定 Chromium 路径
    const chromiumPath = findSystemChromium();
    if (chromiumPath) {
      launchOptions.executablePath = chromiumPath;
    }
    browser = await loadPuppeteer().launch(launchOptions);

    const page = await browser.newPage();
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(error.message));

    try {
      // 设置视口
      await page.setViewport({
        width: width,
        height: 900,
        deviceScaleFactor: scale,
      });

      // 加载页面，等待网络空闲
      await page.goto(require("url").pathToFileURL(absHtmlPath).href, {
        waitUntil: "networkidle0",
        timeout: 30000,
      });

      // 等待字体加载
      try {
        await page.evaluate(() => document.fonts.ready);
        console.log("  ✓ 字体加载完成");
      } catch (_) {
        // fonts API 不可用时忽略
      }

      // Require real Chart instances; blocked CDN or script failure must fall back to HTML.
      await page.waitForFunction(chartsReady, { timeout: 10000 });
      if (pageErrors.length) throw new Error("Report JavaScript failed: " + pageErrors.join("; "));
      console.log("  ✓ 图表实例加载完成");

      // 额外等待（确保动画和延迟脚本完成）
      if (wait > 0) {
        await new Promise((r) => setTimeout(r, wait));
      }

      if (pageErrors.length) throw new Error("Report JavaScript failed: " + pageErrors.join("; "));

      // 固定 canvas 渲染尺寸，防止 PDF 中图表高度塌缩
      await page.evaluate(() => {
        document.querySelectorAll("canvas").forEach((c) => {
          if (c.width > 0 && c.height > 0) {
            const ratio = c.height / c.width;
            const displayWidth = c.offsetWidth || c.clientWidth;
            if (displayWidth > 0) {
              c.style.height = Math.round(displayWidth * ratio) + "px";
            }
          }
        });
      });

      // 获取页面完整尺寸
      const dimensions = await page.evaluate(() => {
        const body = document.body;
        const html = document.documentElement;
        const height = Math.max(
            body.scrollHeight,
            body.offsetHeight,
            html.clientHeight,
            html.scrollHeight,
            html.offsetHeight
        );
        const container = document.querySelector(".container");
        let cWidth;
        if (container) {
          const style = getComputedStyle(container);
          const maxW = parseFloat(style.maxWidth);
          cWidth = maxW && isFinite(maxW) ? maxW : container.scrollWidth;
        } else {
          cWidth = body.scrollWidth;
        }
        return { width: cWidth, height };
      });

      console.log(
          `  ✓ 页面尺寸: ${dimensions.width}px × ${dimensions.height}px`
      );

      // px → mm 转换 (96 dpi: 1mm = 96/25.4 px)
      const pxToMm = 25.4 / 96;
      const contentWidthMm = dimensions.width * pxToMm;
      const contentHeightMm = dimensions.height * pxToMm;

      // 纸张尺寸 = 内容 + 边距 + 少量余量
      const pageWidthMm = contentWidthMm + margin * 2;
      const pageHeightMm = contentHeightMm + margin * 2 + 2;

      console.log(
          `  ✓ PDF 纸张: ${pageWidthMm.toFixed(1)}mm × ${pageHeightMm.toFixed(1)}mm`
      );

      // 注入 print 样式：去掉 box-shadow，避免 PDF 中出现多余阴影框
      await page.addStyleTag({
        content: `
          @media print {
            * { box-shadow: none !important; -webkit-box-shadow: none !important; }
          }
        `,
      });

      // 生成 PDF
      await page.pdf({
        path: pdfPath,
        width: `${pageWidthMm.toFixed(2)}mm`,
        height: `${pageHeightMm.toFixed(2)}mm`,
        printBackground: true,
        scale: 1.0,
        margin: {
          top: `${margin}mm`,
          right: `${margin}mm`,
          bottom: `${margin}mm`,
          left: `${margin}mm`,
        },
        displayHeaderFooter: false,
      });
    } finally {
      await page.close();
    }
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  const stat = fs.statSync(pdfPath);
  const sizeKB = (stat.size / 1024).toFixed(1);
  console.log(`  ✓ PDF 生成完成: ${pdfPath} (${sizeKB} KB)`);

  return pdfPath;
}

// ─── 导出 ──────────────────────────────────────────────────
module.exports = { htmlToPdf, chartsReady };

// ─── CLI 入口 ──────────────────────────────────────────────
if (require.main === module) {
  const args = parseArgs(process.argv);
  console.log(`⏳ 正在转换: ${args.input}`);

  htmlToPdf(args.input, {
    outputPath: args.output,
    width: args.width,
    wait: args.wait,
    scale: args.scale,
    margin: args.margin,
  })
      .then((pdfPath) => {
        console.log(`✅ 完成: ${pdfPath}`);
        process.exit(0);
      })
      .catch((err) => {
        console.error(`❌ 转换失败: ${err.message}`);
        process.exit(1);
      });
}
