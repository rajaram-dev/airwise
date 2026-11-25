/**
 * Accessible tabs following the WAI-ARIA tabs pattern (arrow keys, Home, End).
 * @module tabs
 */

/**
 * @param {HTMLElement} tablist - Element with role="tablist".
 */
export function initTabs(tablist) {
  const tabs = [...tablist.querySelectorAll('[role="tab"]')];

  /** @param {number} index @param {boolean} focus */
  function select(index, focus) {
    tabs.forEach((tab, i) => {
      const selected = i === index;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      document.getElementById(tab.getAttribute('aria-controls')).hidden = !selected;
    });
    if (focus) tabs[index].focus();
  }

  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => select(i, false));
    tab.addEventListener('keydown', (event) => {
      const last = tabs.length - 1;
      const moves = { ArrowRight: i === last ? 0 : i + 1, ArrowLeft: i === 0 ? last : i - 1, Home: 0, End: last };
      if (event.key in moves) {
        event.preventDefault();
        select(moves[event.key], true);
      }
    });
  });
}
