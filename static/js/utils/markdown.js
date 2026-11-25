/**
 * Tiny, safe parser for the Markdown subset the chat AI may use: paragraphs, bullet and
 * numbered lists, and **bold**. It returns plain data (no HTML), so rendering can use
 * textContent only. Anything else (headings, italics, code marks) is shown as plain text.
 * @module utils/markdown
 */

/**
 * @typedef {{text: string, bold: boolean}} Span
 * @typedef {{type: 'p', spans: Span[]} | {type: 'ul'|'ol', items: Span[][]}} Block
 */

const BULLET = /^\s*[-*•]\s+(.*)$/;
const NUMBERED = /^\s*\d+[.)]\s+(.*)$/;
const HEADING = /^\s*#{1,6}\s+/;
const INLINE_BULLETS = /\s[*•]\s+(?=\S)/g;
const MIN_INLINE_BULLETS = 2;

/**
 * Some replies put a whole list on one line ("steps: * one * two"). Split those onto lines.
 * @param {string} text
 * @returns {string}
 */
export function splitInlineBullets(text) {
  if (text.includes('\n')) return text;
  const matches = text.match(INLINE_BULLETS) ?? [];
  return matches.length >= MIN_INLINE_BULLETS ? text.replace(INLINE_BULLETS, '\n* ') : text;
}

/**
 * Split a line into plain and bold spans. Stray *, _ and ` marks are removed.
 * @param {string} line
 * @returns {Span[]}
 */
export function parseInline(line) {
  const spans = [];
  const parts = line.split(/\*\*(.+?)\*\*/g);
  parts.forEach((part, i) => {
    const text = part.replace(/[*_`]/g, '');
    if (text) spans.push({ text, bold: i % 2 === 1 });
  });
  return spans;
}

/**
 * Parse a chat reply into blocks.
 * @param {string} raw
 * @returns {Block[]}
 */
export function parseReply(raw) {
  const lines = splitInlineBullets(String(raw ?? '').replace(/\r\n?/g, '\n')).split('\n');
  /** @type {Block[]} */
  const blocks = [];
  /** @type {string[]} */
  let paragraph = [];

  const flushParagraph = () => {
    if (paragraph.length) blocks.push({ type: 'p', spans: parseInline(paragraph.join(' ')) });
    paragraph = [];
  };

  /** @param {'ul'|'ol'} type @param {string} text */
  const addItem = (type, text) => {
    flushParagraph();
    const last = blocks[blocks.length - 1];
    const spans = parseInline(text);
    if (last && last.type === type) last.items.push(spans);
    else blocks.push({ type, items: [spans] });
  };

  for (const rawLine of lines) {
    const line = rawLine.replace(HEADING, '').trim();
    const bullet = BULLET.exec(line);
    const numbered = NUMBERED.exec(line);
    if (!line) flushParagraph();
    else if (bullet) addItem('ul', bullet[1]);
    else if (numbered) addItem('ol', numbered[1]);
    else paragraph.push(line);
  }
  flushParagraph();
  return blocks.filter((b) => (b.type === 'p' ? b.spans.length : b.items.length));
}
