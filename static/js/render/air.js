/**
 * Render the current air quality card.
 * @module render/air
 */

import { categoryClass, categoryMeta, describeAqi } from '../utils/aqi.js';
import { pollutantName } from '../utils/format.js';
import { clear, el } from '../utils/dom.js';

/**
 * @param {HTMLElement} container
 * @param {{aqi: number, category: string, pm2_5: number, pm10: number,
 *          dominant_pollutant: string, health_message: string}} air
 */
export function renderAir(container, air) {
  const meta = categoryMeta(air.category);
  const badge = el('div', { className: `aqi__badge ${categoryClass(air.category)}` }, [
    el('span', { className: 'aqi__icon', text: meta.icon, attrs: { 'aria-hidden': 'true' } }),
    el('span', {
      className: 'aqi__number',
      text: String(air.aqi),
      attrs: { role: 'img', 'aria-label': describeAqi(air.aqi, air.category) },
    }),
    el('span', { className: 'aqi__label', text: meta.label, attrs: { 'aria-hidden': 'true' } }),
  ]);

  const details = el('dl', { className: 'aqi__details' }, [
    el('dt', { text: 'Health advice' }),
    el('dd', { text: air.health_message }),
    el('dt', { text: 'Main pollutant' }),
    el('dd', { text: pollutantName(air.dominant_pollutant) }),
    el('dt', { text: 'PM2.5' }),
    el('dd', { text: `${Math.round(air.pm2_5)} µg/m³` }),
    el('dt', { text: 'PM10' }),
    el('dd', { text: `${Math.round(air.pm10)} µg/m³` }),
  ]);

  clear(container);
  container.append(el('div', { className: 'aqi' }, [badge, details]));
}
