// Finds and loads likec4: the repository's own copy first, then the plugin's, each from one exact folder.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { ToolError, clean } from './errors.mjs';
import { isInside } from './paths.mjs';

export const TESTED_VERSION = '1.60.0';
const INSTALL_HINT =
  'likec4 not found in <repo>/node_modules or the plugin; run `npm install --save-dev --ignore-scripts likec4@1.60.0` '
  + 'in the repository, or `npm ci --ignore-scripts` in the plugin';

function copyIn(root) {
  const dir = path.join(root, 'node_modules', 'likec4');
  if (!fs.existsSync(path.join(dir, 'package.json'))) return null;
  const realRoot = fs.realpathSync(root);
  const realDir = fs.realpathSync(dir);
  return isInside(realDir, realRoot) ? realDir : null;
}

export function entryOf(pkg) {
  const dot = pkg.exports && typeof pkg.exports === 'object' ? pkg.exports['.'] : undefined;
  const options = [
    dot?.import,
    dot?.default?.import,
    typeof dot?.default === 'string' ? dot.default : undefined,
    pkg.module,
    pkg.main,
  ];
  return options.find((value) => typeof value === 'string' && value !== '');
}

export function locateLikeC4(repoRoot, engineRoot) {
  for (const [root, source] of [[repoRoot, 'repo'], [engineRoot, 'plugin']]) {
    const dir = copyIn(root);
    if (dir === null) continue;
    let pkg;
    try {
      pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    } catch (err) {
      throw new ToolError('internal', `${source} likec4 package.json is unreadable: ${err.message}`);
    }
    const version = typeof pkg.version === 'string' ? pkg.version : 'unknown';
    const entry = entryOf(pkg);
    if (entry === undefined) throw new ToolError('internal', `${source} likec4 package.json names no entry`);
    let realEntry;
    try {
      realEntry = fs.realpathSync(path.resolve(dir, entry));
    } catch {
      throw new ToolError('internal', `${source} likec4 entry ${entry} does not exist`);
    }
    if (!isInside(realEntry, dir)) throw new ToolError('internal', `${source} likec4 entry lies outside its folder`);
    return { dir, version, source, entry: realEntry };
  }
  throw new ToolError('likec4-missing', INSTALL_HINT);
}

export async function importLikeC4(located) {
  const mod = await import(pathToFileURL(located.entry).href);
  if (typeof mod.LikeC4?.fromWorkspace !== 'function') {
    throw new ToolError('internal', `likec4 ${located.version} from ${located.source} has no LikeC4.fromWorkspace`);
  }
  return mod.LikeC4;
}

export function versionNote(located) {
  return located.version === TESTED_VERSION
    ? null
    : `note: likec4 ${clean(located.version)} from ${located.source}; tested with ${TESTED_VERSION}`;
}
