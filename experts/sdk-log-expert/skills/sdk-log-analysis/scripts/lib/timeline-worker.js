import { parentPort, workerData } from 'node:worker_threads';
import { buildTimelineFromEntries } from './timeline.js';

try {
  const result = buildTimelineFromEntries(workerData.entries, workerData.options);
  parentPort.postMessage({ ok: true, events: result.events, sdk: result.sdk, logType: result.logType });
} catch (error) {
  parentPort.postMessage({ ok: false, error: error.message || String(error) });
}
