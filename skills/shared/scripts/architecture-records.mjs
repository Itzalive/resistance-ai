#!/usr/bin/env node
// Architecture records: drafts the change file of a defining-architecture run, or proposes the relationships a
// baseline leaves out of each cycle.
// Changes files only through architecture-records/writer.mjs; never runs another program or uses the network.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError, clean } from './architecture-delta/errors.mjs';
import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';
import { resolveInside, isInside } from './architecture-delta/paths.mjs';
import { readJson, parseDeps, parseGap } from './architecture-delta/inputs.mjs';
import { findCycles, cyclesText } from './architecture-records/cycles.mjs';
import { exportJson } from './architecture-delta/report.mjs';
import { runCheck } from './architecture-delta/check.mjs';
import { changeFileProblems, isRealDate } from './architecture-delta/records.mjs';
import { parseArgs } from './architecture-records/args.mjs';
import { buildChange, canonical, EMPTY_EXPORT } from './architecture-records/change.mjs';
import { writeChange } from './architecture-records/writer.mjs';

// The known-gap entries of a loaded model folder, read as the delta `check` reads them.
function readGap(loaded) {
  const ids = loaded.model.elements.map((element) => element.id);
  return readOptional(loaded.repo, null, path.join(loaded.modelDir, 'known-gap.json'), '--gap', (data) => parseGap(data, ids)) ?? [];
}

// Spec, `change`: --before resolves inside --repo (otherwise `outside-repo`), exists, and is apart from the model folder.
function locateBefore(repo, modelDir, value) {
  const before = resolveInside(repo, value, '--before');
  if (!before.exists || !fs.statSync(before.path).isDirectory()) throw new ToolError('bad-input', '--before directory not found');
  if (isInside(before.path, modelDir) || isInside(modelDir, before.path)) {
    throw new ToolError('bad-input', '--before must not be, contain or lie inside the model folder');
  }
  return before.path;
}

async function runChange(args, deadline) {
  const loaded = await loadRepoModel(args, deadline);
  const id = `${args.date}-${args.name}`;
  // The name is checked before it is used in any path.
  const nameProblems = changeFileProblems(`${id}.json`, {});
  if (nameProblems.length === 1 && nameProblems[0].endsWith(': -: not a valid file name here')) {
    throw new ToolError('bad-input', nameProblems);
  }
  const rel = `changes/${id}.json`;
  // The date is checked before `--compare` looks for the file, so a bad date is `bad-input`, never `missing`.
  if (!isRealDate(args.date)) throw new ToolError('bad-input', [`${clean(rel)}: date: not a real date`]);
  const existingPath = path.join(loaded.modelDir, 'changes', `${id}.json`);
  const existing = fs.existsSync(existingPath) ? readJson(existingPath, rel) : null;
  if (args.compare && existing === null) return { output: `missing ${clean(rel)}\n`, exitCode: 1 };
  const flags = {
    name: args.name,
    date: args.date,
    run: args.run,
    askedBy: args.askedBy ?? existing?.asked_by,
    summary: args.summary ?? existing?.summary,
    rejected: args.compare && args.rejected.length === 0 ? existing.rejected : args.rejected,
  };
  let before = EMPTY_EXPORT;
  let beforeGap = [];
  if (args.before !== null) {
    // The before copy goes through the same loader, so its load errors name `--model` and a LikeC4 version note prints
    // once per load.
    const prior = await loadRepoModel({ repo: loaded.repo, model: locateBefore(loaded.repo, loaded.modelDir, args.before) }, deadline);
    before = exportJson(prior.model, prior.records);
    beforeGap = readGap(prior);
  }
  deadline.check();
  const check = await runCheck({ deps: args.deps, gap: null, shards: null, scope: null, separator: args.separator, format: 'text' },
    deadline, loaded);
  const change = buildChange({ before, after: exportJson(loaded.model, loaded.records), beforeGap, afterGap: readGap(loaded), check, flags });
  const problems = changeFileProblems(`${id}.json`, change);
  if (problems.length > 0) throw new ToolError('bad-input', problems);
  if (args.compare) {
    const same = canonical(change) === canonical(existing);
    return { output: `${same ? 'same' : 'differs'} ${clean(rel)}\n`, exitCode: same ? 0 : 1 };
  }
  writeChange(loaded.modelDir, id, `${JSON.stringify(change, null, 2)}\n`);
  return { output: `wrote ${clean(rel)}\n`, exitCode: 0 };
}

async function runCycles(args, deadline) {
  const loaded = await loadRepoModel(args, deadline);
  readGap(loaded); // Spec, "The helper tool": loaded as the delta `check` loads it, so a bad entry stops the run.
  const deps = resolveInside(loaded.repo, args.deps, '--deps');
  if (!deps.exists) throw new ToolError('bad-input', '--deps file not found');
  const edges = parseDeps(readJson(deps.path, '--deps'));
  deadline.check();
  const result = findCycles(loaded.model, edges, args.separator, deadline.check);
  return { output: args.format === 'json' ? `${JSON.stringify(result, null, 2)}\n` : cyclesText(result), exitCode: 0 };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const result = args.command === 'change' ? await runChange(args, deadline) : await runCycles(args, deadline);
  deadline.stop();
  return result;
}

runCli(main);
