/**
 * Text formatting helpers. Pure functions, no DOM access.
 * @module utils/format
 */

const POLLUTANT_NAMES = Object.freeze({
  pm2_5: 'PM2.5 (fine particles)',
  pm10: 'PM10 (coarse dust)',
  no2: 'Nitrogen dioxide',
  o3: 'Ozone',
});

const ISO_HOUR = /T(\d{2}):(\d{2})/;

/**
 * Format a 0-23 hour as a short 12-hour label.
 * @param {number} hour
 * @returns {string} e.g. "2 pm"
 */
export function formatHour(hour) {
  const h = ((hour % 24) + 24) % 24;
  const display = h % 12 === 0 ? 12 : h % 12;
  return `${display} ${h < 12 ? 'am' : 'pm'}`;
}

/**
 * Read the local hour from an ISO timestamp without converting time zones,
 * so times are shown in the location's own time.
 * @param {string} iso - e.g. "2026-11-25T14:00:00+05:30"
 * @returns {number | null}
 */
export function localHour(iso) {
  const match = ISO_HOUR.exec(String(iso));
  return match ? Number(match[1]) : null;
}

/**
 * Format a window from two ISO timestamps.
 * @param {string} startIso
 * @param {string} endIso
 * @returns {string} e.g. "2 pm – 4 pm"
 */
export function formatTimeRange(startIso, endIso) {
  const start = localHour(startIso);
  const end = localHour(endIso);
  if (start === null || end === null) return '';
  return `${formatHour(start)} – ${formatHour(end)}`;
}

/**
 * Return a friendly pollutant name.
 * @param {string} key - API pollutant key.
 * @returns {string}
 */
export function pollutantName(key) {
  return Object.hasOwn(POLLUTANT_NAMES, key) ? POLLUTANT_NAMES[key] : key;
}

/**
 * Turn an impact object into short chip labels.
 * @param {{exposure_reduction_pct?: number|null, co2_kg_saved_per_day?: number|null,
 *          note?: string|null, basis?: string}} impact
 * @returns {string[]}
 */
export function impactChips(impact) {
  if (!impact) return [];
  const chips = [];
  const pct = impact.exposure_reduction_pct;
  if (typeof pct === 'number' && pct > 0) {
    chips.push(`Up to ${pct}% less pollution breathed`);
  }
  const co2 = impact.co2_kg_saved_per_day;
  if (typeof co2 === 'number' && co2 > 0) {
    chips.push(`Saves ${co2} kg CO₂ a day`);
  }
  if (impact.note) chips.push(impact.note);
  return chips;
}

/**
 * Explain where an impact figure came from.
 * @param {string} basis - "computed" or "estimated".
 * @returns {string}
 */
export function basisLabel(basis) {
  return basis === 'computed' ? 'Calculated from today\'s forecast' : 'Estimate from published data';
}

/**
 * Clamp a number into a range, returning the fallback for non-numeric input.
 * @param {unknown} value
 * @param {number} min
 * @param {number} max
 * @param {number} fallback
 * @returns {number}
 */
export function clampInt(value, min, max, fallback) {
  const n = Number.parseInt(String(value), 10);
  if (Number.isNaN(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}
