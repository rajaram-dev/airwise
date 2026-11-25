/**
 * Safe DOM helpers. Text is always set with textContent — never innerHTML.
 * @module utils/dom
 */

/**
 * Create an element.
 * @param {string} tag
 * @param {{className?: string, text?: string, attrs?: Record<string, string>}} [options]
 * @param {(Node|null|undefined)[]} [children]
 * @returns {HTMLElement}
 */
export function el(tag, options = {}, children = []) {
  const node = document.createElement(tag);
  if (options.className) node.className = options.className;
  if (options.text !== undefined) node.textContent = options.text;
  for (const [name, value] of Object.entries(options.attrs ?? {})) {
    node.setAttribute(name, value);
  }
  for (const child of children) {
    if (child) node.append(child);
  }
  return node;
}

/**
 * Remove all children from a node.
 * @param {Element} node
 */
export function clear(node) {
  node.replaceChildren();
}

/**
 * Get a required element by id.
 * @param {string} id
 * @returns {HTMLElement}
 */
export function byId(id) {
  const node = document.getElementById(id);
  if (!node) throw new Error(`Missing element #${id}`);
  return node;
}
