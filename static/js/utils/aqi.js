/**
 * AQI and risk display helpers. Pure functions, no DOM access.
 * @module utils/aqi
 */

/** @type {Record<string, {label: string, icon: string}>} */
export const CATEGORY_META = Object.freeze({
  good: { label: 'Good', icon: '😊' },
  moderate: { label: 'Moderate', icon: '🙂' },
  unhealthy_sensitive: { label: 'Unhealthy for Sensitive Groups', icon: '😐' },
  unhealthy: { label: 'Unhealthy', icon: '😷' },
  very_unhealthy: { label: 'Very Unhealthy', icon: '⚠️' },
  hazardous: { label: 'Hazardous', icon: '⛔' },
});

/** @type {Record<string, string>} */
export const RISK_LABELS = Object.freeze({
  low: 'Low risk',
  moderate: 'Moderate risk',
  high: 'High risk',
  severe: 'Severe risk',
});

const FALLBACK_META = Object.freeze({ label: 'Unknown', icon: '❔' });

/**
 * Return display metadata for an AQI category.
 * @param {string} category - API category value, e.g. "very_unhealthy".
 * @returns {{label: string, icon: string}}
 */
export function categoryMeta(category) {
  return Object.hasOwn(CATEGORY_META, category) ? CATEGORY_META[category] : FALLBACK_META;
}

/**
 * Return the CSS modifier class for a category, or an empty string if unknown.
 * @param {string} category
 * @returns {string}
 */
export function categoryClass(category) {
  return Object.hasOwn(CATEGORY_META, category) ? `aqi--${category}` : '';
}

/**
 * Build the accessible description of an AQI value.
 * @param {number} aqi
 * @param {string} category
 * @returns {string} e.g. "Air quality index 287, Very Unhealthy"
 */
export function describeAqi(aqi, category) {
  return `Air quality index ${aqi}, ${categoryMeta(category).label}`;
}

/**
 * Return a readable label for a risk level.
 * @param {string} level
 * @returns {string}
 */
export function riskLabel(level) {
  return Object.hasOwn(RISK_LABELS, level) ? RISK_LABELS[level] : 'Unknown risk';
}
