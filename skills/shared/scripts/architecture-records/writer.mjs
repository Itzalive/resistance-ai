// The only module of the records tool that changes files: it writes one change file into <model>/changes.
import fs from 'node:fs';
import path from 'node:path';
import { ToolError } from '../architecture-delta/errors.mjs';

// A temporary name the records reader ignores (it starts with `.`, records layout rule 7).
export const TEMP = /^\.architecture-records-[0-9]+-[0-9]+$/;
let counter = 0;

function attempt(what, rel, action) {
  try {
    return action();
  } catch (err) {
    if (err instanceof ToolError) throw err;
    throw new ToolError('out-error', `could not ${what} ${rel}: ${err?.code ?? err?.message ?? String(err)}`);
  }
}

// Spec, `change`: writes `changes/<id>.json` with `text` through a temporary file and a rename. An existing file of
// that id is replaced only when its `approved` is null (a draft); anything else is `out-error` and nothing changes.
// Left-over temporary files in `changes/` are removed first. `id` must already be a valid change id.
export function writeChange(modelDir, id, text) {
  const dir = path.join(modelDir, 'changes');
  const rel = `changes/${id}.json`;
  const target = path.join(dir, `${id}.json`);
  attempt('create', 'changes', () => fs.mkdirSync(dir, { recursive: true }));
  if (fs.existsSync(target)) {
    const current = attempt('read', rel, () => JSON.parse(fs.readFileSync(target, 'utf8')));
    if (current === null || typeof current !== 'object' || current.approved !== null) {
      throw new ToolError('out-error', `${rel} is not a draft and is never replaced`);
    }
  }
  for (const name of attempt('list', 'changes', () => fs.readdirSync(dir))) {
    if (TEMP.test(name)) attempt('remove', `changes/${name}`, () => fs.unlinkSync(path.join(dir, name)));
  }
  const temp = path.join(dir, `.architecture-records-${process.pid}-${counter}`);
  counter += 1;
  attempt('write', rel, () => fs.writeFileSync(temp, text, { encoding: 'utf8', flag: 'wx' }));
  attempt('replace', rel, () => fs.renameSync(temp, target));
}
