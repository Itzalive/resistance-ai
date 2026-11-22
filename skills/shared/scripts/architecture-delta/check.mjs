// The delta `check` run: compares the code's dependency edges with a loaded model. Shared by the delta tool and
// the records tool, so both print exactly the same report.
import path from 'node:path';
import { ToolError } from './errors.mjs';
import { readOptional } from './load.mjs';
import { resolveInside } from './paths.mjs';
import { readJson, parseDeps, parseGap, parseShards } from './inputs.mjs';
import { compare } from './match.mjs';
import { checkJson, checkText } from './report.mjs';

export async function runCheck(args, deadline, loaded) {
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
