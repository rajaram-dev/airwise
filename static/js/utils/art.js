/**
 * Illustrations for the audience cards. Where both a woman and a man are available,
 * the picture alternates by day so both are represented over time, while staying
 * stable for the whole day. Pure functions, no DOM access.
 * @module utils/art
 */

const MS_PER_DAY = 86400000;

/** @type {Record<string, {icon: string, images: string[], offset: number}>} */
export const AUDIENCE_ART = Object.freeze({
  children: { icon: 'child', images: ['/img/person-child.webp', '/img/person-child-boy.webp'], offset: 0 },
  adults: { icon: 'run', images: ['/img/person-adult-female.webp', '/img/person-adult.webp'], offset: 0 },
  // Offset by one so the older-adult card shows the opposite gender to the adult card.
  sensitive: { icon: 'lungs', images: ['/img/person-elder-female.webp', '/img/person-elder.webp'], offset: 1 },
  pregnancy: { icon: 'heart', images: ['/img/person-pregnant.webp'], offset: 0 },
});

/**
 * Whole days since 1970-01-01 for the local calendar date.
 * @param {Date} date
 * @returns {number}
 */
export function dayIndex(date) {
  return Math.floor(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()) / MS_PER_DAY);
}

/**
 * Icon and image for an audience on a given day.
 * @param {string} audience
 * @param {Date} date
 * @returns {{icon: string, image: string}}
 */
export function audienceArt(audience, date) {
  const art = Object.hasOwn(AUDIENCE_ART, audience) ? AUDIENCE_ART[audience] : AUDIENCE_ART.adults;
  const index = (dayIndex(date) + art.offset) % art.images.length;
  return { icon: art.icon, image: art.images[index] };
}
