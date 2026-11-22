#!/usr/bin/env node
// Architecture delta: compares a LikeC4 C4 model with a repository's code dependencies.
// Reads files only; never writes a file or runs another program.
import { parseArgs } from './architecture-delta/args.mjs';
import { startDeadline, loadRepoModel, runCli } from './architecture-delta/load.mjs';
import { runCheck } from './architecture-delta/check.mjs';
import { exportJson } from './architecture-delta/report.mjs';

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
