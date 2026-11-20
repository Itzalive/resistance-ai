// Mermaid diagram text. Node ids are generated (n1, n2, ... in the order given); every label is entity-encoded, so model
// text cannot close a quote, end a statement or open a directive. Mermaid decodes `#<code>;` before it parses.
export const ARROW_LIMIT = 80;
const SAFE = /^[A-Za-z0-9 .'/_-]$/;

export function label(text) {
  return Array.from(String(text).replace(/\n/g, ' '))
    .map((ch) => (SAFE.test(ch) ? ch : `#${ch.codePointAt(0)};`))
    .join('');
}

// A left-to-right flowchart. `nodes`: { id, text }; `arrows`: { from, to, dashed, text } by node id, drawn solid or
// dashed, with the text as a label when it is not empty. Returns null when there are more than ARROW_LIMIT arrows.
export function flowchart(nodes, arrows) {
  if (arrows.length > ARROW_LIMIT) return null;
  const ids = new Map(nodes.map((node, index) => [node.id, `n${index + 1}`]));
  const lines = ['flowchart LR', ...nodes.map((node) => `  ${ids.get(node.id)}["${label(node.text)}"]`)];
  for (const arrow of arrows) {
    const from = ids.get(arrow.from);
    const to = ids.get(arrow.to);
    if (from === undefined || to === undefined) throw new Error(`arrow ${arrow.from} -> ${arrow.to} has an end that is not a node`);
    const text = arrow.text ? `|"${label(arrow.text)}"|` : '';
    lines.push(`  ${from} ${arrow.dashed ? '-.->' : '-->'}${text} ${to}`);
  }
  return lines.join('\n');
}
