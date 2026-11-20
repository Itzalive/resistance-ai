// Shared start of the architecture tools: the deadline, the model and records load, optional input files, and the run wrapper.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ToolError, errorLines } from './errors.mjs';
import { locateLikeC4, importLikeC4, versionNote } from './likec4.mjs';
import { walkModelDir, checkSpecCopy } from './walk.mjs';
import { loadModel } from './model.mjs';
import { readRecords } from './records.mjs';
import { realRepo, resolveInside } from './paths.mjs';
import { readJson } from './inputs.mjs';

const LIB_DIR = path.dirname(fileURLToPath(import.meta.url));
const ENGINE_ROOT = path.resolve(LIB_DIR, '..', '..', '..', '..');
const SHIPPED_SPEC = path.resolve(LIB_DIR, '..', '..', 'architecture', 'c4.c4');

export function startDeadline(seconds) {
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

export async function loadRepoModel(args, deadline) {
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
  // Spec (records): validated right after the model loads, before any other input is read.
  const records = readRecords(model.path, loaded.elements.map((element) => element.id), deadline.check,
    loaded.capabilities.map((capability) => capability.name));
  return { repo, modelDir: model.path, located, model: loaded, records };
}

// Spec, Errors: a missing input file is `bad-input`; only the default gap file may be absent.
export function readOptional(repo, value, fallback, flag, parse) {
  const target = resolveInside(repo, value ?? fallback, flag);
  if (!target.exists) {
    if (value !== null) throw new ToolError('bad-input', `${flag} file not found`);
    return null;
  }
  return parse(readJson(target.path, flag));
}

// Spec, Errors: any failure, including one thrown later from a timer or a promise and a failed
// stdout write, is exit 2; the first one is reported and nothing after it can set another code.
// `main(argv, { failed })` returns { output, exitCode }; the output is written only when nothing has failed.
// `failed()` tells `main` whether a failure has been reported already, so it can stop before changing anything.
export function runCli(main) {
  let failed = false;
  const fail = (err) => {
    if (failed) return;
    failed = true;
    const error = err instanceof ToolError ? err : new ToolError('internal', err?.message ?? String(err));
    process.exitCode = 2;
    process.stderr.write(`${errorLines(error).join('\n')}\n`);
  };
  process.on('uncaughtException', fail);
  process.on('unhandledRejection', fail);
  process.stdout.on('error', fail);
  main(process.argv.slice(2), { failed: () => failed })
    .then((result) => {
      if (failed) return;
      process.stdout.write(result.output);
      process.exitCode = result.exitCode;
    })
    .catch(fail);
}
