// Path containment for the architecture delta tool.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from './errors.mjs';

export function isInside(child, parent) {
  const rel = path.relative(parent, child);
  return rel === '' || (rel.split(path.sep)[0] !== '..' && !path.isAbsolute(rel));
}

export function realRepo(repo) {
  let stat;
  try {
    stat = fs.statSync(repo);
  } catch {
    throw new ToolError('bad-input', `--repo not found: ${repo}`);
  }
  if (!stat.isDirectory()) throw new ToolError('bad-input', `--repo is not a directory: ${repo}`);
  return fs.realpathSync(repo);
}

export function resolveInside(root, value, flag) {
  const lexical = path.resolve(root, value);
  if (!fs.existsSync(lexical)) {
    if (!isInside(lexical, root)) throw new ToolError('outside-repo', `${flag} lies outside --repo`);
    return { path: lexical, exists: false };
  }
  const real = fs.realpathSync(lexical);
  if (!isInside(real, root)) throw new ToolError('outside-repo', `${flag} resolves outside --repo`);
  return { path: real, exists: true };
}
