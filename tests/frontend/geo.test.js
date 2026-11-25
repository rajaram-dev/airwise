import assert from 'node:assert/strict';
import { test } from 'node:test';

import { geoErrorMessage, placeLabel, roundCoord } from '../../static/js/utils/geo.js';

test('geoErrorMessage explains each browser error', () => {
  assert.match(geoErrorMessage(1), /blocked/);
  assert.match(geoErrorMessage(2), /isn't available/);
  assert.match(geoErrorMessage(3), /too long/);
  assert.match(geoErrorMessage(undefined), /couldn't get your location/);
});

test('roundCoord keeps about 1 km precision', () => {
  assert.equal(roundCoord(28.613939), 28.61);
  assert.equal(roundCoord(-77.20902), -77.21);
});

test('placeLabel joins parts and skips blanks and duplicates', () => {
  assert.equal(
    placeLabel({ name: 'Delhi', admin1: 'National Capital Territory of Delhi', country: 'India' }),
    'Delhi, National Capital Territory of Delhi, India',
  );
  assert.equal(placeLabel({ name: 'Singapore', admin1: 'Singapore', country: 'Singapore' }), 'Singapore');
  assert.equal(placeLabel({ name: 'Lahore', admin1: '', country: 'Pakistan' }), 'Lahore, Pakistan');
});
