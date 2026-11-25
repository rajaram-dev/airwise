import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  CATEGORY_META,
  categoryClass,
  categoryMeta,
  describeAqi,
  riskLabel,
} from '../../static/js/utils/aqi.js';

test('every API category has a label and icon', () => {
  const categories = ['good', 'moderate', 'unhealthy_sensitive', 'unhealthy', 'very_unhealthy', 'hazardous'];
  for (const category of categories) {
    const meta = categoryMeta(category);
    assert.ok(meta.label.length > 0);
    assert.ok(meta.icon.length > 0);
  }
  assert.equal(Object.keys(CATEGORY_META).length, categories.length);
});

test('unknown category falls back safely', () => {
  assert.equal(categoryMeta('__proto__').label, 'Unknown');
  assert.equal(categoryClass('bogus'), '');
});

test('categoryClass builds the CSS modifier', () => {
  assert.equal(categoryClass('very_unhealthy'), 'aqi--very_unhealthy');
});

test('describeAqi gives a screen-reader friendly sentence', () => {
  assert.equal(describeAqi(287, 'very_unhealthy'), 'Air quality index 287, Very Unhealthy');
});

test('riskLabel', () => {
  assert.equal(riskLabel('severe'), 'Severe risk');
  assert.equal(riskLabel('other'), 'Unknown risk');
});
