import assert from 'node:assert/strict';
import { test } from 'node:test';

import {
  areaPath,
  axisLabels,
  buildBars,
  chartSummary,
  cleanestHour,
  gradientStops,
  inWindow,
  linePath,
  niceMax,
  scalePoints,
  upcomingHours,
  yTicks,
} from '../../static/js/utils/chart.js';

/** Build hourly forecast entries in IST starting at the given local hour. */
function hours(aqis, startHour = 9) {
  return aqis.map((aqi, i) => {
    const h = String((startHour + i) % 24).padStart(2, '0');
    const day = startHour + i >= 24 ? '26' : '25';
    return { time: `2026-11-${day}T${h}:00:00+05:30`, aqi, pm2_5: aqi / 2 };
  });
}

test('upcomingHours keeps the current hour onwards, capped', () => {
  const forecast = hours([300, 290, 280, 270], 8);
  const upcoming = upcomingHours(forecast, '2026-11-25T09:15:00+05:30', 2);
  assert.deepEqual(upcoming.map((h) => h.aqi), [290, 280]);
});

test('upcomingHours keeps everything for an unparseable time', () => {
  assert.equal(upcomingHours(hours([1, 2, 3]), 'not a date').length, 3);
});

test('inWindow uses half-open intervals', () => {
  const windows = [{ start: '2026-11-25T14:00:00+05:30', end: '2026-11-25T16:00:00+05:30' }];
  assert.equal(inWindow('2026-11-25T14:00:00+05:30', windows), true);
  assert.equal(inWindow('2026-11-25T15:00:00+05:30', windows), true);
  assert.equal(inWindow('2026-11-25T16:00:00+05:30', windows), false);
});

test('buildBars assigns levels and scales heights', () => {
  const windows = [{ start: '2026-11-25T11:00:00+05:30', end: '2026-11-25T12:00:00+05:30' }];
  const bars = buildBars(hours([300, 150, 90]), windows);
  assert.deepEqual(bars.map((b) => b.level), ['high', 'low', 'window']);
  assert.equal(bars[0].heightPct, 100);
  assert.equal(bars[1].heightPct, 50);
  assert.equal(bars[0].label, '9 am');
});

test('buildBars uses a minimum scale so clean days are not full height', () => {
  const [bar] = buildBars(hours([20]));
  assert.equal(bar.heightPct, 20);
});

test('axisLabels shows every fourth label', () => {
  const labels = axisLabels(buildBars(hours([1, 1, 1, 1, 1, 1])));
  assert.deepEqual(labels, ['9 am', '', '', '', '1 pm', '']);
});

test('cleanestHour', () => {
  assert.equal(cleanestHour(hours([200, 80, 120])).aqi, 80);
  assert.equal(cleanestHour([]), null);
});

test('chartSummary describes range and window', () => {
  const windows = [{ start: '2026-11-25T10:00:00+05:30', end: '2026-11-25T11:00:00+05:30' }];
  const text = chartSummary(buildBars(hours([200, 80, 120]), windows));
  assert.match(text, /from 80 at 10 am to 200 at 9 am/);
  assert.match(text, /Cleanest window highlighted: 10 am/);
  assert.equal(chartSummary([]), 'No forecast data available.');
});


test('niceMax rounds up to tidy steps with a floor of 100', () => {
  assert.equal(niceMax(hours([40])), 100);
  assert.equal(niceMax(hours([186])), 200);
  assert.equal(niceMax(hours([312])), 400);
});

test('yTicks', () => {
  assert.deepEqual(yTicks(200), [0, 50, 100, 150, 200]);
  assert.deepEqual(yTicks(400), [0, 100, 200, 300, 400]);
});

test('scalePoints maps AQI to y with 0 at the bottom', () => {
  const points = scalePoints(hours([0, 100, 200]), { width: 100, height: 50, yMax: 200 });
  assert.deepEqual(points.map((p) => [p.x, p.y]), [[0, 50], [50, 25], [100, 0]]);
  const [single] = scalePoints(hours([100]), { width: 100, height: 50, yMax: 200 });
  assert.equal(single.x, 50);
});

test('linePath and areaPath', () => {
  const points = [{ x: 0, y: 10 }, { x: 10, y: 0 }];
  assert.match(linePath(points), /^M0 10 C/);
  assert.match(areaPath(points, 50), /L10 50 L0 50 Z$/);
  assert.equal(linePath([]), '');
  assert.equal(areaPath([], 50), '');
});

test('gradientStops end at the top colour for the axis maximum', () => {
  const stops = gradientStops(200);
  assert.equal(stops[0].offset, 0);
  assert.equal(stops.at(-1).offset, 1);
  assert.equal(stops.at(-1).className, 'stop-unhealthy');
  const partial = gradientStops(250);
  assert.equal(partial.at(-1).className, 'stop-very');
});
