---
name: playwright-browser-automation
description: "Direct Playwright API for browser automation without MCP complexity. Navigate websites, interact with elements, extract data, take screenshots, generate PDFs, record videos. More reliable than MCP-based approaches. Requires: node, npx, playwright."
description_zh: "直接调用 Playwright API 实现浏览器自动化（无需 MCP）"
description_en: "Direct Playwright API browser automation: navigate, interact, screenshot, PDF"
version: 2.0.0
allowed-tools: Bash
metadata:
  openclaw:
    emoji: "\U0001F3AD"
    os:
      - linux
      - darwin
      - win32
    requires:
      bins:
        - node
        - npx
    install:
      - id: npm-playwright
        kind: npm
        package: playwright
        bins:
          - playwright
        label: Install Playwright
---

# Playwright Browser Automation

Direct Playwright API for reliable browser automation without MCP complexity.

## Installation

```bash
# Install Playwright
npm install -g playwright

# Install browsers (one-time, ~100MB each)
npx playwright install chromium
# Optional:
npx playwright install firefox
npx playwright install webkit

# For system dependencies on Ubuntu/Debian:
sudo npx playwright install-deps chromium
```

## Quick Start

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://example.com');
  await page.screenshot({ path: 'screenshot.png' });
  
  await browser.close();
})();
```

## Best Practices

### 1. Use Locators (Auto-waiting)

```javascript
// ✅ GOOD: Uses auto-waiting and retries
await page.getByRole('button', { name: 'Submit' }).click();
await page.getByLabel('Username').fill('user');
await page.getByPlaceholder('Search').fill('query');

// ❌ BAD: May fail if element not ready
await page.click('#submit');
```

### 2. Prefer User-Facing Attributes

```javascript
// ✅ GOOD: Resilient to DOM changes
await page.getByRole('heading', { name: 'Welcome' });
await page.getByText('Sign in');
await page.getByTestId('login-button');

// ❌ BAD: Brittle CSS selectors
await page.click('.btn-primary > div:nth-child(2)');
```

### 3. Handle Dynamic Content

```javascript
// Wait for network idle
await page.goto('https://spa-app.com', { waitUntil: 'networkidle' });

// Wait for specific element
await page.waitForSelector('.results-loaded');
await page.waitForFunction(() => document.querySelectorAll('.item').length > 0);
```

### 4. Use Contexts for Isolation

```javascript
// Each context = isolated session (cookies, storage)
const context = await browser.newContext();
const page = await context.newPage();

// Multiple pages in one context
const page2 = await context.newPage();
```

### 5. Network Interception

```javascript
// Mock API responses
await page.route('**/api/users', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ users: [] })
  });
});

// Block resources
await page.route('**/*.{png,jpg,css}', route => route.abort());
```

## Common Patterns

### Form Automation

```javascript
// Fill form
await page.goto('https://example.com/login');
await page.getByLabel('Username').fill('myuser');
await page.getByLabel('Password').fill('mypass');
await page.getByRole('button', { name: 'Sign in' }).click();

// Wait for navigation/result
await page.waitForURL('/dashboard');
await expect(page.getByText('Welcome')).toBeVisible();
```

### Data Extraction

```javascript
// Extract table data
const rows = await page.$$eval('table tr', rows =>
  rows.map(row => ({
    name: row.querySelector('td:nth-child(1)')?.textContent,
    price: row.querySelector('td:nth-child(2)')?.textContent
  }))
);

// Extract with JavaScript evaluation
const data = await page.evaluate(() => {
  return Array.from(document.querySelectorAll('.product')).map(p => ({
    title: p.querySelector('.title')?.textContent,
    price: p.querySelector('.price')?.textContent
  }));
});
```

### Screenshots & PDFs

```javascript
// Full page screenshot
await page.screenshot({ path: 'full.png', fullPage: true });

// Element screenshot
await page.locator('.chart').screenshot({ path: 'chart.png' });

// PDF (Chromium only)
await page.pdf({ 
  path: 'page.pdf', 
  format: 'A4',
  printBackground: true 
});
```

### Video Recording

```javascript
const context = await browser.newContext({
  recordVideo: {
    dir: './videos/',
    size: { width: 1920, height: 1080 }
  }
});
const page = await context.newPage();

// ... do stuff ...

await context.close(); // Video saved automatically
```

### Mobile Emulation

```javascript
const context = await browser.newContext({
  viewport: { width: 375, height: 667 },
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)',
  isMobile: true,
  hasTouch: true
});
```

### Authentication

```javascript
// Method 1: HTTP Basic Auth
const context = await browser.newContext({
  httpCredentials: { username: 'user', password: 'pass' }
});

// Method 2: Cookies
await context.addCookies([
  { name: 'session', value: 'abc123', domain: '.example.com', path: '/' }
]);

// Method 3: Local Storage
await page.evaluate(() => {
  localStorage.setItem('token', 'xyz');
});

// Method 4: Reuse auth state
await context.storageState({ path: 'auth.json' });
// Later: await browser.newContext({ storageState: 'auth.json' });
```

## Advanced Features

### File Upload/Download

```javascript
// Upload
await page.setInputFiles('input[type="file"]', '/path/to/file.pdf');

// Download
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.click('a[download]')
]);
await download.saveAs('/path/to/save/' + download.suggestedFilename());
```

### Dialogs Handling

```javascript
page.on('dialog', dialog => {
  if (dialog.type() === 'alert') dialog.accept();
  if (dialog.type() === 'confirm') dialog.accept();
  if (dialog.type() === 'prompt') dialog.accept('My answer');
});
```

### Frames & Shadow DOM

```javascript
// Frame by name
const frame = page.frame('frame-name');
await frame.click('button');

// Frame by locator
const frame = page.frameLocator('iframe').first();
await frame.getByRole('button').click();

// Shadow DOM
await page.locator('my-component').locator('button').click();
```

### Tracing (Debug)

```javascript
await context.tracing.start({ screenshots: true, snapshots: true });

// ... run tests ...

await context.tracing.stop({ path: 'trace.zip' });
// View at https://trace.playwright.dev
```

## Configuration Options

```javascript
const browser = await chromium.launch({
  headless: true,        // Run without UI
  slowMo: 50,           // Slow down by 50ms (for debugging)
  devtools: false,      // Open DevTools
  args: ['--no-sandbox', '--disable-setuid-sandbox'] // Docker/Ubuntu
});

const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  locale: 'ru-RU',
  timezoneId: 'Europe/Moscow',
  geolocation: { latitude: 55.7558, longitude: 37.6173 },
  permissions: ['geolocation'],
  userAgent: 'Custom Agent',
  bypassCSP: true,      // Bypass Content Security Policy
});
```

## Error Handling

```javascript
// Retry with timeout
try {
  await page.getByRole('button', { name: 'Load' }).click({ timeout: 10000 });
} catch (e) {
  console.log('Button not found or not clickable');
}

// Check if element exists
const hasButton = await page.getByRole('button').count() > 0;

// Wait with custom condition
await page.waitForFunction(() => 
  document.querySelectorAll('.loaded').length >= 10
);
```

## Sudoers Setup

For Playwright browser installation:

```bash
# /etc/sudoers.d/playwright
username ALL=(root) NOPASSWD: /usr/bin/npx playwright install-deps *
username ALL=(root) NOPASSWD: /usr/bin/npx playwright install *
```

## References

- [Playwright Docs](https://playwright.dev)
- [API Reference](https://playwright.dev/docs/api/class-playwright)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Locators Guide](https://playwright.dev/docs/locators)
