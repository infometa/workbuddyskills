---
description: Browser automation with Playwright MCP. Use for web scraping, testing, screenshots, and browser interactions.
mcp:
  playwright:
    command: npx
    args: ["@playwright/mcp@latest"]
---

# Playwright Browser Automation

This skill provides browser automation capabilities via the Playwright MCP server.

## When to Use

Use this skill for:
- Web scraping and data extraction
- Automated browser testing
- Taking screenshots of web pages
- Form filling and user interaction simulation
- Monitoring and validation of web applications
- DOM element inspection and manipulation

## Capabilities

Through the Playwright MCP, this skill provides:

### Navigation & Page Control
- Navigate to URLs
- Take screenshots (full page or specific elements)
- Execute JavaScript in page context
- Get page content and HTML

### Element Interaction
- Click elements
- Fill in forms and inputs
- Select dropdown options
- Hover over elements
- Press keyboard keys

### Inspection & Validation
- Get element attributes and properties
- Extract text content
- Verify element existence
- Check element visibility
- Validate page state

### Advanced Features
- Handle multiple tabs/windows
- Wait for specific conditions
- Capture network requests
- Manage browser cookies
- Handle file uploads/downloads

## Usage Examples

### Basic Navigation and Screenshot
```
Use skill playwright to navigate to https://example.com and take a screenshot
```

### Form Automation
```
Use skill playwright to:
1. Navigate to https://example.com/login
2. Fill in username field with "test@example.com"
3. Fill in password field with "password123"
4. Click the submit button
5. Take a screenshot of the result
```

### Data Extraction
```
Use skill playwright to scrape product prices from https://example.com/products
```

### Testing
```
Use skill playwright to test the checkout flow on our staging site
```

## Notes

- The Playwright MCP server will be automatically started when this skill is used
- Browser runs in headless mode by default
- Screenshots are saved to the current directory
- Supports modern web standards (ES6+, Web Components, etc.)
- Works with SPA frameworks (React, Vue, Angular)

## Requirements

- Node.js 14+ (for npx)
- Internet connection (to install MCP server on first use)
- Sufficient disk space for Chromium browser

## Troubleshooting

If the skill fails to start:
1. Verify Node.js is installed: `node --version`
2. Check network connectivity
3. Try manual installation: `npm install -g @playwright/mcp`
4. Check system resources (RAM, disk space)


