// Inline SVG line icons. Every icon inherits `currentColor`.

const ICON_ATTRS =
  'xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" ' +
  'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"';

export const icons = {
  search: `<svg ${ICON_ATTRS}><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.6-3.6"/></svg>`,
  close: `<svg ${ICON_ATTRS}><path d="M6 6l12 12M18 6L6 18"/></svg>`,
  upload: `<svg ${ICON_ATTRS}><path d="M12 16V4M6 10l6-6 6 6"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></svg>`,
  file: `<svg ${ICON_ATTRS}><path d="M14 3H7a1.5 1.5 0 0 0-1.5 1.5v15A1.5 1.5 0 0 0 7 21h10a1.5 1.5 0 0 0 1.5-1.5V7.5z"/><path d="M14 3v4.5h4.5"/></svg>`,
  trash: `<svg ${ICON_ATTRS}><path d="M4 7h16"/><path d="M9 7V4.5A1.5 1.5 0 0 1 10.5 3h3A1.5 1.5 0 0 1 15 4.5V7"/><path d="M6.5 7l.8 12a1.5 1.5 0 0 0 1.5 1.4h6.4a1.5 1.5 0 0 0 1.5-1.4l.8-12"/><path d="M10 11v6M14 11v6"/></svg>`,
};

/** Fallback illustration: a cutting table drawn as two-tone line art. */
export const fallbackIllustration = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 110" fill="none" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
  <path d="M16 100 H184" stroke="#A1A1AA"/>
  <path d="M81 56 L74 70 M119 56 L126 70 M34 63 H166" stroke="#A1A1AA"/>
  <path d="M44 56 L156 56 L176 70 L24 70 Z" stroke="#27272A"/>
  <path d="M24 70 V82 H176 V70" stroke="#27272A"/>
  <path d="M34 82 L30 98 M166 82 L170 98" stroke="#27272A"/>
  <rect x="46" y="36" width="108" height="9" rx="1.5" stroke="#27272A"/>
  <path d="M54 45 L50 63 M146 45 L150 63" stroke="#27272A"/>
  <rect x="92" y="22" width="16" height="30" rx="2" stroke="#27272A"/>
  <path d="M97 52 H103 V58 H97 Z M100 58 V64" stroke="#27272A"/>
  <path d="M104 22 C104 8 121 8 121 20" stroke="#A1A1AA"/>
</svg>`;

/**
 * Build the illustration markup of a machine.
 *
 * @param {{name: string, illustration: string|null}} machine
 * @returns {string} An `<img>` when the machine has an illustration, the fallback SVG otherwise.
 */
export function illustrationMarkup(machine) {
  if (machine.illustration) {
    return `<img src="${escapeAttribute(machine.illustration)}" alt="" loading="lazy">`;
  }
  return fallbackIllustration;
}

/** Escape a string for safe use inside an HTML attribute. */
export function escapeAttribute(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
