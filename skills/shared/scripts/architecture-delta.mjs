#!/usr/bin/env node
// Architecture delta: compares a LikeC4 C4 model with a repository's code dependencies.
// Reads files only; never writes a file or runs another program.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ToolError, errorLines } from './architecture-delta/errors.mjs';
import { parseArgs } from './architecture-delta/args.mjs';
import { locateLikeC4, importLikeC4, versionNote } from './architecture-delta/likec4.mjs';
import { walkModelDir, checkSpecCopy } from './architecture-delta/walk.mjs';
import { loadModel } from './architecture-delta/model.mjs';
import { realRepo, resolveInside } from './architecture-delta/paths.mjs';
import { exportJson } from './architecture-delta/report.mjs';

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = path.resolve(SCRIPT_DIR, '..', '..', '..');
const SHIPPED_SPEC = path.resolve(SCRIPT_DIR, '..', 'architecture', 'c4.c4');

function startDeadline(seconds) {
  const end = Date.now() + seconds * 1000;
  const message = `run exceeded --timeout ${seconds}s`;
  const timer = setTimeout(() => {
    process.stderr.write(`error: timeout: ${message}\n`);
    process.exit(2);
  }, seconds * 1000);
  timer.unref();
  return {
    check() {
      if (Date.now() >= end) throw new ToolError('timeout', message);
    },
    stop() {
      clearTimeout(timer);
    },
  };
}

async function loadRepoModel(args, deadline) {
  const repo = realRepo(args.repo);
  const model = resolveInside(repo, args.model, '--model');
  if (!model.exists || !fs.statSync(model.path).isDirectory()) throw new ToolError('bad-input', '--model directory not found');
  const located = locateLikeC4(repo, ENGINE_ROOT);
  const note = versionNote(located);
  if (note !== null) process.stderr.write(`${note}\n`);
  const LikeC4 = await importLikeC4(located);
  deadline.check();
  walkModelDir(model.path);
  checkSpecCopy(model.path, SHIPPED_SPEC);
  const loaded = await loadModel(LikeC4, model.path);
  deadline.check();
  return { repo, modelDir: model.path, located, model: loaded };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const { model } = await loadRepoModel(args, deadline);
  let output;
  let exitCode = 0;
  if (args.command === 'export') {
    output = `${JSON.stringify(exportJson(model), null, 2)}\n`;
  } else {
    throw new ToolError('internal', 'check is not available in this build');
  }
  deadline.stop();
  process.stdout.write(output);
  process.exitCode = exitCode;
}

main(process.argv.slice(2)).catch((err) => {
  const error = err instanceof ToolError ? err : new ToolError('internal', err?.message ?? String(err));
  process.stderr.write(`${errorLines(error).join('\n')}\n`);
  process.exitCode = 2;
});
