---
name: static-app
description: "Deploy static websites and built frontend apps to Static.app hosting. Use when a user wants to upload, host, update, or manage a static site through Static.app with an API key."
description_zh: "将静态网站或前端构建产物部署到 Static.app"
description_en: "Deploy static websites and frontend builds to Static.app hosting"
version: 1.0.4
homepage: https://static.app
allowed-tools: Bash,Read
---
# Static.app Deployment Skill

Deploy static websites and applications to [Static.app](https://static.app) hosting directly from OpenClaw.

## Workspace Structure

All Static.app operations in your workspace use a dedicated folder structure:

```
workspace/
└── staticapp/              # Main folder for all Static.app operations
    ├── new-site/           # New sites created locally
    └── {pid}/              # Downloaded existing sites (by PID)
```

- **New sites**: Created in `staticapp/` subfolders before deployment
- **Downloaded sites**: Extracted to `staticapp/{pid}/` for editing

## How Static.app Handles Files

Static.app automatically creates clean URLs from your filenames:

| File | URL |
|------|-----|
| `index.html` | `/` (homepage) |
| `about.html` | `/about` |
| `portfolio.html` | `/portfolio` |
| `contact.html` | `/contact` |

**No subdirectories needed!** Just create `.html` files in the root folder.

## Project Structure

### Simple Multi-Page Site

```
my-site/
├── index.html          # Homepage → /
├── about.html          # About page → /about
├── portfolio.html      # Portfolio → /portfolio
├── contact.html        # Contact → /contact
├── style.css           # Stylesheet
├── js/                 # JavaScript files
│   ├── main.js
│   └── utils.js
└── images/             # Images folder
    ├── logo.png
    └── photo.jpg
```

### JavaScript App (React, Vue, etc.)

For JS apps, **build first**, then deploy the `dist` (or `build`) folder:

```bash
# Build your app
npm run build

# Deploy the dist folder
node scripts/deploy.js ./dist
```

## Prerequisites

1. **Get API Key**: Go to https://static.app/account/api and create an API key (starts with `sk_`)
2. **Set Environment Variable**: Store the API key in `STATIC_APP_API_KEY` env var

## Usage

### Deploy Multi-Page Site

```bash
# Create your pages
echo '<h1>Home</h1>' > index.html
echo '<h1>About</h1>' > about.html
echo '<h1>Portfolio</h1>' > portfolio.html

# Deploy
node scripts/deploy.js
```

### Deploy Specific Directory

```bash
node scripts/deploy.js ./my-site
```

### Update Existing Site

```bash
node scripts/deploy.js . --pid olhdscieyr
```

### List All Sites

```bash
node scripts/list.js
```

### List Site Files

```bash
node scripts/files.js YOUR_PID
```

Options:
- `--raw` — Output raw JSON
- `-k <key>` — Specify API key

### Delete Site

```bash
node scripts/delete.js YOUR_PID
```

Options:
- `-f, --force` — Skip confirmation prompt
- `-k <key>` — Specify API key

### Download Site

Download an existing site to your workspace for editing:

```bash
node scripts/download.js YOUR_PID
```

This will:
1. Fetch the download URL from Static.app API
2. Download the site archive
3. Extract it to `staticapp/{pid}/`

Options:
- `-p, --pid` — Site PID to download
- `-o, --output` — Custom output directory (default: `./staticapp/{pid}`)
- `-k <key>` — Specify API key
- `--raw` — Output raw JSON response

Example:
```bash
# Download site to default location
node scripts/download.js abc123

# Download to custom folder
node scripts/download.js abc123 -o ./my-site
```

## Script Options

```
node scripts/deploy.js [SOURCE_DIR] [OPTIONS]

Arguments:
  SOURCE_DIR          Directory to deploy (default: current directory)

Options:
  -k, --api-key       API key (or set STATIC_APP_API_KEY env var)
  -p, --pid           Project PID to update existing site
  -e, --exclude       Comma-separated exclude patterns
  --keep-zip          Keep zip archive after deployment
```

## Default Exclusions

The following are automatically excluded from deployment:
- `node_modules`
- `.git`, `.github`
- `*.md`
- `package*.json`
- `.env`
- `.openclaw`

## Important Notes

### ✅ What Works

- **Static HTML sites** — Any number of `.html` pages
- **CSS & JavaScript** — Frontend frameworks, vanilla JS
- **Images & Assets** — Place in `images/` folder or root
- **JavaScript files** — Place in `js/` folder or root
- **Built JS Apps** — Deploy `dist/` or `build/` folder after `npm run build`

### ❌ What Doesn't Work

- **Node.js Server Apps** — No server-side rendering, no Express.js, no API routes
- **PHP, Python, Ruby** — Static.app only serves static files
- **Databases** — Use client-side storage or external APIs

### JavaScript Apps Workflow

```bash
# 1. Build your React/Vue/Angular app
npm run build

# 2. Deploy the build output
node scripts/deploy.js ./dist --pid YOUR_PID
```

## API Reference

### Deploy Site
- **Endpoint**: `POST https://api.static.app/v1/sites/zip`
- **Auth**: Bearer token (API key)
- **Body**: Multipart form with `archive` (zip file) and optional `pid`

### List Sites
- **Endpoint**: `GET https://api.static.app/v1/sites`
- **Auth**: Bearer token (API key)
- **Headers**: `Accept: application/json`

### List Site Files
- **Endpoint**: `GET https://api.static.app/v1/sites/files/{pid}`
- **Auth**: Bearer token (API key)
- **Headers**: `Accept: application/json`

### Delete Site
- **Endpoint**: `DELETE https://api.static.app/v1/sites/{pid}`
- **Auth**: Bearer token (API key)
- **Headers**: `Accept: application/json`

### Download Site
- **Endpoint**: `GET https://api.static.app/v1/sites/download/{pid}`
- **Auth**: Bearer token (API key)
- **Headers**: `Accept: application/json`
- **Response**: Returns download URL for the site archive

## Dependencies

- `archiver` — Zip archive creation
- `form-data` — Multipart form encoding
- `node-fetch` — HTTP requests
- `adm-zip` — Zip extraction

Install with: `cd scripts && npm install`

## Response

On success, the script outputs:
```
✅ Deployment successful!
🌐 Site URL: https://xyz.static.app
📋 PID: abc123

STATIC_APP_URL=https://xyz.static.app
STATIC_APP_PID=abc123
```

## Workflow

1. Check for `STATIC_APP_API_KEY` env var or `--api-key`
2. Create zip archive from source directory (with exclusions)
3. Upload to Static.app API
4. Parse response and output URLs
5. Clean up temporary zip file

## Error Handling

- Missing API key → Clear error with instructions
- Network issues → HTTP error details
- Invalid PID → API error message
