#!/usr/bin/env node
import { createRequire as __cb_createRequire } from 'node:module';
import { fileURLToPath as __cb_fileURLToPath } from 'node:url';
import { dirname as __cb_dirname } from 'node:path';
const require = __cb_createRequire(import.meta.url);
const __filename = __cb_fileURLToPath(import.meta.url);
const __dirname = __cb_dirname(__filename);

import{existsSync as t}from"node:fs";import{dirname as o,resolve as n}from"node:path";import{fileURLToPath as i}from"node:url";var c=o(i(import.meta.url)),s=n(c,"./server.mjs"),p="http://127.0.0.1:39099/mcp";function m(e,r){/^https?:\/\//i.test(e)||(console.error(`[sheetagent] ${r} \u5FC5\u987B\u662F http(s):// \u5F00\u5934\u7684 URL\uFF0C\u5B9E\u9645\u4E3A "${e}"\u3002`),process.exit(1))}function a(){if((process.env.SHEET_API_MODE??"local").toLowerCase()!=="local")return;let e=process.env.TENCENT_DOCS_LOCAL_MCP?.trim()||"",r=e||p;m(r,e?"TENCENT_DOCS_LOCAL_MCP":"\u9ED8\u8BA4\u672C\u5730 MCP URL"),process.env.SHEET_LOCAL_UPSTREAM_URL=r}function l(){let[e,r]=process.versions.node.split(".").map(Number);e>20||e===20&&r>=6||(console.error(`[sheetagent] Node.js v${process.versions.node} \u8FC7\u4F4E\uFF0C\u9700\u8981 >= 20.6\u3002`),process.exit(1))}function L(){t(s)||(console.error("[sheetagent] \u627E\u4E0D\u5230 server.mjs\u3002\n  \u8BF7\u786E\u8BA4\u63D2\u4EF6\u5DF2\u6B63\u786E\u6784\u5EFA\u3002\n  \u5F00\u53D1\u8005\u672C\u5730\u6784\u5EFA\uFF1A\u5728\u4ED3\u5E93\u6839\u76EE\u5F55\u6267\u884C `npm install && npm run build`"),process.exit(1))}a();l();L();await import(s);
