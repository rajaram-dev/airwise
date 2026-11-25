/**
 * Render the 24-hour AQI line chart as inline SVG.
 * All colours come from CSS classes (no inline styles), so the strict CSP is respected.
 * @module render/chart
 */

import {
  axisLabels,
  buildBars,
  chartSummary,
  cleanestHour,
  gradientStops,
  niceMax,
  scalePoints,
  yTicks,
  areaPath,
  linePath,
} from '../utils/chart.js';
import { formatHour, formatTimeRange, localHour } from '../utils/format.js';
import { byId } from '../utils/dom.js';

const SVG_NS = 'http://www.w3.org/2000/svg';
const W = 600;
const H = 240;
const M = { top: 34, right: 14, bottom: 28, left: 38 };
const PLOT_W = W - M.left - M.right;
const PLOT_H = H - M.top - M.bottom;
const GRADIENT_ID = 'aqi-gradient';

/**
 * @param {string} tag
 * @param {Record<string, string | number>} attrs
 * @param {string} [text]
 */
function svgEl(tag, attrs, text) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, String(value));
  if (text !== undefined) node.textContent = text;
  return node;
}

/** @param {number} yMax */
function gradient(yMax) {
  const grad = svgEl('linearGradient', {
    id: GRADIENT_ID,
    // userSpaceOnUse resolves in the paths' own (plot) coordinates: bottom = AQI 0, top = yMax.
    gradientUnits: 'userSpaceOnUse',
    x1: 0,
    y1: PLOT_H,
    x2: 0,
    y2: 0,
  });
  for (const stop of gradientStops(yMax)) {
    grad.append(svgEl('stop', { offset: stop.offset, class: stop.className }));
  }
  const defs = svgEl('defs', {});
  defs.append(grad);
  return defs;
}

/**
 * @param {Array<{x: number, y: number}>} points
 * @param {ReturnType<typeof buildBars>} bars
 */
function windowBands(points, bars) {
  const group = svgEl('g', {});
  const step = points.length > 1 ? points[1].x - points[0].x : PLOT_W;
  let start = -1;
  bars.forEach((bar, i) => {
    const isWindow = bar.level === 'window';
    if (isWindow && start < 0) start = i;
    const endsHere = start >= 0 && (!isWindow || i === bars.length - 1);
    if (!endsHere) return;
    const end = isWindow ? i : i - 1;
    const x1 = Math.max(0, points[start].x - step / 2);
    const x2 = Math.min(PLOT_W, points[end].x + step / 2);
    group.append(svgEl('rect', { class: 'chart__window', x: x1, y: 0, width: x2 - x1, height: PLOT_H, rx: 6 }));
    group.append(svgEl('text', { class: 'chart__window-label', x: (x1 + x2) / 2, y: 14, 'text-anchor': 'middle' }, 'Cleanest'));
    start = -1;
  });
  return group;
}

/** @param {{x: number, y: number, aqi: number}} point */
function nowMarker(point) {
  const group = svgEl('g', {});
  const label = `${point.aqi} AQI · Now`;
  const tagW = 104;
  const tagX = Math.min(Math.max(point.x - 8, -M.left + 4), PLOT_W - tagW);
  const tagY = Math.max(point.y - 34, -M.top + 4);
  group.append(svgEl('rect', { class: 'chart__tag', x: tagX, y: tagY, width: tagW, height: 24, rx: 6 }));
  group.append(svgEl('text', { class: 'chart__tag-text', x: tagX + tagW / 2, y: tagY + 16, 'text-anchor': 'middle' }, label));
  group.append(svgEl('circle', { class: 'chart__dot', cx: point.x, cy: point.y, r: 5 }));
  return group;
}

/**
 * Draw the chart and update its heading.
 * @param {Array<{time: string, aqi: number, pm2_5: number}>} hours - Upcoming forecast hours.
 * @param {Array<{start: string, end: string}> | null} windows - Plan windows, or null before a plan.
 */
export function renderChart(hours, windows) {
  const container = byId('chart');
  const bars = buildBars(hours, windows ?? []);
  const yMax = niceMax(hours);
  const points = scalePoints(hours, { width: PLOT_W, height: PLOT_H, yMax });

  const svg = svgEl('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-labelledby': 'chart-title' });
  svg.append(svgEl('title', { id: 'chart-title' }, chartSummary(bars)), gradient(yMax));

  const plot = svgEl('g', { transform: `translate(${M.left} ${M.top})` });
  for (const tick of yTicks(yMax)) {
    const y = PLOT_H - (tick / yMax) * PLOT_H;
    plot.append(svgEl('line', { class: 'chart__grid', x1: 0, x2: PLOT_W, y1: y, y2: y }));
    plot.append(svgEl('text', { class: 'chart__label', x: -8, y: y + 4, 'text-anchor': 'end' }, String(tick)));
  }
  axisLabels(bars).forEach((label, i) => {
    if (label) {
      plot.append(svgEl('text', { class: 'chart__label', x: points[i].x, y: PLOT_H + 20, 'text-anchor': 'middle' }, label));
    }
  });

  if (points.length) {
    plot.append(windowBands(points, bars));
    plot.append(svgEl('path', { class: 'chart__area', d: areaPath(points, PLOT_H), fill: `url(#${GRADIENT_ID})` }));
    plot.append(svgEl('path', { class: 'chart__line', d: linePath(points), stroke: `url(#${GRADIENT_ID})` }));
    plot.append(nowMarker(points[0]));
  }
  svg.append(plot);
  container.replaceChildren(svg);

  const title = byId('forecast-heading');
  if (windows && windows.length) {
    title.textContent = `Cleanest window: ${formatTimeRange(windows[0].start, windows[0].end)}`;
  } else if (windows) {
    title.textContent = 'No safe outdoor window today';
  } else {
    const best = cleanestHour(hours);
    const hour = best ? localHour(best.time) : null;
    title.textContent = best && hour !== null ? `Cleanest hour: ${formatHour(hour)} (AQI ${best.aqi})` : 'Forecast unavailable';
  }
}
