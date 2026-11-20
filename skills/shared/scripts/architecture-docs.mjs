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

// A failure reported earlier (a timer or a promise) stops the build before it writes. The folder is resolved and
// listed again right before writing, so the write works from what the folder holds now.
function runBuild(locate, files, state, tick) {
  const stopped = { output: '', exitCode: 2 };
  if (state.failed()) return stopped;
  const outDir = locate();
  const listed = listOut(outDir, tick);
  if (state.failed()) return stopped;
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
  // As in the writer: a file whose name differs from a produced one only in letter case is not `extra`.
  const keep = new Set(produced.map((rel) => rel.toLowerCase()));
  for (const rel of listed.files) if (!keep.has(rel.toLowerCase())) lines.push(['extra', rel]);
  lines.sort((x, y) => cmp(x[1], y[1]));
  const count = (word) => lines.filter((line) => line[0] === word).length;
  const output = lines.map(([word, rel]) => `${word} ${clean(rel)}\n`).join('')
    + `${count('missing')} missing, ${count('changed')} changed, ${count('extra')} extra\n`;
  return { output, exitCode: lines.length > 0 ? 1 : 0 };
}

async function main(argv, state) {
  const args = parseArgs(argv);
  const deadline = startDeadline(args.timeout);
  // Spec: the output folder is checked (write rules 1 and 2) before the model loads.
  const repo = realRepo(args.repo);
  const locate = () => resolveOut(repo, resolveInside(repo, args.model, '--model').path, args.out);
  const outDir = locate();
  const listed = listOut(outDir, deadline.check);
  deadline.check();
  const loaded = await loadRepoModel(args, deadline);
  const gap = readGap(loaded, args.gap);
  deadline.check();
  const files = buildFiles(loaded.model, loaded.records, gap, deadline.check);
  checkLimits(files);
  const result = args.command === 'build'
    ? runBuild(locate, files, state, deadline.check)
    : runCheck(outDir, files, listed);
  deadline.stop();
  return result;
}

runCli(main);
