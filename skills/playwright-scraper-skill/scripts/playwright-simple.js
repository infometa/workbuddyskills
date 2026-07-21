#!/usr/bin/env node
/**
 * Playwright Simple Scraper
 * 適用：一般動態網站，無反爬保護
 * 速度：快（3-5 秒）
 * 
 * Usage: node playwright-simple.js <URL>
 */

const { chromium } = require('playwright');

const url = process.argv[2];
const waitTime = parseInt(process.env.WAIT_TIME || '3000');
const screenshotPath = process.env.SCREENSHOT_PATH;

if (!url) {
    console.error('❌ 請提供 URL');
    console.error('用法: node playwright-simple.js <URL>');
    process.exit(1);
}

(async () => {
    console.log('🚀 啟動 Playwright 簡單版爬蟲...');
    const startTime = Date.now();
    
    const browser = await chromium.launch({ 
        headless: process.env.HEADLESS !== 'false' 
    });
    const page = await browser.newPage();
    
    console.log(`📱 導航到: ${url}`);
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    
    console.log(`⏳ 等待 ${waitTime}ms...`);
    await page.waitForTimeout(waitTime);
    
    // 擷取基本資訊
    const result = await page.evaluate(() => {
        return {
            title: document.title,
            url: window.location.href,
            content: document.body.innerText.substring(0, 5000),
            metaDescription: document.querySelector('meta[name="description"]')?.content || '',
        };
    });
    
    // 截圖（如果指定）
    if (screenshotPath) {
        await page.screenshot({ path: screenshotPath });
        console.log(`📸 截圖已儲存: ${screenshotPath}`);
    }
    
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(2);
    result.elapsedSeconds = elapsed;
    
    console.log('\n✅ 爬取完成！');
    console.log(JSON.stringify(result, null, 2));
    
    await browser.close();
})();
