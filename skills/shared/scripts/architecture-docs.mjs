#!/usr/bin/env node
// Architecture docs: builds documents from the architecture model into one output folder, or reports which are stale.
// Changes files only inside its output folder (architecture-docs/writer.mjs); never runs another program or uses the network.
import fs from 'node:fs';
import path from 'node:path';
import { clean, cleanText } from './architecture-delta/errors.mjs';
import { realRepo, resolveInside } from './architecture-delta/paths.mjs';
import { parseGap } from './architecture-delta/inputs.mjs';
import { cmp } from './architecture-delta/report.mjs';
import { startDeadline, loadRepoModel, readOptional, runCli } from './architecture-delta/load.mjs';
import { parseArgs } from './architecture-docs/args.mjs';
import { resolveOut, listOut } from './architecture-docs/out.mjs';
import { writeOutput } from './architecture-docs/writer.mjs';
import { buildFiles, checkLimits } from './architecture-docs/build.mjs';

// Spec, The tool: known-gap entries are cleaned like `export` output before any document uses them.
function readGap(loaded, value) {
  const ids = loaded.model.elements.map((element) => element.id);
  const entries = readOptional(loaded.repo, value, path.join(loaded.modelDir, 'known-gap.json'), '--gap',
    (data) => parseGap(data, ids)) ?? [];
  return entries.map((entry) => ({
    from: clean(entry.from),
    to: clean(entry.to),
    reason: cleanText(entry.reason),
    close_by: entry.close_by === null ? null : cleanText(entry.close_by),
  }));
}

function runBuild(outDir, files, listed) {
  const { wrote, removed } = writeOutput(outDir, files, listed);
  return { output: `wrote ${wrote} files, removed ${removed}\n`, exitCode: 0 };
}

// Spec, `check`: compare after CRLF to LF; a marked file no longer produced is `extra`.
function runCheck(outDir, files, listed) {
  const produced = Object.keys(files);
  const lines = [];
  for (const rel of produced) {
    const full = path.join(outDir, rel);
    if (!fs.existsSync(full)) lines.push(['missing', rel]);
    else if (fs.readFileSync(full, 'utf8').replace(/\r\n/g, '\n') !== files[rel]) lines.push(['changed', rel]);
  }
  const keep = new Set(produced);
  for (const rel of listed.files) if (!keep.has(rel)) lines.push(['extra', rel]);
  lines.sort((x, y) => cmp(x[1], y[1]));
  const count = (word) => lines.filter((line) => line[0] === word).length;
  const output = lines.map(([word, rel]) => `${word} ${clean(rel)}\n`).join('')
    + `${count('missing')} missing, ${count('changed')} changed, ${count('extra')} extra\n`;
  return { output, exitCode: lines.length > 0 ? 1 : 0 };
}

async function main(argv) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  // Spec: the output folder is checked (write rules 1 and 2) before the model loads.
  const repo = realRepo(args.repo);
  const outDir = resolveOut(repo, resolveInside(repo, args.model, '--model').path, args.out);
  const listed = listOut(outDir);
  deadline.check();
  const loaded = await loadRepoModel(args, deadline);
  const gap = readGap(loaded, args.gap);
  deadline.check();
  const files = buildFiles(loaded.model, loaded.records, gap, deadline.check);
  checkLimits(files);
  const result = args.command === 'build' ? runBuild(outDir, files, listed) : runCheck(outDir, files, listed);
  deadline.stop();
  return result;
}

runCli(main);
