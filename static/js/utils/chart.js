/**
 * Data preparation for the 24-hour AQI bar chart. Pure functions, no DOM access.
 * @module utils/chart
 */

import { formatHour, localHour } from './format.js';

/** AQI at or above this is drawn as "Unhealthy or worse" (US EPA Unhealthy starts at 151). */
export const HIGH_AQI = 151;
const MIN_SCALE = 100;
const MIN_BAR_PCT = 4;
const AXIS_EVERY = 4;
const ONE_HOUR_MS = 3600000;

/**
 * @typedef {{time: string, aqi: number, pm2_5: number}} ForecastHour
 * @typedef {{start: string, end: string}} Window
 * @typedef {{time: string, hour: number|null, aqi: number, level: 'high'|'low'|'window',
 *            heightPct: number, label: string}} Bar
 */

/**
 * Keep only forecast hours from the current hour onwards, up to ``hours`` entries.
 * @param {ForecastHour[]} forecast
 * @param {string} nowIso - Observation time of the current reading.
 * @param {number} [hours]
 * @returns {ForecastHour[]}
 */
export function upcomingHours(forecast, nowIso, hours = 24) {
  const now = Date.parse(nowIso);
  // Keep the hour that contains "now": its start is less than one hour ago.
  const cutoff = Number.isNaN(now) ? -Infinity : now - ONE_HOUR_MS;
  return forecast.filter((h) => Date.parse(h.time) > cutoff).slice(0, hours);
}

/**
 * True if the timestamp falls inside any window.
 * @param {string} timeIso
 * @param {Window[]} windows
 */
export function inWindow(timeIso, windows) {
  const t = Date.parse(timeIso);
  return windows.some((w) => t >= Date.parse(w.start) && t < Date.parse(w.end));
}

/**
 * Turn forecast hours into bars with a level and relative height.
 * @param {ForecastHour[]} hours
 * @param {Window[]} [windows]
 * @returns {Bar[]}
 */
export function buildBars(hours, windows = []) {
  const max = Math.max(MIN_SCALE, ...hours.map((h) => h.aqi));
  return hours.map((h) => {
    const hour = localHour(h.time);
    let level = h.aqi >= HIGH_AQI ? 'high' : 'low';
    if (inWindow(h.time, windows)) level = 'window';
    return {
      time: h.time,
      hour,
      aqi: h.aqi,
      level,
      heightPct: Math.max(MIN_BAR_PCT, Math.round((h.aqi / max) * 100)),
      label: hour === null ? '' : formatHour(hour),
    };
  });
}

/**
 * Axis labels: one every few bars, empty strings in between.
 * @param {Bar[]} bars
 * @returns {string[]}
 */
export function axisLabels(bars) {
  return bars.map((bar, i) => (i % AXIS_EVERY === 0 ? bar.label : ''));
}

/**
 * Return the hour with the lowest AQI, or null when there is no data.
 * @param {ForecastHour[]} hours
 * @returns {ForecastHour|null}
 */
export function cleanestHour(hours) {
  return hours.reduce((best, h) => (best === null || h.aqi < best.aqi ? h : best), null);
}

/**
 * One-sentence text alternative for the chart.
 * @param {Bar[]} bars
 * @returns {string}
 */
export function chartSummary(bars) {
  if (!bars.length) return 'No forecast data available.';
  const low = bars.reduce((a, b) => (b.aqi < a.aqi ? b : a));
  const high = bars.reduce((a, b) => (b.aqi > a.aqi ? b : a));
  const windowHours = bars.filter((b) => b.level === 'window').map((b) => b.label);
  const windowText = windowHours.length ? ` Cleanest window highlighted: ${windowHours.join(', ')}.` : '';
  return `AQI forecast for the next ${bars.length} hours, from ${low.aqi} at ${low.label} to ${high.aqi} at ${high.label}.${windowText}`;
}

/* ---------- Line chart geometry ---------- */

/** AQI breakpoints and the CSS class that colours each gradient stop. */
export const AQI_STOPS = Object.freeze([
  [0, 'stop-good'],
  [50, 'stop-good'],
  [100, 'stop-moderate'],
  [150, 'stop-usg'],
  [200, 'stop-unhealthy'],
  [300, 'stop-very'],
  [500, 'stop-hazardous'],
]);

/**
 * Round the y-axis maximum up to a tidy value (at least 100).
 * @param {Array<{aqi: number}>} hours
 * @returns {number}
 */
export function niceMax(hours) {
  const max = Math.max(MIN_SCALE, ...hours.map((h) => h.aqi));
  const step = max > 300 ? 100 : 50;
  return Math.ceil(max / step) * step;
}

/**
 * Y-axis tick values from 0 to yMax.
 * @param {number} yMax
 * @returns {number[]}
 */
export function yTicks(yMax) {
  const step = yMax > 300 ? 100 : 50;
  const ticks = [];
  for (let v = 0; v <= yMax; v += step) ticks.push(v);
  return ticks;
}

/**
 * Map hours to x/y coordinates inside a width x height box (y grows downwards).
 * @param {Array<{time: string, aqi: number}>} hours
 * @param {{width: number, height: number, yMax: number}} box
 * @returns {Array<{x: number, y: number, aqi: number, time: string}>}
 */
export function scalePoints(hours, { width, height, yMax }) {
  const n = hours.length;
  return hours.map((h, i) => ({
    x: n === 1 ? width / 2 : (i / (n - 1)) * width,
    y: height - (Math.min(h.aqi, yMax) / yMax) * height,
    aqi: h.aqi,
    time: h.time,
  }));
}

/** @param {number} n */
const fmt = (n) => Math.round(n * 10) / 10;

/**
 * Smooth SVG path through the points (Catmull-Rom converted to cubic Béziers).
 * @param {Array<{x: number, y: number}>} points
 * @returns {string}
 */
export function linePath(points) {
  if (!points.length) return '';
  let d = `M${fmt(points[0].x)} ${fmt(points[0].y)}`;
  for (let i = 0; i < points.length - 1; i += 1) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(points.length - 1, i + 2)];
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
    d += ` C${fmt(c1.x)} ${fmt(c1.y)} ${fmt(c2.x)} ${fmt(c2.y)} ${fmt(p2.x)} ${fmt(p2.y)}`;
  }
  return d;
}

/**
 * Closed area path under the line, down to the baseline.
 * @param {Array<{x: number, y: number}>} points
 * @param {number} baseline
 * @returns {string}
 */
export function areaPath(points, baseline) {
  if (!points.length) return '';
  const last = points[points.length - 1];
  return `${linePath(points)} L${fmt(last.x)} ${baseline} L${fmt(points[0].x)} ${baseline} Z`;
}

/**
 * Gradient stops (offset 0 = bottom/AQI 0, 1 = top/yMax) for the AQI colour scale.
 * @param {number} yMax
 * @returns {Array<{offset: number, className: string}>}
 */
export function gradientStops(yMax) {
  const stops = AQI_STOPS.filter(([aqi]) => aqi <= yMax).map(([aqi, className]) => ({
    offset: Math.round((aqi / yMax) * 1000) / 1000,
    className,
  }));
  const next = AQI_STOPS.find(([aqi]) => aqi > yMax);
  if (next && stops[stops.length - 1].offset < 1) stops.push({ offset: 1, className: next[1] });
  return stops;
}
