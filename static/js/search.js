/**
 * Location search: live suggestions while typing, "Use my current location" as the first
 * option, keyboard navigation, and visible feedback while the browser finds the user.
 * @module search
 */

import { geocode } from './api.js';
import { byId, el } from './utils/dom.js';
import { geoErrorMessage, placeLabel, roundCoord } from './utils/geo.js';
import { icon } from './utils/icons.js';

const DEBOUNCE_MS = 300;
const MIN_CHARS = 2;
const GEO_OPTIONS = Object.freeze({ timeout: 10000, maximumAge: 600000 });

/**
 * @typedef {{name: string, latitude: number, longitude: number}} Location
 * @typedef {(busyText: string, task: () => Promise<void>) => Promise<void>} RunTask
 */

/** @returns {Promise<GeolocationPosition>} */
function currentPosition() {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      resolve,
      (error) => reject(new Error(geoErrorMessage(error.code))),
      GEO_OPTIONS,
    );
  });
}

/**
 * Wire up the search box and location buttons.
 * @param {{onChoose: (location: Location) => Promise<void>, run: RunTask}} deps
 * @returns {{locate: () => Promise<void>}}
 */
export function initSearch({ onChoose, run }) {
  const form = /** @type {HTMLFormElement} */ (byId('search-form'));
  const input = /** @type {HTMLInputElement} */ (byId('city-input'));
  const list = byId('search-results');
  const fieldError = byId('city-error');
  const geoButton = /** @type {HTMLButtonElement} */ (byId('geo-btn'));
  const status = byId('locate-status');
  const canLocate = 'geolocation' in navigator;
  let requestId = 0;
  let timer = 0;

  const setOpen = (open) => {
    list.hidden = !open;
    input.setAttribute('aria-expanded', String(open));
  };

  const buttons = () => [...list.querySelectorAll('button')];

  async function locate() {
    setOpen(false);
    status.hidden = false;
    geoButton.setAttribute('aria-busy', 'true');
    try {
      await run('Finding your location…', async () => {
        const position = await currentPosition();
        await onChoose({
          name: 'Your location',
          latitude: roundCoord(position.coords.latitude),
          longitude: roundCoord(position.coords.longitude),
        });
      });
    } finally {
      status.hidden = true;
      geoButton.removeAttribute('aria-busy');
    }
  }

  function locateOption() {
    const button = el('button', { className: 'search__option search__option--locate', attrs: { type: 'button' } }, [
      icon('pin'),
      el('span', {}, [
        el('span', { className: 'search__option-title', text: 'Use my current location' }),
        el('span', { className: 'search__option-hint', text: 'Uses your browser\'s location, rounded to about 1 km' }),
      ]),
    ]);
    button.addEventListener('click', locate);
    return el('li', {}, [button]);
  }

  /** @param {any} place */
  function placeOption(place) {
    const label = placeLabel(place);
    const button = el('button', { className: 'search__option', attrs: { type: 'button' } }, [
      icon('search'),
      el('span', { className: 'search__option-title', text: label }),
    ]);
    button.addEventListener('click', () => {
      input.value = place.name;
      setOpen(false);
      run(`Getting live air data for ${place.name}…`, () =>
        onChoose({ name: place.name, latitude: place.latitude, longitude: place.longitude }),
      );
    });
    return el('li', {}, [button]);
  }

  /**
   * @param {any[]} places
   * @param {string} [message]
   */
  function render(places, message) {
    const items = [];
    if (canLocate) items.push(locateOption());
    if (message) items.push(el('li', { className: 'search__message', text: message }));
    items.push(...places.map(placeOption));
    list.replaceChildren(...items);
    setOpen(items.length > 0);
  }

  /** @param {string} query */
  async function suggest(query) {
    const id = ++requestId;
    try {
      const { results } = await geocode(query);
      if (id === requestId) render(results);
    } catch (error) {
      if (id !== requestId) return;
      render([], error.code === 'location_not_found' ? 'No places found. Check the spelling.' : 'Suggestions are unavailable right now.');
    }
  }

  input.addEventListener('input', () => {
    window.clearTimeout(timer);
    fieldError.hidden = true;
    input.removeAttribute('aria-invalid');
    const query = input.value.trim();
    if (query.length < MIN_CHARS) {
      requestId += 1;
      render([]);
      return;
    }
    timer = window.setTimeout(() => suggest(query), DEBOUNCE_MS);
  });

  input.addEventListener('focus', () => {
    if (!list.hidden) return;
    const query = input.value.trim();
    if (query.length < MIN_CHARS) render([]);
    else suggest(query);
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    window.clearTimeout(timer);
    const query = input.value.trim();
    const valid = query.length >= MIN_CHARS;
    input.setAttribute('aria-invalid', String(!valid));
    fieldError.hidden = valid;
    fieldError.textContent = valid ? '' : 'Enter at least 2 letters of your city or town.';
    if (!valid) {
      input.focus();
      return;
    }
    run('Searching…', async () => {
      const { results } = await geocode(query);
      render(results);
      list.querySelector('.search__option:not(.search__option--locate)')?.focus();
    });
  });

  form.addEventListener('keydown', (event) => {
    const options = buttons();
    const index = options.indexOf(/** @type {HTMLButtonElement} */ (document.activeElement));
    if (event.key === 'Escape' && !list.hidden) {
      setOpen(false);
      input.focus();
    } else if (event.key === 'ArrowDown' && options.length) {
      event.preventDefault();
      if (list.hidden) render([]);
      options[Math.min(index + 1, options.length - 1)]?.focus();
    } else if (event.key === 'ArrowUp' && index >= 0) {
      event.preventDefault();
      if (index === 0) input.focus();
      else options[index - 1].focus();
    }
  });

  document.addEventListener('click', (event) => {
    if (!form.contains(/** @type {Node} */ (event.target))) setOpen(false);
  });

  if (canLocate) {
    geoButton.addEventListener('click', locate);
  } else {
    geoButton.hidden = true;
  }

  return { locate };
}
