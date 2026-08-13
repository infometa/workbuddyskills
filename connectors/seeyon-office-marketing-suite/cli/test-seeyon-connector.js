#!/usr/bin/env node
"use strict";

/** Seeyon 连接器 CLI 的离线测试。by AI.Coding */

const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");

const cliPath = path.join(__dirname, "seeyon-connector.js");
const tempHome = fs.mkdtempSync(path.join(os.tmpdir(), "seeyon-connector-test-"));
process.env.HOME = tempHome;
process.env.USERPROFILE = tempHome;
process.env.SEEYON_CONNECTOR_HOME = path.resolve(__dirname, "..");
process.env.OA_BASE_URL = "http://oa.example.com/seeyon/main.do?method=login";

try {
  const moduleApi = require(cliPath);
  assert.strictEqual(
    moduleApi.normalizeServiceUrl("http://oa.example.com/seeyon/main.do?method=login"),
    "http://oa.example.com/seeyon",
  );
  assert.deepStrictEqual(moduleApi.deriveCandidateServiceUrls([
    "chrome://newtab/",
    "http://172.31.15.200/seeyon/main.do?method=login",
    "https://example.com/not-oa",
  ], {
    serviceUrl: "http://172.31.15.158/seeyon",
    serviceUrlLocked: false,
  }), ["http://172.31.15.200/seeyon", "http://172.31.15.158/seeyon"]);
  assert.deepStrictEqual(moduleApi.deriveCandidateServiceUrls([
    "http://172.31.15.200/seeyon/main.do?method=login",
  ], {
    serviceUrl: "http://172.31.15.158/seeyon",
    serviceUrlLocked: true,
  }), ["http://172.31.15.158/seeyon"]);

  process.env.OA_AUTH_USERNAME = "";
  process.env.OA_AUTH_PASSWORD = "";
  const forcedConfig = moduleApi.loadConfig();
  assert.strictEqual(forcedConfig.serviceUrlLocked, true);
  assert.strictEqual(moduleApi.hasEnvironmentCredentials(forcedConfig), false);
  process.env.OA_AUTH_USERNAME = "ducl";
  process.env.OA_AUTH_PASSWORD = "secret";
  assert.strictEqual(moduleApi.hasEnvironmentCredentials(moduleApi.loadConfig()), true);

  const storedSession = {
    serviceUrl: "http://oa.example.com/seeyon",
    username: "ducl",
    JSESSIONID: "test-session",
    route: "node-a",
    savedAt: Date.now(),
  };
  moduleApi.saveSession(storedSession);
  assert.deepStrictEqual(moduleApi.loadSession(), storedSession);

  const profileDir = path.join(os.tmpdir(), "seeyon-connector-cleanup-test");
  let cleanupOptions;
  assert.strictEqual(moduleApi.cleanupBrowserProfile(profileDir, {
    removeSync(target, options) {
      assert.strictEqual(target, profileDir);
      cleanupOptions = options;
    },
  }), true);
  assert.strictEqual(cleanupOptions.maxRetries, 10);
  assert.strictEqual(cleanupOptions.retryDelay, 200);

  let warning;
  assert.strictEqual(moduleApi.cleanupBrowserProfile(profileDir, {
    removeSync() {
      const error = new Error("locked");
      error.code = "EBUSY";
      throw error;
    },
    warn(message) {
      warning = message;
    },
  }), false);
  assert.match(warning, /EBUSY/);

  process.stdout.write("Seeyon connector CLI offline tests passed.\n");
} finally {
  fs.rmSync(tempHome, { recursive: true, force: true });
}
