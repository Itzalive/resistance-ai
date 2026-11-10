// Path containment for the architecture delta tool.
import path from 'node:path';

export function isInside(child, parent) {
  const rel = path.relative(parent, child);
  return rel === '' || (rel.split(path.sep)[0] !== '..' && !path.isAbsolute(rel));
}
