import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  basisLabel,
  clampInt,
  cleanName,
  formatClock,
  formatHour,
  formatTimeRange,
  greetingFor,
  impactChips,
  impactLine,
  localHour,
  pollutantName,
  profileSummary,
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
  assert.match(basisLabel('estimated'), /published data/);
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

test('impactLine splits headline and source', () => {
  assert.deepEqual(impactLine({ exposure_reduction_pct: 40, basis: 'computed' }), {
    headline: 'Up to 40% less pollution breathed',
    detail: 'from today\'s forecast',
  });
  assert.deepEqual(impactLine({ co2_kg_saved_per_day: 3.3, note: 'No traffic smog', basis: 'estimated' }), {
    headline: 'Saves 3.3 kg CO₂ a day',
    detail: 'No traffic smog · estimate from published data',
  });
  assert.equal(impactLine({ basis: 'estimated' }), null);
});

test('profileSummary builds the header chip text', () => {
  assert.equal(profileSummary(null), 'Set up your household');
  assert.equal(
    profileSummary({ household: { children: true, respiratory_condition: true }, commute_mode: 'two_wheeler' }),
    'Child · asthma · scooter',
  );
  assert.equal(profileSummary({ household: {}, commute_mode: 'wfh' }), 'Adults · home-based');
  assert.equal(profileSummary({ household: {}, commute_mode: 'unknown' }), 'Adults');
});


test('greetingFor', () => {
  assert.equal(greetingFor(8), 'Good morning');
  assert.equal(greetingFor(13), 'Good afternoon');
  assert.equal(greetingFor(20), 'Good evening');
});

test('formatClock keeps the location time', () => {
  assert.equal(formatClock('2026-11-25T09:15:00+05:30'), '9:15 am');
  assert.equal(formatClock('2026-11-25T21:05'), '9:05 pm');
  assert.equal(formatClock('bad'), '');
});

test('cleanName trims and limits length', () => {
  assert.equal(cleanName('  Raja   Ram  '), 'Raja Ram');
  assert.equal(cleanName('x'.repeat(50)).length, 40);
  assert.equal(cleanName(undefined), '');
});
