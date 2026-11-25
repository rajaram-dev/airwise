/**
 * Inline SVG icons (24x24 stroke icons), built with DOM APIs so no markup strings are parsed.
 * @module utils/icons
 */

const SVG_NS = 'http://www.w3.org/2000/svg';

/** @type {Record<string, string[]>} Path data per icon name. */
const PATHS = Object.freeze({
  leaf: ['M5 19c0-8 5-14 15-15c0 10-6 15-14 15', 'M5 19l8-8'],
  search: ['M11 4a7 7 0 1 0 0 14a7 7 0 1 0 0-14', 'M20 20l-4-4'],
  pin: ['M12 21s-6-5.6-6-11a6 6 0 1 1 12 0c0 5.4-6 11-6 11z', 'M12 8a2 2 0 1 0 0 4a2 2 0 1 0 0-4'],
  user: ['M12 4a4 4 0 1 0 0 8a4 4 0 1 0 0-8', 'M4 21a8 8 0 0 1 16 0'],
  x: ['M6 6l12 12', 'M18 6L6 18'],
  clock: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M12 7v5l3 2'],
  home: ['M4 11l8-7l8 7', 'M6 10v10h12V10', 'M10 20v-5h4v5'],
  train: ['M7 3h10a2 2 0 0 1 2 2v9a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5a2 2 0 0 1 2-2z', 'M5 10h14', 'M8 21l2-4', 'M16 21l-2-4'],
  message: ['M4 5h16v11H9l-5 4z'],
  alert: ['M12 4l9 16H3z', 'M12 10v4', 'M12 17h.01'],
  check: ['M5 12l5 5l9-10'],
  minus: ['M6 12h12'],
  lungs: ['M12 4v7', 'M12 11c-1 2-3 3-4 3', 'M12 11c1 2 3 3 4 3', 'M8 7c-3 1-4 5-4 9c0 2 1 3 3 3s3-1 3-3V9', 'M16 7c3 1 4 5 4 9c0 2-1 3-3 3s-3-1-3-3V9'],
  trend: ['M4 17l5-5l4 4l7-8', 'M15 8h5v5'],
  wind: ['M3 8h10a3 3 0 1 0-3-3', 'M3 12h15a3 3 0 1 1-3 3', 'M3 16h6'],
  child: ['M12 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8', 'M9.5 7.5h.01', 'M14.5 7.5h.01', 'M10 9.5c1 .8 3 .8 4 0', 'M7 21v-3a5 5 0 0 1 10 0v3'],
  run: ['M14 4a2 2 0 1 0 0 4a2 2 0 1 0 0-4', 'M9 20l3-6l3 2v5', 'M6 12l3-3l4 1l3 3h3', 'M12 14l-2-4'],
  heart: ['M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z'],
  purifier: ['M7 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z', 'M12 6a2 2 0 1 0 0 4a2 2 0 1 0 0-4', 'M9 14v4', 'M12 14v4', 'M15 14v4'],
  window: ['M4 4h16v16H4z', 'M12 4v16', 'M4 12h16'],
  mop: ['M14 3l-4 11', 'M6 14h8l2 7H4z', 'M8 17v4', 'M12 17v4'],
  smoke: ['M5 20h14', 'M8 16c-2-2 2-3 0-5s2-3 0-5', 'M13 16c-2-2 2-3 0-5s2-3 0-5', 'M18 16c-2-2 2-3 0-5'],
  flame: ['M12 21c-4 0-6-3-6-6c0-4 4-6 4-10c3 2 4 4 4 6c1-1 1.5-2 1.5-3c2 2 2.5 4 2.5 7c0 3-2 6-6 6z'],
  globe: ['M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18', 'M3 12h18', 'M12 3c3 3 3 15 0 18', 'M12 3c-3 3-3 15 0 18'],
  calendar: ['M4 6h16v14H4z', 'M4 10h16', 'M8 3v4', 'M16 3v4'],
});

/**
 * Create an SVG icon element. Icons are decorative (aria-hidden).
 * @param {string} name - Icon name from PATHS.
 * @returns {SVGSVGElement}
 */
export function icon(name) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('class', 'icon');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  for (const d of PATHS[name] ?? []) {
    const path = document.createElementNS(SVG_NS, 'path');
    path.setAttribute('d', d);
    svg.append(path);
  }
  return svg;
}

/** Replace every element with a data-icon attribute by its SVG icon. */
export function hydrateIcons(root = document) {
  for (const holder of root.querySelectorAll('[data-icon]')) {
    holder.replaceChildren(icon(holder.getAttribute('data-icon')));
  }
}
