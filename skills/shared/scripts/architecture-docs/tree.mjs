// The document tree the writers turn into Markdown and HTML. Strings are model text; links point at documents.
// Inline parts (in paragraphs, list items and table cells) are strings or links.
export const heading = (level, text) => ({ type: 'heading', level, text });
export const paragraph = (...parts) => ({ type: 'paragraph', parts });
export const list = (items) => ({ type: 'list', items });
export const table = (header, rows) => ({ type: 'table', header, rows });
export const code = (text) => ({ type: 'code', text });
export const diagram = (text) => ({ type: 'diagram', text });
// Named docLink: the safety test forbids any call named like fs.link outside the writer.
export const docLink = (text, href) => ({ type: 'link', text, href });
export const doc = (title, blocks) => ({ title, blocks });

// A link target: a relative path to a document, made only of safe characters.
export const SAFE_HREF = /^[A-Za-z0-9._/-]+$/;
