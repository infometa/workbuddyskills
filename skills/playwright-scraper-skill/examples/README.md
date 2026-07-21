# Usage Examples

## Basic Usage

### 1. Quick Scrape (Example.com)

```bash
node scripts/playwright-simple.js https://example.com
```

**Output:**
```json
{
  "title": "Example Domain",
  "url": "https://example.com/",
  "content": "Example Domain\n\nThis domain is for use...",
  "metaDescription": "",
  "elapsedSeconds": "3.42"
}
```

---

### 2. Anti-Bot Protected Site (Discuss.com.hk)

```bash
node scripts/playwright-stealth.js "https://m.discuss.com.hk/#hot"
```

**Output:**
```json
{
  "title": "香港討論區 discuss.com.hk",
  "url": "https://m.discuss.com.hk/#hot",
  "htmlLength": 186345,
  "contentPreview": "...",
  "cloudflare": false,
  "screenshot": "./screenshot-1770467444364.png",
  "data": {
    "links": [
      {
        "text": "區議員周潔瑩疑消防通道違泊 道歉稱急於搬貨",
        "href": "https://m.discuss.com.hk/index.php?action=thread&tid=32148378..."
      }
    ]
  },
  "elapsedSeconds": "19.59"
}
```

---

## Advanced Usage

### 3. Custom Wait Time

```bash
WAIT_TIME=15000 node scripts/playwright-stealth.js <URL>
```

### 4. Show Browser (Debug Mode)

```bash
HEADLESS=false node scripts/playwright-stealth.js <URL>
```

### 5. Save Screenshot and HTML

```bash
SCREENSHOT_PATH=/tmp/my-page.png \
SAVE_HTML=true \
node scripts/playwright-stealth.js <URL>
```

### 6. Custom User-Agent

```bash
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
node scripts/playwright-stealth.js <URL>
```

---

## Integration Examples

### Using in Shell Scripts

```bash
#!/bin/bash
# Run from playwright-scraper-skill directory

URL="https://example.com"
OUTPUT_FILE="result.json"

echo "🕷️  Starting scrape: $URL"

node scripts/playwright-stealth.js "$URL" > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo "✅ Success! Results saved to: $OUTPUT_FILE"
else
  echo "❌ Failed"
  exit 1
fi
```

### Batch Scraping Multiple URLs

```bash
#!/bin/bash

URLS=(
  "https://example.com"
  "https://example.org"
  "https://example.net"
)

for url in "${URLS[@]}"; do
  echo "Scraping: $url"
  node scripts/playwright-stealth.js "$url" > "output_$(date +%s).json"
  sleep 5  # Avoid IP blocking
done
```

---

## Calling from Node.js

```javascript
const { spawn } = require('child_process');

function scrape(url) {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [
      'scripts/playwright-stealth.js',
      url
    ]);
    
    let output = '';
    
    proc.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    proc.on('close', (code) => {
      if (code === 0) {
        try {
          // Extract JSON (last line)
          const lines = output.trim().split('\n');
          const json = JSON.parse(lines[lines.length - 1]);
          resolve(json);
        } catch (e) {
          reject(e);
        }
      } else {
        reject(new Error(`Exit code: ${code}`));
      }
    });
  });
}

// Usage
(async () => {
  const result = await scrape('https://example.com');
  console.log(result.title);
})();
```

---

## Common Scenarios

### Scraping News Articles

```bash
node scripts/playwright-stealth.js "https://news.example.com/article/123"
```

### Scraping E-commerce Products

```bash
WAIT_TIME=10000 \
SAVE_HTML=true \
node scripts/playwright-stealth.js "https://shop.example.com/product/456"
```

### Scraping Forum Posts

```bash
node scripts/playwright-stealth.js "https://forum.example.com/thread/789"
```

---

## Troubleshooting

### Issue: Page Not Fully Loaded

**Solution:** Increase wait time
```bash
WAIT_TIME=20000 node scripts/playwright-stealth.js <URL>
```

### Issue: Still Blocked by Cloudflare

**Solution:** Use headful mode + manual wait
```bash
HEADLESS=false \
WAIT_TIME=30000 \
node scripts/playwright-stealth.js <URL>
```

### Issue: Requires Login

**Solution:** Manually login first, export cookies, then load
(Future feature, currently not supported)

---

## Performance Tips

1. **Parallel scraping:** Use `Promise.all()` or shell `&`
2. **Delay requests:** `sleep 5` to avoid IP blocking
3. **Use proxies:** Rotate IPs (future feature)
4. **Cache results:** Avoid duplicate scraping

---

For more information, see [SKILL.md](../SKILL.md)
