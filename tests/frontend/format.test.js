import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  basisLabel,
  clampInt,
  formatHour,
  formatTimeRange,
  impactChips,
  localHour,
  pollutantName,
} from '../../static/js/utils/format.js';

test('formatHour uses 12-hour labels', () => {
  assert.equal(formatHour(0), '12 am');
  assert.equal(formatHour(9), '9 am');
  assert.equal(formatHour(12), '12 pm');
  assert.equal(formatHour(14), '2 pm');
  assert.equal(formatHour(24), '12 am');
});

test('localHour reads the location time without converting time zones', () => {
  assert.equal(localHour('2026-11-25T14:00:00+05:30'), 14);
  assert.equal(localHour('garbage'), null);
});

test('formatTimeRange', () => {
  assert.equal(formatTimeRange('2026-11-25T14:00:00+05:30', '2026-11-25T16:00:00+05:30'), '2 pm – 4 pm');
  assert.equal(formatTimeRange('bad', 'bad'), '');
});

test('impactChips lists numbers and notes', () => {
  assert.deepEqual(
    impactChips({ exposure_reduction_pct: 35, co2_kg_saved_per_day: 2.8, note: 'Cleaner air', basis: 'computed' }),
    ['Up to 35% less pollution breathed', 'Saves 2.8 kg CO₂ a day', 'Cleaner air'],
  );
});

test('impactChips skips zero and missing values', () => {
  assert.deepEqual(impactChips({ exposure_reduction_pct: 0, co2_kg_saved_per_day: null, basis: 'estimated' }), []);
  assert.deepEqual(impactChips(null), []);
});

test('basisLabel', () => {
  assert.match(basisLabel('computed'), /forecast/);
  assert.match(basisLabel('estimated'), /Estimate/);
});

test('pollutantName', () => {
  assert.match(pollutantName('pm2_5'), /PM2\.5/);
  assert.equal(pollutantName('so2'), 'so2');
});

test('clampInt', () => {
  assert.equal(clampInt('30', 0, 240, 0), 30);
  assert.equal(clampInt('999', 0, 240, 0), 240);
  assert.equal(clampInt('-5', 0, 240, 0), 0);
  assert.equal(clampInt('abc', 0, 240, 7), 7);
});
