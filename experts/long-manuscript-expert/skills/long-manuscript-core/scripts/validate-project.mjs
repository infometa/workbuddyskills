import fs from 'node:fs';
import { validateProject } from './project-state.mjs';

try {
  const inputPath = process.argv[2];
  const project = JSON.parse(inputPath ? fs.readFileSync(inputPath, 'utf8') : fs.readFileSync(0, 'utf8'));
  const result = validateProject(project);
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (!result.ok) process.exitCode = 1;
} catch (error) {
  process.stderr.write(`${JSON.stringify({ ok: false, issues: [error.message] })}\n`);
  process.exitCode = 1;
}
