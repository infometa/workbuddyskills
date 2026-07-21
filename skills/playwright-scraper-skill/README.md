# Playwright Scraper Skill 🕷️

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Playwright](https://img.shields.io/badge/Playwright-1.40+-blue.svg)](https://playwright.dev/)

**[中文文檔](README_ZH.md)** | English

A Playwright-based web scraping OpenClaw Skill with anti-bot protection. Successfully tested on complex websites like Discuss.com.hk.

> 📦 **Installation:** See [INSTALL.md](INSTALL.md)  
> 📚 **Full Documentation:** See [SKILL.md](SKILL.md)  
> 💡 **Examples:** See [examples/README.md](examples/README.md)

---

## ✨ Features

- ✅ **Pure Playwright** — Modern, powerful, easy to use
- ✅ **Anti-Bot Protection** — Hides automation, realistic UA
- ✅ **Verified** — 100% success on Discuss.com.hk
- ✅ **Simple to Use** — One-line commands
- ✅ **Customizable** — Environment variable support

---

## 🚀 Quick Start

### Installation

```bash
npm install
npx playwright install chromium
```

### Usage

```bash
# Quick scraping
node scripts/playwright-simple.js https://example.com

# Stealth mode (recommended)
node scripts/playwright-stealth.js "https://m.discuss.com.hk/#hot"
```

---

## 📖 Two Modes

| Mode | Use Case | Speed | Anti-Bot |
|------|----------|-------|----------|
| **Simple** | Regular dynamic sites | Fast (3-5s) | None |
| **Stealth** ⭐ | Sites with anti-bot | Medium (5-20s) | Medium-High |

### Simple Mode

For sites without anti-bot protection:

```bash
node scripts/playwright-simple.js <URL>
```

### Stealth Mode (Recommended)

For sites with Cloudflare or anti-bot protection:

```bash
node scripts/playwright-stealth.js <URL>
```

**Anti-Bot Techniques:**
- Hide `navigator.webdriver`
- Realistic User-Agent (iPhone)
- Human-like behavior simulation
- Screenshot and HTML saving support

---

## 🎯 Customization

All scripts support environment variables:

```bash
# Show browser
HEADLESS=false node scripts/playwright-stealth.js <URL>

# Custom wait time (milliseconds)
WAIT_TIME=10000 node scripts/playwright-stealth.js <URL>

# Save screenshot
SCREENSHOT_PATH=/tmp/page.png node scripts/playwright-stealth.js <URL>

# Save HTML
SAVE_HTML=true node scripts/playwright-stealth.js <URL>

# Custom User-Agent
USER_AGENT="Mozilla/5.0 ..." node scripts/playwright-stealth.js <URL>
```

---

## 📊 Test Results

| Website | Result | Time |
|---------|--------|------|
| **Discuss.com.hk** | ✅ 200 OK | 5-20s |
| **Example.com** | ✅ 200 OK | 3-5s |
| **Cloudflare Protected** | ✅ Mostly successful | 10-30s |

---

## 📁 File Structure

```
playwright-scraper-skill/
├── scripts/
│   ├── playwright-simple.js       # Simple mode
│   └── playwright-stealth.js      # Stealth mode ⭐
├── examples/
│   ├── discuss-hk.sh              # Discuss.com.hk example
│   └── README.md                  # More examples
├── SKILL.md                       # Full documentation
├── INSTALL.md                     # Installation guide
├── README.md                      # This file
├── README_ZH.md                   # Chinese documentation
├── CONTRIBUTING.md                # Contribution guide
├── CHANGELOG.md                   # Version history
└── package.json                   # npm config
```

---

## 💡 Best Practices

1. **Try web_fetch first** — OpenClaw's built-in tool is fastest
2. **Use Simple for dynamic sites** — When no anti-bot protection
3. **Use Stealth for protected sites** ⭐ — Main workhorse
4. **Use specialized skills** — For YouTube, Reddit, etc.

---

## 🐛 Troubleshooting

### Getting 403 blocked?

Use Stealth mode:
```bash
node scripts/playwright-stealth.js <URL>
```

### Cloudflare challenge?

Increase wait time + headful mode:
```bash
HEADLESS=false WAIT_TIME=30000 node scripts/playwright-stealth.js <URL>
```

### Playwright not found?

Reinstall:
```bash
npm install
npx playwright install chromium
```

More issues? See [INSTALL.md](INSTALL.md)

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License - See [LICENSE](LICENSE)

---

## 🔗 Links

- [Playwright Official Docs](https://playwright.dev/)
- [Full Documentation (SKILL.md)](SKILL.md)
- [Installation Guide (INSTALL.md)](INSTALL.md)
- [Examples (examples/)](examples/)
