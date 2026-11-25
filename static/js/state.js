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
  /** @type {Array<{role: 'user'|'assistant', text: string}>} */
  history: [],
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

/** Remove saved answers from this device. */
export function forgetProfile() {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to clear.
  }
}
