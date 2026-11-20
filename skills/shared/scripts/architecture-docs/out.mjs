// The docs tool's output folder: where it may be (write rule 1) and what it may hold (write rule 2).
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';
import { isInside } from '../architecture-delta/paths.mjs';

export const GENERATED = 'generated';
const outError = (detail) => new ToolError('out-error', detail);
const shown = (root, target) => path.relative(root, target).split(path.sep).join('/');

function lstatOrNull(target) {
  try {
    return fs.lstatSync(target);
  } catch (err) {
    if (err?.code === 'ENOENT') return null;
    throw err;
  }
}

// Spec, write rule 1, through real paths: every existing part of the path below `--repo` is checked with `lstat`, then
// the checks run on the native real path (which settles Windows short names and letter case), and that path is returned.
export function resolveOut(repo, modelDir, value) {
  const lexical = value === null ? path.join(modelDir, GENERATED) : path.resolve(repo, value);
  // A lexical refusal first. It fails closed: it may also refuse an absolute short-name or other-case spelling of a
  // folder that is inside the repository. The real-path checks below decide everything else.
  if (!isInside(lexical, repo)) throw outError('--out lies outside --repo');
  let current = repo;
  let deepest = repo;
  const rest = [];
  for (const part of path.relative(repo, lexical).split(path.sep).filter((item) => item !== '')) {
    if (rest.length > 0) {
      rest.push(part);
      continue;
    }
    current = path.join(current, part);
    const stat = lstatOrNull(current);
    if (stat === null) {
      rest.push(part);
      continue;
    }
    if (stat.isSymbolicLink()) throw outError(`--out passes through a link: ${shown(repo, current)}`);
    if (!stat.isDirectory()) {
      if (current === lexical) throw outError('--out is not a folder');
      throw outError(`--out passes through a file: ${shown(repo, current)}`);
    }
    deepest = current;
  }
  const real = path.join(fs.realpathSync.native(deepest), ...rest);
  const repoReal = fs.realpathSync.native(repo);
  const modelReal = fs.existsSync(modelDir) ? fs.realpathSync.native(modelDir) : modelDir;
  if (!isInside(real, repoReal)) throw outError('--out lies outside --repo');
  if (isInside(modelReal, real)) throw outError('--out must not hold the model folder');
  // Spec: inside the model folder only its `generated` folder, matched in any case as the model walk matches it.
  if (isInside(real, modelReal) && path.relative(modelReal, real).toLowerCase() !== GENERATED) {
    throw outError(`--out inside the model folder must be its ${GENERATED} folder`);
  }
  return real;
}
