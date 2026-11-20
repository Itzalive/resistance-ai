#!/usr/bin/env node
// Architecture delta: compares a LikeC4 C4 model with a repository's code dependencies.
// Reads files only; never writes a file or runs another program.
import path from 'node:path';
import { ToolError } from './architecture-delta/errors.mjs';
import { parseArgs } from './architecture-delta/args.mjs';
import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';
import { resolveInside } from './architecture-delta/paths.mjs';
import { readJson, parseDeps, parseGap, parseShards } from './architecture-delta/inputs.mjs';
import { compare } from './architecture-delta/match.mjs';
import { exportJson, checkJson, checkText } from './architecture-delta/report.mjs';

async function runCheck(args, deadline, loaded) {
  const { repo, modelDir, located, model } = loaded;
  const ids = model.elements.map((element) => element.id);
  const deps = resolveInside(repo, args.deps, '--deps');
  if (!deps.exists) throw new ToolError('bad-input', '--deps file not found');
  const edges = parseDeps(readJson(deps.path, '--deps'));
  deadline.check();
  const gap = readOptional(repo, args.gap, path.join(modelDir, 'known-gap.json'), '--gap', (data) => parseGap(data, ids)) ?? [];
  deadline.check();
  const shards = args.shards === null ? null : readOptional(repo, args.shards, null, '--shards', (data) => parseShards(data, ids));
  deadline.check();
  if (args.scope !== null) {
    const known = new Set(ids);
    const unknown = args.scope.filter((id) => !known.has(id));
    if (unknown.length > 0) throw new ToolError('unknown-scope', unknown.map((id) => `${id} is not a model element`));
  }
  const result = compare(model, edges, { separator: args.separator, gap, scope: args.scope, shards, tick: deadline.check });
  const report = checkJson(result, located);
  const output = args.format === 'json' ? `${JSON.stringify(report, null, 2)}\n` : checkText(report);
  return { output, exitCode: result.exitCode };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  const loaded = await loadRepoModel(args, deadline);
  const result = args.command === 'export'
    ? { output: `${JSON.stringify(exportJson(loaded.model, loaded.records), null, 2)}\n`, exitCode: 0 }
    : await runCheck(args, deadline, loaded);
  deadline.stop();
  return result;
}

runCli(main);
