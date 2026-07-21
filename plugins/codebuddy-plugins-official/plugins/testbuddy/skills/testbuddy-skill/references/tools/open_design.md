# open_design

打开 TestBuddy 测试设计页面。用于用户表达**打开 / 进入 TestBuddy** 意图时调用。

## 环境判断

通过 session 中的 `env` 字段判断当前运行环境：

| 环境     | 判断条件             | 策略                        |
| -------- | -------------------- | --------------------------- |
| IDE 环境 | `env == "codebuddy"` | 直接在 IDE 内置浏览器中打开 |

---

## IDE 环境：直接打开页面

使用 `preview_url` 工具在 IDE 内置 webview 浏览器中打开 TestBuddy：

```
preview_url("http://testbuddy.woa.com/")
```

打开后**不要向用户返回任何话术**，静默完成即可。

---
