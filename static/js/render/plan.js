/**
 * Render the personalised plan: audience cards, indoor tips, insights, outlook and action cards.
 * @module render/plan
 */

import { audienceArt } from '../utils/art.js';
import { impactLine } from '../utils/format.js';
import { byId, el } from '../utils/dom.js';
import { icon } from '../utils/icons.js';

const INDOOR_ICONS = Object.freeze({
  run_purifier: 'purifier',
  consider_purifier: 'purifier',
  ventilate_clean_hour: 'window',
  avoid_indoor_smoke: 'smoke',
  wet_cleaning: 'mop',
  gas_heater_safety: 'flame',
});

const CATEGORY_INFO = Object.freeze({
  routine: { label: 'Daily routine', icon: 'clock' },
  alternative: { label: 'Greener swap', icon: 'train' },
});

const INSIGHT_ICONS = ['trend', 'globe', 'wind'];

/**
 * @param {any} advice
 * @param {Date} today
 */
function audienceCard(advice, today) {
  const art = audienceArt(advice.audience, today);
  const tips = advice.tips.map((tip) =>
    el('li', {}, [
      el('span', { className: `tip-icon tip-icon--${tip.kind}` }, [icon(tip.kind === 'avoid' ? 'minus' : 'check')]),
      el('span', {}, [
        el('span', { className: 'visually-hidden', text: tip.kind === 'avoid' ? 'Avoid: ' : 'Do: ' }),
        document.createTextNode(tip.text),
      ]),
    ]),
  );
  const image = el('img', {
    className: 'audience__person',
    attrs: { src: art.image, alt: '', width: '480', height: '480', loading: 'lazy' },
  });
  return el('li', { className: `audience audience--${advice.audience}` }, [
    el('div', { className: 'audience__head' }, [
      el('span', { className: 'audience__icon' }, [icon(art.icon)]),
      el('div', {}, [
        el('h3', { text: advice.title }),
        el('p', { className: 'audience__subtitle', text: advice.subtitle }),
      ]),
    ]),
    el('ul', { className: 'audience__tips' }, tips),
    image,
  ]);
}

/** @param {any} rec */
function indoorItem(rec) {
  const impact = impactLine(rec.impact);
  return el('li', { className: 'indoor__item' }, [
    el('span', { className: 'indoor__icon' }, [icon(INDOOR_ICONS[rec.id] ?? 'home')]),
    el('span', { text: rec.title }),
    impact ? el('span', { className: 'indoor__impact', text: impact.headline }) : null,
  ]);
}

/** @param {any} rec */
function actionCard(rec) {
  const info = CATEGORY_INFO[rec.category] ?? { label: rec.category, icon: 'check' };
  const impact = impactLine(rec.impact);
  return el('li', { className: 'card rec-card' }, [
    el('div', { className: 'rec-card__top' }, [
      el('span', { className: 'rec-card__icon' }, [icon(info.icon)]),
      el('p', { className: 'rec-card__category', text: info.label }),
    ]),
    el('h4', { text: rec.title }),
    el('p', { className: 'rec-card__action', text: rec.action }),
    el('p', { className: 'rec-card__why', text: rec.why }),
    impact
      ? el('p', { className: 'rec-card__impact' }, [
          el('strong', { text: impact.headline }),
          document.createTextNode(` · ${impact.detail}`),
        ])
      : null,
  ]);
}

/**
 * @param {HTMLElement} list
 * @param {HTMLElement[]} items
 * @param {string} emptyText
 */
function fillList(list, items, emptyText) {
  list.replaceChildren(...(items.length ? items : [el('li', { className: 'empty', text: emptyText })]));
}

/**
 * Render the whole plan section.
 * @param {any} plan - Plan response from the API.
 */
export function renderPlan(plan) {
  byId('plan-lead').textContent = `Personalised guidance based on today's air quality (AQI ${plan.air.aqi}).`;
  byId('plan-summary').textContent = plan.summary;
  byId('plan-reasons').replaceChildren(...plan.risk.reasons.map((reason) => el('li', { text: reason })));
  const today = new Date();
  byId('audience-cards').replaceChildren(...plan.audiences.map((advice) => audienceCard(advice, today)));

  const recs = plan.recommendations;
  fillList(
    byId('indoor-list'),
    recs.filter((r) => r.category === 'indoor').map(indoorItem),
    'Your indoor air needs no special care today.',
  );
  fillList(
    byId('plan-cards'),
    recs.filter((r) => r.category !== 'indoor').map(actionCard),
    'No changes needed today. Enjoy your usual routine.',
  );

  byId('insights-list').replaceChildren(
    ...plan.insights.map((text, i) =>
      el('li', {}, [
        el('span', { className: 'insights__icon' }, [icon(INSIGHT_ICONS[i % INSIGHT_ICONS.length])]),
        el('span', { text }),
      ]),
    ),
  );

  const outlook = byId('outlook-text').closest('.outlook');
  outlook.classList.remove('outlook--improving', 'outlook--steady', 'outlook--worsening');
  outlook.classList.add(`outlook--${plan.outlook.trend}`);
  byId('outlook-text').textContent = plan.outlook.headline;

  const source = plan.source === 'ai'
    ? 'Written by AirWise AI from today\'s data. All numbers come from our own calculations.'
    : 'Standard advice based on today\'s data.';
  byId('plan-source').textContent = `${source} ${plan.disclaimer}`;
}
