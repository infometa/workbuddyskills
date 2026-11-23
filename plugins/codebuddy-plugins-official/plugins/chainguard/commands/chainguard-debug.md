---
description: Toggle debug logging or export diagnostic bundle for ChainGuard troubleshooting
---

Manage ChainGuard plugin debug logging and diagnostic export.

User argument can be:
- `on`: Enable debug mode (records full diagnostic logs to /tmp/security-guard.log)
- `off`: Disable debug mode
- `export`: Package and export logs for troubleshooting
- (empty / status): Show current debug status

Execute this command:

```
node ${CODEBUDDY_PLUGIN_ROOT}/dist/security-guard.cjs --debug-toggle $ARGUMENTS
```

Show the user a clear, concise confirmation of the action performed.
If logs were exported, display the archive file path and instruct the user:
"📋 请将此日志文件发送给 @selinasong 进行排障分析。"
