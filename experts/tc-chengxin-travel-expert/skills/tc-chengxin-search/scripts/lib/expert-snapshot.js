'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function snapshotId(snapshot) {
  return crypto.createHash('sha256').update(JSON.stringify({
    version: snapshot.version, capturedAt: snapshot.capturedAt,
    apiPath: snapshot.apiPath, requestParams: snapshot.requestParams, data: snapshot.data,
    ...(snapshot.intent ? { intent: snapshot.intent } : {})
  })).digest('hex');
}

function writeSnapshot(data, requestParams, apiPath) {
  const directory = path.resolve(process.env.CHENGXIN_WORKBUDDY_OUTPUT_DIR || path.join(process.cwd(), 'outputs'), '.expert-inputs');
  fs.mkdirSync(directory, { recursive: true, mode: 0o700 });
  const snapshot = { version: 1, capturedAt: new Date().toISOString(), apiPath, requestParams, data };
  if (['itinerary', 'selection'].includes(process.env.CHENGXIN_EXPERT_INTENT)) snapshot.intent = process.env.CHENGXIN_EXPERT_INTENT;
  snapshot.snapshotId = snapshotId(snapshot);
  const file = path.join(directory, `${snapshot.snapshotId}.json`);
  if (!fs.existsSync(file)) fs.writeFileSync(file, JSON.stringify(snapshot), { flag: 'wx', mode: 0o600 });
  return { type: 'workbuddy_expert_snapshot', stage: 'collected', snapshotFilePath: file, snapshotId: snapshot.snapshotId };
}

module.exports = { snapshotId, writeSnapshot };
