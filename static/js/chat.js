/**
 * Follow-up chat with AirWise.
 * @module chat
 */

import { sendChat } from './api.js';
import { state } from './state.js';
import { byId, el } from './utils/dom.js';
import { parseReply } from './utils/markdown.js';

const MAX_HISTORY = 6;
const MAX_MESSAGE = 500;

/** @param {Array<{text: string, bold: boolean}>} spans */
function inline(spans) {
  return spans.map((span) => (span.bold ? el('strong', { text: span.text }) : document.createTextNode(span.text)));
}

/**
 * Build formatted nodes for an assistant reply (paragraphs, lists, bold) using DOM APIs only.
 * @param {string} text
 * @returns {HTMLElement[]}
 */
function formatReply(text) {
  return parseReply(text).map((block) =>
    block.type === 'p'
      ? el('p', {}, inline(block.spans))
      : el(block.type, {}, block.items.map((spans) => el('li', {}, inline(spans)))),
  );
}

/**
 * @param {'user'|'assistant'} role
 * @param {string} text
 */
function appendMessage(role, text) {
  const body = role === 'assistant' ? formatReply(text) : [el('p', { text })];
  byId('chat-log').append(
    el('div', { className: `chat-msg chat-msg--${role}` }, [
      el('span', { className: 'chat-msg__who', text: role === 'user' ? 'You' : 'AirWise' }),
      ...body,
    ]),
  );
}

/** Build the compact plan context sent with each question. */
function planContext() {
  const plan = state.plan;
  return {
    location_name: plan.location.name,
    aqi: plan.air.aqi,
    risk_level: plan.risk.level,
    summary: plan.summary.slice(0, 600),
    item_titles: plan.recommendations.slice(0, 15).map((r) => r.title.slice(0, 80)),
  };
}

/** Clear the conversation (called when a new plan is made). */
export function resetChat() {
  state.history = [];
  byId('chat-log').replaceChildren();
}

/** Wire up the chat form. */
export function initChat() {
  const form = /** @type {HTMLFormElement} */ (byId('chat-form'));
  const input = /** @type {HTMLInputElement} */ (byId('chat-input'));
  const button = form.querySelector('button[type="submit"]');

  for (const suggestion of document.querySelectorAll('.suggestion')) {
    suggestion.addEventListener('click', () => {
      input.value = suggestion.textContent;
      form.requestSubmit();
    });
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim().slice(0, MAX_MESSAGE);
    if (!message || !state.plan) return;

    appendMessage('user', message);
    input.value = '';
    button.disabled = true;
    try {
      const response = await sendChat({
        message,
        context: planContext(),
        history: state.history.slice(-MAX_HISTORY),
        language: document.getElementById('language').value,
      });
      appendMessage('assistant', response.reply);
      state.history.push({ role: 'user', text: message }, { role: 'assistant', text: response.reply.slice(0, 1000) });
    } catch (error) {
      appendMessage('assistant', error.message);
    } finally {
      button.disabled = false;
      input.focus();
    }
  });
}
