/**
 * App state and opt-in on-device storage of the profile.
 * @module state
 */

const STORAGE_KEY = 'airwise.profile.v1';

/** Shared mutable state for the current session (never sent anywhere by itself). */
export const state = {
  /** @type {{name: string, latitude: number, longitude: number} | null} */
  location: null,
  /** @type {any} */
  plan: null,
  /** @type {Record<string, any> | null} Household answers (without location). */
  answers: null,
  /** @type {Array<{time: string, aqi: number, pm2_5: number}>} Upcoming forecast hours. */
  hours: [],
  /** @type {Array<{role: 'user'|'assistant', text: string}>} */
  history: [],
  /** Optional display name for the greeting (never sent to the server). */
  name: '',
};

/**
 * Load the saved profile answers, if any.
 * @returns {Record<string, unknown> | null}
 */
export function loadSavedProfile() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/**
 * Save profile answers on this device. Location is not saved.
 * @param {Record<string, unknown>} answers
 */
export function saveProfile(answers) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(answers));
  } catch {
    // Storage may be blocked (private mode); the app works without it.
  }
}

/** Remove saved answers and name from this device. */
export function forgetProfile() {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    window.localStorage.removeItem(NAME_KEY);
  } catch {
    // Nothing to clear.
  }
}

const NAME_KEY = 'airwise.name.v1';

/**
 * Load the saved display name, if any.
 * @returns {string}
 */
export function loadName() {
  try {
    return window.localStorage.getItem(NAME_KEY) ?? '';
  } catch {
    return '';
  }
}

/**
 * Save (or clear, when empty) the display name on this device only.
 * @param {string} name
 */
export function saveName(name) {
  try {
    if (name) window.localStorage.setItem(NAME_KEY, name);
    else window.localStorage.removeItem(NAME_KEY);
  } catch {
    // Storage may be blocked; the greeting still works for this visit.
  }
}
