/**
 * Location helpers. Pure functions, no DOM or browser APIs.
 * @module utils/geo
 */

/** GeolocationPositionError codes (see the Geolocation API spec). */
const PERMISSION_DENIED = 1;
const POSITION_UNAVAILABLE = 2;
const TIMEOUT = 3;

const MESSAGES = Object.freeze({
  [PERMISSION_DENIED]: 'Location access is blocked. Allow it in your browser settings, or search for your city.',
  [POSITION_UNAVAILABLE]: 'Your location isn\'t available right now. Search for your city instead.',
  [TIMEOUT]: 'Finding your location took too long. Try again, or search for your city.',
});

/**
 * Friendly message for a geolocation error code.
 * @param {number | undefined} code
 * @returns {string}
 */
export function geoErrorMessage(code) {
  return MESSAGES[code] ?? 'We couldn\'t get your location. Search for your city instead.';
}

/**
 * Round a coordinate to 2 decimals (~1 km) so precise locations are never sent or stored.
 * @param {number} value
 * @returns {number}
 */
export function roundCoord(value) {
  return Math.round(value * 100) / 100;
}

/**
 * Display label for a geocoding result, e.g. "Delhi, National Capital Territory of Delhi, India".
 * @param {{name: string, admin1?: string, country?: string}} place
 * @returns {string}
 */
export function placeLabel(place) {
  const parts = [place.name, place.admin1, place.country].filter(Boolean);
  return [...new Set(parts)].join(', ');
}
