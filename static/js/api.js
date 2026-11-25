/**
 * Thin wrapper over fetch for the AirWise API.
 * @module api
 */

const BASE = '/api/v1';
const TIMEOUT_MS = 30000;

/** Error carrying the API's machine code and a user-friendly message. */
export class ApiError extends Error {
  /**
   * @param {string} message
   * @param {string} code
   * @param {number} status
   */
  constructor(message, code, status) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
  }
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers ?? {}) },
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    throw new ApiError('Could not reach AirWise. Check your connection and try again.', 'network', 0);
  }

  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(body.message ?? 'Something went wrong.', body.error ?? 'unknown', response.status);
  }
  return body;
}

/**
 * Search places by name.
 * @param {string} query
 * @returns {Promise<{results: Array<{name: string, country: string, admin1: string, latitude: number, longitude: number}>}>}
 */
export function geocode(query) {
  return request(`/geocode?q=${encodeURIComponent(query)}`);
}

/**
 * Name of the town or city at a coordinate.
 * @param {number} lat
 * @param {number} lon
 * @returns {Promise<{name: string, admin1: string, country: string}>}
 */
export function reverseGeocode(lat, lon) {
  return request(`/reverse-geocode?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
}

/**
 * Current air and forecast for a coordinate.
 * @param {number} lat
 * @param {number} lon
 */
export function getAir(lat, lon) {
  return request(`/air?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`);
}

/**
 * Build a personalised plan.
 * @param {object} profile
 */
export function getPlan(profile) {
  return request('/plan', { method: 'POST', body: JSON.stringify(profile) });
}

/**
 * Ask a follow-up question.
 * @param {object} payload
 */
export function sendChat(payload) {
  return request('/chat', { method: 'POST', body: JSON.stringify(payload) });
}
