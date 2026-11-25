/**
 * App entry point: wires location search, air card, profile form, plan and chat.
 * @module main
 */

import { geocode, getAir, getPlan } from './api.js';
import { initChat, resetChat } from './chat.js';
import { renderAir } from './render/air.js';
import { fillAnswers, readAnswers, validateAnswers } from './render/form.js';
import { renderPlan } from './render/plan.js';
import { forgetProfile, loadSavedProfile, saveProfile, state } from './state.js';
import { initTabs } from './tabs.js';
import { byId, clear, el } from './utils/dom.js';

const GEO_TIMEOUT_MS = 10000;

const statusRegion = byId('status');
const errorBox = byId('error');

/** @param {string} message */
function announce(message) {
  statusRegion.textContent = message;
}

/** @param {string} message */
function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function hideError() {
  errorBox.hidden = true;
  errorBox.textContent = '';
}

/**
 * Run an async task with a busy button and shared error handling.
 * @param {HTMLButtonElement | null} button
 * @param {string} busyText
 * @param {() => Promise<void>} task
 */
async function withBusy(button, busyText, task) {
  const original = button?.textContent ?? '';
  if (button) {
    button.disabled = true;
    button.textContent = busyText;
  }
  hideError();
  announce(busyText);
  try {
    await task();
  } catch (error) {
    showError(error.message);
    announce('');
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = original;
    }
  }
}

/**
 * Set the chosen location and show the current air.
 * @param {{name: string, latitude: number, longitude: number}} location
 */
async function chooseLocation(location) {
  state.location = location;
  byId('search-results').hidden = true;
  const air = await getAir(location.latitude, location.longitude);
  byId('air-place').textContent = location.name;
  renderAir(byId('air-card'), air.current);
  byId('air-section').hidden = false;
  byId('profile-section').hidden = false;
  announce(`Air quality for ${location.name} loaded: ${air.current.category_label}.`);
}

/** @param {Array<any>} results */
function showResults(results) {
  const list = byId('search-results');
  clear(list);
  for (const place of results) {
    const label = [place.name, place.admin1, place.country].filter(Boolean).join(', ');
    const button = el('button', { className: 'btn', text: label, attrs: { type: 'button' } });
    button.addEventListener('click', () =>
      withBusy(null, `Getting live air data for ${place.name}…`, () =>
        chooseLocation({ name: place.name, latitude: place.latitude, longitude: place.longitude }),
      ),
    );
    list.append(el('li', {}, [button]));
  }
  list.hidden = false;
  announce(`${results.length} places found. Choose one from the list.`);
  list.querySelector('button')?.focus();
}

function initSearch() {
  const form = /** @type {HTMLFormElement} */ (byId('search-form'));
  const input = /** @type {HTMLInputElement} */ (byId('city-input'));
  const fieldError = byId('city-error');

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim();
    const valid = query.length >= 2;
    input.setAttribute('aria-invalid', String(!valid));
    fieldError.hidden = valid;
    fieldError.textContent = valid ? '' : 'Enter at least 2 letters of your city or town.';
    if (!valid) {
      input.focus();
      return;
    }
    withBusy(form.querySelector('button'), 'Searching…', async () => {
      const { results } = await geocode(query);
      showResults(results);
    });
  });

  const geoButton = /** @type {HTMLButtonElement} */ (byId('geo-btn'));
  if (!('geolocation' in navigator)) {
    geoButton.hidden = true;
    return;
  }
  geoButton.addEventListener('click', () => {
    withBusy(geoButton, 'Finding you…', async () => {
      const position = await new Promise((resolve, reject) =>
        navigator.geolocation.getCurrentPosition(resolve, () =>
          reject(new Error('We could not get your location. Please search for your city instead.')),
        { timeout: GEO_TIMEOUT_MS, maximumAge: 600000 }),
      );
      await chooseLocation({
        name: 'your location',
        latitude: Math.round(position.coords.latitude * 100) / 100,
        longitude: Math.round(position.coords.longitude * 100) / 100,
      });
    });
  });
}

function initProfile() {
  const form = /** @type {HTMLFormElement} */ (byId('profile-form'));
  const saved = loadSavedProfile();
  if (saved) fillAnswers(form, saved);

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!state.location || !validateAnswers(form)) return;
    const answers = readAnswers(form);
    if (form.elements.namedItem('remember').checked) saveProfile(answers);

    withBusy(form.querySelector('button[type="submit"]'), 'Making your plan…', async () => {
      const plan = await getPlan({
        ...answers,
        latitude: state.location.latitude,
        longitude: state.location.longitude,
        location_name: state.location.name,
      });
      state.plan = plan;
      resetChat();
      renderPlan(plan);
      byId('plan-section').hidden = false;
      byId('chat-section').hidden = false;
      announce(`Your plan for ${plan.location.name} is ready.`);
      byId('plan-heading').focus();
    });
  });

  byId('forget-btn').addEventListener('click', () => {
    forgetProfile();
    form.elements.namedItem('remember').checked = false;
    announce('Saved answers removed from this device.');
  });
}

initSearch();
initProfile();
initTabs(document.querySelector('[role="tablist"]'));
initChat();
