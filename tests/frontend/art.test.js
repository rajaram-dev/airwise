import assert from 'node:assert/strict';
import { test } from 'node:test';

import { AUDIENCE_ART, audienceArt, dayIndex } from '../../static/js/utils/art.js';

const DAY_A = new Date(2026, 10, 26, 9, 0);
const DAY_A_EVENING = new Date(2026, 10, 26, 21, 30);
const DAY_B = new Date(2026, 10, 27, 9, 0);

test('dayIndex is stable within a day and increases by one per day', () => {
  assert.equal(dayIndex(DAY_A), dayIndex(DAY_A_EVENING));
  assert.equal(dayIndex(DAY_B) - dayIndex(DAY_A), 1);
});

test('pictures stay the same all day', () => {
  for (const audience of Object.keys(AUDIENCE_ART)) {
    assert.deepEqual(audienceArt(audience, DAY_A), audienceArt(audience, DAY_A_EVENING));
  }
});

test('adult and older-adult pictures alternate between days', () => {
  for (const audience of ['children', 'adults', 'sensitive']) {
    assert.notEqual(audienceArt(audience, DAY_A).image, audienceArt(audience, DAY_B).image);
  }
});

test('adult and older-adult cards show different genders on the same day', () => {
  for (const day of [DAY_A, DAY_B]) {
    const adultIsFemale = audienceArt('adults', day).image.includes('female');
    const elderIsFemale = audienceArt('sensitive', day).image.includes('female');
    assert.notEqual(adultIsFemale, elderIsFemale);
  }
});

test('pregnancy always uses its own picture and icon', () => {
  assert.deepEqual(audienceArt('pregnancy', DAY_A), { icon: 'heart', image: '/img/person-pregnant.webp' });
  assert.deepEqual(audienceArt('pregnancy', DAY_B), audienceArt('pregnancy', DAY_A));
});

test('unknown audience falls back to the adult art', () => {
  assert.equal(audienceArt('__proto__', DAY_A).icon, 'run');
});
