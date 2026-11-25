/**
 * Render the personalised plan.
 * @module render/plan
 */

import { riskLabel } from '../utils/aqi.js';
import { basisLabel, formatTimeRange, impactChips } from '../utils/format.js';
import { byId, clear, el } from '../utils/dom.js';

const CATEGORIES = ['routine', 'indoor', 'alternative'];
const EMPTY_TEXT = {
  routine: 'No changes to your routine are needed today.',
  indoor: 'Your indoor air needs no special care today.',
  alternative: 'No swaps to suggest for your lifestyle. Nice work!',
};

/** @param {any} rec */
function recommendationCard(rec) {
  const chips = impactChips(rec.impact).map((text) => el('li', { className: 'chip', text }));
  if (chips.length) {
    chips.push(el('li', { className: 'chip chip--basis', text: basisLabel(rec.impact.basis) }));
  }
  return el('li', { className: 'rec-card' }, [
    el('h3', { text: rec.title }),
    el('p', { className: 'rec-card__action', text: rec.action }),
    el('p', { className: 'rec-card__why', text: `Why: ${rec.why}` }),
    chips.length ? el('ul', { className: 'rec-card__impact', attrs: { 'aria-label': 'Impact' } }, chips) : null,
  ]);
}

/** @param {any} risk */
function riskBanner(risk) {
  return el('div', { className: `risk risk--${risk.level}` }, [
    el('h3', { text: riskLabel(risk.level) }),
    el('ul', {}, risk.reasons.map((reason) => el('li', { text: reason }))),
  ]);
}

/** @param {any[]} windows */
function windowsBlock(windows) {
  if (!windows.length) {
    return el('div', { className: 'windows' }, [
      el('h3', { text: 'Best time to be outside' }),
      el('p', { text: 'No hour today is clean enough for outdoor exercise for your household. Stay active indoors.' }),
    ]);
  }
  const items = windows.map((w) =>
    el('li', { text: `${formatTimeRange(w.start, w.end)} (average AQI ${w.avg_aqi})` }),
  );
  return el('div', { className: 'windows' }, [
    el('h3', { text: 'Best times to be outside today' }),
    el('ul', {}, items),
  ]);
}

/**
 * Render the whole plan into the plan section.
 * @param {any} plan - Plan response from the API.
 */
export function renderPlan(plan) {
  byId('plan-summary').textContent = plan.summary;
  byId('plan-source').textContent = plan.source === 'ai'
    ? 'Written by AirWise AI from today\'s data. All numbers come from our calculations.'
    : 'Standard advice based on today\'s data.';
  byId('plan-disclaimer').textContent = plan.disclaimer;

  const risk = byId('risk-banner');
  clear(risk);
  risk.append(riskBanner(plan.risk));

  const windows = byId('windows');
  clear(windows);
  windows.append(windowsBlock(plan.best_windows));

  for (const category of CATEGORIES) {
    const panel = byId(`panel-${category}`);
    const recs = plan.recommendations.filter((r) => r.category === category);
    clear(panel);
    panel.append(
      recs.length
        ? el('ul', { className: 'rec-list' }, recs.map(recommendationCard))
        : el('p', { className: 'empty', text: EMPTY_TEXT[category] }),
    );
    const tab = byId(`tab-${category}`);
    tab.textContent = `${tab.textContent.replace(/ \(\d+\)$/, '')} (${recs.length})`;
  }
}
