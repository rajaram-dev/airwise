/**
 * Render the hero card: sky illustration, current AQI, verdict and pollutant tiles.
 * @module render/air
 */

import { categoryClass, categoryMeta, describeAqi, riskLabel, skyFor } from '../utils/aqi.js';
import { formatClock, formatTimeRange } from '../utils/format.js';
import { byId } from '../utils/dom.js';
import { icon } from '../utils/icons.js';

const CLEAN_CATEGORIES = new Set(['good', 'moderate']);

/**
 * @param {HTMLElement} badge
 * @param {string} text
 * @param {string} className
 * @param {boolean} warn
 */
function setBadge(badge, text, className, warn) {
  badge.className = `badge ${className}`;
  badge.replaceChildren(...(warn ? [icon('alert')] : []), document.createTextNode(text));
}

/** @param {number | null | undefined} value */
function rounded(value) {
  return typeof value === 'number' ? String(Math.round(value)) : '–';
}

/**
 * Show the current reading. Before a plan exists the badge shows the AQI category
 * and the message is the general health advice.
 * @param {string} place
 * @param {{aqi: number, category: string, category_label: string, pm2_5: number, pm10: number,
 *          no2?: number|null, o3?: number|null, health_message: string, observed_at: string}} air
 */
export function renderHero(place, air) {
  const sky = skyFor(air.category);
  const hero = byId('dashboard');
  hero.classList.remove('hero--clear', 'hero--haze', 'hero--smog');
  hero.classList.add(`hero--${sky}`);
  byId('hero-sky').setAttribute('src', `/img/sky-${sky}.webp`);

  byId('hero-place').textContent = place;
  const clock = formatClock(air.observed_at);
  byId('hero-updated').textContent = clock ? `Updated ${clock}` : '';

  const number = byId('hero-aqi');
  number.textContent = String(air.aqi);
  number.setAttribute('aria-label', describeAqi(air.aqi, air.category));
  setBadge(byId('hero-badge'), categoryMeta(air.category).label, categoryClass(air.category), false);

  const clean = CLEAN_CATEGORIES.has(air.category);
  const verdictIcon = byId('hero-title').closest('.hero__verdict').querySelector('.hero__verdict-icon');
  verdictIcon.classList.toggle('hero__verdict-icon--ok', clean);
  byId('hero-title').textContent = `${air.category_label} air today`;
  byId('hero-message').textContent = air.health_message;

  byId('hero-pm25').textContent = rounded(air.pm2_5);
  byId('hero-pm10').textContent = rounded(air.pm10);
  byId('hero-no2').textContent = rounded(air.no2);
  byId('hero-o3').textContent = rounded(air.o3);
}

/**
 * After a plan arrives, switch the badge to the household risk and personalise the message.
 * @param {{risk: {level: string}, best_windows: Array<{start: string, end: string}>}} plan
 */
export function personaliseHero(plan) {
  const level = plan.risk.level;
  const severe = level === 'high' || level === 'severe';
  setBadge(byId('hero-badge'), riskLabel(level), `badge--${level}`, severe);

  const window = plan.best_windows[0];
  const next = window
    ? `Your cleanest time outdoors is ${formatTimeRange(window.start, window.end)}.`
    : 'Best to stay active indoors and keep windows closed.';
  byId('hero-message').textContent = `${riskLabel(level)} for your household. ${next}`;
}
