import assert from 'node:assert/strict';
import { test } from 'node:test';

import { parseInline, parseReply, splitInlineBullets } from '../../static/js/utils/markdown.js';

test('parseInline splits bold and removes stray marks', () => {
  assert.deepEqual(parseInline('**Get a purifier:** use it in `bedrooms` *daily*'), [
    { text: 'Get a purifier:', bold: true },
    { text: ' use it in bedrooms daily', bold: false },
  ]);
  assert.deepEqual(parseInline(''), []);
});

test('plain paragraphs are kept and blank lines split them', () => {
  assert.deepEqual(parseReply('First line\ncontinues here.\n\nSecond paragraph.'), [
    { type: 'p', spans: [{ text: 'First line continues here.', bold: false }] },
    { type: 'p', spans: [{ text: 'Second paragraph.', bold: false }] },
  ]);
});

test('bullet lists with bold labels', () => {
  const blocks = parseReply('Try these:\n* **Purifier:** run it.\n- **Mop:** wet clean.');
  assert.equal(blocks.length, 2);
  assert.equal(blocks[0].type, 'p');
  assert.equal(blocks[1].type, 'ul');
  assert.equal(blocks[1].items.length, 2);
  assert.deepEqual(blocks[1].items[0][0], { text: 'Purifier:', bold: true });
});

test('numbered lists become ordered lists', () => {
  const blocks = parseReply('1. Close windows\n2) Run the purifier');
  assert.equal(blocks[0].type, 'ol');
  assert.equal(blocks[0].items.length, 2);
});

test('a whole list squeezed onto one line is split into items', () => {
  const reply =
    'Here are some steps: * **Get a HEPA air purifier:** Use one. * **Avoid indoor smoke:** No candles. * **Mop:** Less dust.';
  const blocks = parseReply(reply);
  assert.equal(blocks[0].type, 'p');
  assert.equal(blocks[0].spans[0].text, 'Here are some steps:');
  assert.equal(blocks[1].type, 'ul');
  assert.equal(blocks[1].items.length, 3);
  assert.deepEqual(blocks[1].items[1][0], { text: 'Avoid indoor smoke:', bold: true });
});

test('a single inline asterisk is not treated as a list', () => {
  assert.equal(splitInlineBullets('Rate it 5 * stars'), 'Rate it 5 * stars');
});

test('headings are shown as plain paragraphs and empty input gives nothing', () => {
  assert.deepEqual(parseReply('## Tips'), [{ type: 'p', spans: [{ text: 'Tips', bold: false }] }]);
  assert.deepEqual(parseReply(''), []);
  assert.deepEqual(parseReply(undefined), []);
});
