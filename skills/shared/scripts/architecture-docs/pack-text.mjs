// Pack text (spec, Writers, Pack text): the pack is read raw by agents, so ids and text are written as `export` gives
// them, unescaped. The line separators U+2028 and U+2029 count as line feeds. A one-line field loses its line feeds; in
// a multi-line field every line is kept, and a line starting with `#`, `---`, three backticks or `~~~` gets a leading
// `\`, so record text cannot start a heading, a separator or a code fence.
import { MARKER } from './out.mjs';

const LINE_BREAK = /[\n\u2028\u2029]/g;
export const oneLine = (text) => String(text).replace(LINE_BREAK, ' ');

const GUARDED = /^(#|---|```|~~~)/;
export const multiLine = (text) => String(text).replace(LINE_BREAK, '\n').split('\n')
  .map((line) => (GUARDED.test(line) ? `\\${line}` : line)).join('\n');

// Spec, Pack layout: the marker line, `# <title>`, then the file's parts (headings, paragraphs and blocks of lines),
// one blank line apart, ending in one line feed.
export function packFile(title, parts) {
  return `${[MARKER, `# ${oneLine(title)}`, ...parts].join('\n\n')}\n`;
}
