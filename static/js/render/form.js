/**
 * Read and fill the household profile form.
 * @module render/form
 */

import { clampInt } from '../utils/format.js';

const HOUSEHOLD_FIELDS = ['children', 'elderly', 'respiratory_condition', 'pregnant'];
const SELECT_FIELDS = ['commute_mode', 'cooking_fuel', 'heating', 'outdoor_activity', 'language'];
const MAX_COMMUTE_MINUTES = 240;

/**
 * Read the form into answers (without location).
 * @param {HTMLFormElement} form
 * @returns {Record<string, any>}
 */
export function readAnswers(form) {
  const f = form.elements;
  const household = Object.fromEntries(HOUSEHOLD_FIELDS.map((name) => [name, f.namedItem(name).checked]));
  const selects = Object.fromEntries(SELECT_FIELDS.map((name) => [name, f.namedItem(name).value]));
  const minutes = selects.commute_mode === 'wfh'
    ? 0
    : clampInt(f.namedItem('commute_minutes').value, 0, MAX_COMMUTE_MINUTES, 0);
  return {
    household,
    ...selects,
    commute_minutes: minutes,
    has_air_purifier: f.namedItem('has_air_purifier').checked,
  };
}

/**
 * Validate the commute field and show an inline error.
 * @param {HTMLFormElement} form
 * @returns {boolean} true when valid
 */
export function validateAnswers(form) {
  const input = form.elements.namedItem('commute_minutes');
  const error = document.getElementById('commute-error');
  const value = Number(input.value);
  const valid = input.value === '' || (Number.isInteger(value) && value >= 0 && value <= MAX_COMMUTE_MINUTES);
  input.setAttribute('aria-invalid', String(!valid));
  error.hidden = valid;
  error.textContent = valid ? '' : `Enter a whole number of minutes from 0 to ${MAX_COMMUTE_MINUTES}.`;
  if (!valid) input.focus();
  return valid;
}

/**
 * Fill the form from saved answers. Unknown or invalid values are ignored.
 * @param {HTMLFormElement} form
 * @param {Record<string, any>} answers
 */
export function fillAnswers(form, answers) {
  const f = form.elements;
  for (const name of HOUSEHOLD_FIELDS) {
    f.namedItem(name).checked = Boolean(answers.household?.[name]);
  }
  for (const name of SELECT_FIELDS) {
    const select = f.namedItem(name);
    if ([...select.options].some((o) => o.value === answers[name])) select.value = answers[name];
  }
  f.namedItem('commute_minutes').value = String(clampInt(answers.commute_minutes, 0, MAX_COMMUTE_MINUTES, 0));
  f.namedItem('has_air_purifier').checked = Boolean(answers.has_air_purifier);
  f.namedItem('remember').checked = true;
}
