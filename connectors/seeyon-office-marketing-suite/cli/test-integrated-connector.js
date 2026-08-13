#!/usr/bin/env node
"use strict";

/** Seeyon 整合连接器结构离线测试。by AI.Coding */

const assert = require("assert");
const fs = require("fs");
const path = require("path");

/** 校验连接器元数据和两份内置 Skill 均可被发现。 */
function testIntegratedConnector() {
  const connectorHome = path.resolve(__dirname, "..");
  const metadata = JSON.parse(fs.readFileSync(path.join(connectorHome, "connector-meta.json"), "utf8"));
  const cliConfig = JSON.parse(fs.readFileSync(path.join(connectorHome, "cli.json"), "utf8"));

  assert.strictEqual(metadata.id, "seeyon-office-marketing-suite");
  assert.match(cliConfig.env.SEEYON_CONNECTOR_HOME, /seeyon-office-marketing-suite$/);

  // 两份 Skill 保持独立入口，避免合并后发生脚本和模块命名冲突。
  const skillEntries = [
    "skills/seeyon-collaborative-office-loop-skill/SKILL.md",
    "skills/seeyon-marketing-data-analysis-skill/SKILL.md",
  ];
  for (const relativePath of skillEntries) {
    assert.strictEqual(fs.existsSync(path.join(connectorHome, relativePath)), true, relativePath);
  }
}

testIntegratedConnector();
process.stdout.write("Seeyon integrated connector offline tests passed.\n");
