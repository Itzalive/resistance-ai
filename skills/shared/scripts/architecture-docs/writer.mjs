// The only module of the docs tool that changes files: it writes, replaces and deletes inside the output folder (write rule 3).
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';
import { FOLDERS, TEMP_PREFIX } from './out.mjs';

function attempt(what, rel, action) {
  try {
    return action();
  } catch (err) {
    throw new ToolError('out-error', `could not ${what} ${rel}: ${err?.code ?? err?.message ?? String(err)}`);
  }
}

// Spec, write rule 3: every file of `files` ({ path with '/': text }) is written to a temporary name and renamed into
// place (left-over temporary files are deleted first); then the listed marked files no longer produced are deleted; then named
// folders left empty are removed, deepest first. `listed` is `listOut`'s result. Returns the counts.
export function writeOutput(outDir, files, listed) {
  attempt('create', '.', () => fs.mkdirSync(outDir, { recursive: true }));
  // Left-over temporary files go first, so a new temporary name can never meet an old one.
  for (const rel of listed.temps) attempt('delete', rel, () => fs.unlinkSync(path.join(outDir, rel)));
  const names = Object.keys(files).sort();
  names.forEach((rel, index) => {
    const final = path.join(outDir, rel);
    const temp = path.join(path.dirname(final), `${TEMP_PREFIX}${process.pid}-${index}`);
    attempt('create', path.posix.dirname(rel), () => fs.mkdirSync(path.dirname(final), { recursive: true }));
    // `wx`: a temporary file that appeared since the listing is never overwritten.
    attempt('write', rel, () => fs.writeFileSync(temp, files[rel], { encoding: 'utf8', flag: 'wx' }));
    attempt('replace', rel, () => fs.renameSync(temp, final));
  });
  // A listed file whose name differs from a produced one only in letter case may be that file on a case-insensitive
  // file system, so it is never stale.
  const produced = new Set(names.map((rel) => rel.toLowerCase()));
  const stale = listed.files.filter((rel) => !produced.has(rel.toLowerCase()));
  for (const rel of stale) attempt('delete', rel, () => fs.unlinkSync(path.join(outDir, rel)));
  for (const folder of [...FOLDERS].sort((x, y) => y.split('/').length - x.split('/').length)) {
    const full = path.join(outDir, folder);
    if (fs.existsSync(full) && fs.readdirSync(full).length === 0) attempt('remove', folder, () => fs.rmdirSync(full));
  }
  return { wrote: names.length, removed: stale.length };
}
