/**
 * App entry point: location search, dashboard, household panel, plan and chat.
 * @module main
 */

import { getAir, getPlan } from './api.js';
import { initChat, resetChat, updateChatButton } from './chat.js';
import { personaliseHero, renderHero } from './render/air.js';
import { renderChart } from './render/chart.js';
import { fillAnswers, readAnswers, validateAnswers } from './render/form.js';
import { renderPlan } from './render/plan.js';
import { initSearch } from './search.js';
import { forgetProfile, loadName, loadSavedProfile, saveName, saveProfile, state } from './state.js';
import { upcomingHours } from './utils/chart.js';
import { byId, el } from './utils/dom.js';
import { cleanName, greetingFor, profileSummary } from './utils/format.js';
import { hydrateIcons } from './utils/icons.js';


const form = /** @type {HTMLFormElement} */ (byId('profile-form'));
const panel = byId('profile-panel');
const chip = byId('profile-chip');

/** @param {string} message */
function announce(message) {
  byId('status').textContent = message;
}

/** @param {string} message */
function showError(message) {
  const box = byId('error');
  box.textContent = message;
  box.hidden = false;
}

function hideError() {
  const box = byId('error');
  box.hidden = true;
  box.textContent = '';
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
    if (!button.classList.contains('icon-btn')) button.textContent = busyText;
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
      if (!button.classList.contains('icon-btn')) button.textContent = original;
    }
  }
}

/* ---------- Greeting ---------- */

const DATE_FORMAT = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
});

function renderGreeting() {
  const now = new Date();
  const heading = byId('greeting');
  const parts = [document.createTextNode(greetingFor(now.getHours()))];
  if (state.name) {
    parts.push(document.createTextNode(', '), el('span', { className: 'greeting__name', text: state.name }));
  }
  heading.replaceChildren(...parts);
  byId('today-date').textContent = DATE_FORMAT.format(now);
}

/* ---------- Household panel ---------- */

/** @param {boolean} open */
function setPanel(open) {
  panel.hidden = !open;
  chip.setAttribute('aria-expanded', String(open));
  if (open) {
    byId('welcome').hidden = true;
    byId('profile-heading').focus();
  }
}

function refreshChip() {
  byId('profile-chip-text').textContent = profileSummary(state.answers);
}

/* ---------- Plan ---------- */

async function buildPlan() {
  const plan = await getPlan({
    ...state.answers,
    latitude: state.location.latitude,
    longitude: state.location.longitude,
    location_name: state.location.name,
  });
  state.plan = plan;
  resetChat();
  personaliseHero(plan);
  renderChart(state.hours, plan.best_windows);
  renderPlan(plan);
  byId('plan-section').hidden = false;
  byId('chat-section').hidden = false;
  updateChatButton();
  announce(`Your plan for ${plan.location.name} is ready.`);
}

/* ---------- Location ---------- */

/**
 * Load air data for a location, show the dashboard, then build a plan if we know the household.
 * @param {{name: string, latitude: number, longitude: number}} location
 */
async function chooseLocation(location) {
  state.location = location;
  state.plan = null;
  const air = await getAir(location.latitude, location.longitude);
  state.hours = upcomingHours(air.forecast, air.current.observed_at);
  renderHero(location.name, air.current);
  renderChart(state.hours, null);
  byId('welcome').hidden = true;
  byId('dashboard').hidden = false;
  byId('plan-section').hidden = true;
  byId('chat-section').hidden = true;
  updateChatButton();
  announce(`Air quality for ${location.name}: ${air.current.category_label}.`);

  if (state.answers) {
    await buildPlan();
  } else {
    setPanel(true);
    announce(`Air quality for ${location.name} loaded. Tell us about your household to get your plan.`);
  }
}

function initProfile() {
  const saved = loadSavedProfile();
  if (saved) {
    fillAnswers(form, saved);
    state.answers = readAnswers(form);
  }
  state.name = cleanName(loadName());
  form.elements.namedItem('user_name').value = state.name;
  refreshChip();
  renderGreeting();

  chip.addEventListener('click', () => setPanel(panel.hidden));
  byId('profile-close').addEventListener('click', () => {
    setPanel(false);
    chip.focus();
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    if (!validateAnswers(form)) return;
    state.answers = readAnswers(form);
    state.name = cleanName(form.elements.namedItem('user_name').value);
    if (form.elements.namedItem('remember').checked) {
      saveProfile(state.answers);
      saveName(state.name);
    }
    refreshChip();
    renderGreeting();

    if (!state.location) {
      setPanel(false);
      byId('welcome').hidden = false;
      showError('Saved. Now search for your city to get your plan.');
      byId('city-input').focus();
      return;
    }
    withBusy(form.querySelector('button[type="submit"]'), 'Making your plan…', async () => {
      await buildPlan();
      setPanel(false);
      byId('plan-heading').focus();
    });
  });

  byId('forget-btn').addEventListener('click', () => {
    forgetProfile();
    form.elements.namedItem('remember').checked = false;
    announce('Saved answers and name removed from this device.');
  });
}

hydrateIcons();
const search = initSearch({
  onChoose: chooseLocation,
  run: (busyText, task) => withBusy(null, busyText, task),
});
byId('welcome-locate').addEventListener('click', () => search.locate());
initProfile();
initChat();
