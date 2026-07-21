# Windows Support Notes

The upstream `vercel-labs/agent-browser` project provides a native Windows x64 build.

## Target Environment

- Windows 11 x64
- PowerShell
- Node.js 18+
- npm available in PATH

## Install

```powershell
npm install -g agent-browser
agent-browser install
```

## Verify Browser Automation

```powershell
agent-browser open https://example.com
agent-browser wait --load networkidle
agent-browser snapshot
agent-browser screenshot
agent-browser close
```

## Common Issues

### `agent-browser` command not found

Restart PowerShell and check npm global prefix:

```powershell
npm config get prefix
```

Make sure the npm global bin directory is in PATH.

### Chromium install failed

Retry the browser installation:

```powershell
agent-browser install
```

### Browser does not close

Run:

```powershell
agent-browser close
```

If needed, close remaining browser processes from Task Manager.

---

For deeper environment problems (daemon won't start, Chromium revision mismatch, SIGILL / Exit 133, install timeouts), see [`troubleshooting.md`](./troubleshooting.md).
