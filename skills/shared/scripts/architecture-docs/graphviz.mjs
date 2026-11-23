// Finds and loads Graphviz for the SVG diagrams: the repository's own copy first, then the plugin's, each from one
// exact folder and only at the pinned version, because the SVG bytes `check` compares depend on it.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { ToolError, clean } from '../architecture-delta/errors.mjs';
import { isInside } from '../architecture-delta/paths.mjs';
import { entryOf } from '../architecture-delta/likec4.mjs';

export const GRAPHVIZ_VERSION = '1.29.2';
const NAME = '@hpcc-js/wasm-graphviz';
const ENGINE_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', '..', '..');
const INSTALL_HINT = `${NAME} ${GRAPHVIZ_VERSION} not found in <repo>/node_modules or the plugin; run `
  + `\`npm install --save-dev --ignore-scripts ${NAME}@${GRAPHVIZ_VERSION}\` in the repository, or \`npm ci --ignore-scripts\` in the plugin`;

// The package folder under `root`, by real path inside `root`, or null.
function copyIn(root) {
  const dir = path.join(root, 'node_modules', '@hpcc-js', 'wasm-graphviz');
  if (!fs.existsSync(path.join(dir, 'package.json'))) return null;
  const realDir = fs.realpathSync(dir);
  return isInside(realDir, fs.realpathSync(root)) ? realDir : null;
}

// `repoRoot` null looks in the plugin only.
export function locateGraphviz(repoRoot, engineRoot = ENGINE_ROOT) {
  const found = [];
  for (const [root, source] of [[repoRoot, 'repo'], [engineRoot, 'plugin']]) {
    if (root === null) continue;
    const dir = copyIn(root);
    if (dir === null) continue;
    let pkg;
    try {
      pkg = JSON.parse(fs.readFileSync(path.join(dir, 'package.json'), 'utf8'));
    } catch (err) {
      throw new ToolError('internal', `${source} ${NAME} package.json is unreadable: ${err.message}`);
    }
    const version = typeof pkg.version === 'string' ? pkg.version : 'unknown';
    if (version !== GRAPHVIZ_VERSION) {
      found.push(`${source} ${clean(version)}`);
      continue;
    }
    const entry = entryOf(pkg);
    if (entry === undefined) throw new ToolError('internal', `${source} ${NAME} package.json names no entry`);
    let realEntry;
    try {
      realEntry = fs.realpathSync(path.resolve(dir, entry));
    } catch {
      throw new ToolError('internal', `${source} ${NAME} entry ${entry} does not exist`);
    }
    if (!isInside(realEntry, dir)) throw new ToolError('internal', `${source} ${NAME} entry lies outside its folder`);
    return { dir, version, source, entry: realEntry };
  }
  throw new ToolError('graphviz-missing', found.length > 0 ? `${INSTALL_HINT} (found ${found.join(', ')})` : INSTALL_HINT);
}

export async function importGraphviz(located) {
  const mod = await import(pathToFileURL(located.entry).href);
  if (typeof mod.Graphviz?.load !== 'function') {
    throw new ToolError('internal', `${NAME} ${located.version} from ${located.source} has no Graphviz.load`);
  }
  return mod.Graphviz;
}
