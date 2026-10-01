const BADGE_ID = 'scamshield-badge';
const HIGHLIGHT_ATTR = 'data-scamshield-highlight';
const OUTLINE_ATTR = 'data-scamshield-outline';
const MAX_PAGE_CHARS = 4000;

if (!globalThis.__scamshieldContentRegistered) {
  globalThis.__scamshieldContentRegistered = true;
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || typeof message !== 'object') return false;

    if (message.type === 'scamshield:get-selection') {
      try {
        sendResponse({ ok: true, text: getScanTarget() });
      } catch (error) {
        sendResponse({ ok: false, error: String(error && error.message ? error.message : error) });
      }
      return false;
    }

    if (message.type === 'scamshield:scan-result') {
      try {
        showResult(message.result);
      } catch (error) {
        console.warn('ScamShield: could not display the scan result', error);
      }
      return false;
    }

    return false;
  });
}

function getScanTarget() {
  try {
    const selection = window.getSelection();
    const selected = selection ? String(selection).trim() : '';
    if (selected) return selected.slice(0, 10000);
  } catch (_error) {
    /* fall through to page text */
  }
  try {
    const body = document.body;
    const text = body && body.innerText ? body.innerText : '';
    return text.replace(/\s+/g, ' ').trim().slice(0, MAX_PAGE_CHARS);
  } catch (_error) {
    return '';
  }
}

function findAnchorElement() {
  try {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) return null;
    const range = selection.getRangeAt(0);
    let node = range.commonAncestorContainer;
    if (node && node.nodeType === Node.TEXT_NODE) node = node.parentNode;
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return null;
    const element = node;
    return element.closest('p, li, td, th, dd, dt, blockquote, pre, a, span, div') || element;
  } catch (_error) {
    return null;
  }
}

function clearPrevious() {
  try {
    const badge = document.getElementById(BADGE_ID);
    if (badge && badge.parentNode) badge.parentNode.removeChild(badge);
    const marked = document.querySelectorAll(`[${HIGHLIGHT_ATTR}]`);
    marked.forEach((element) => {
      const previous = element.getAttribute(OUTLINE_ATTR) || '';
      element.style.outline = previous;
      element.removeAttribute(HIGHLIGHT_ATTR);
      element.removeAttribute(OUTLINE_ATTR);
    });
  } catch (_error) {
    /* nothing to clean up */
  }
}

function toneFor(riskLevel) {
  const level = String(riskLevel || '').toUpperCase();
  if (level === 'CRITICAL' || level === 'HIGH') return { background: '#dc2626', color: '#ffffff' };
  if (level === 'MEDIUM' || level === 'SUSPICIOUS') return { background: '#d97706', color: '#ffffff' };
  if (level === 'LOW') return { background: '#16a34a', color: '#ffffff' };
  return { background: '#3f3f46', color: '#ffffff' };
}

function showResult(result) {
  if (!result) return;
  clearPrevious();

  const anchor = findAnchorElement();
  if (anchor) {
    try {
      anchor.setAttribute(OUTLINE_ATTR, anchor.style.outline || '');
      anchor.setAttribute(HIGHLIGHT_ATTR, 'true');
      anchor.style.outline = '2px solid #6366f1';
    } catch (_error) {
      /* highlighting is best effort */
    }
  }

  const badge = document.createElement('div');
  badge.id = BADGE_ID;
  badge.setAttribute('role', 'status');
  const tone = toneFor(result.risk_level);
  const confidence =
    typeof result.confidence === 'number' && Number.isFinite(result.confidence)
      ? ` · ${Math.round(result.confidence * 100)}%`
      : '';
  badge.textContent = `ScamShield · ${result.risk_level || 'UNKNOWN'}${confidence}`;

  badge.style.cssText = [
    'position:fixed',
    'top:12px',
    'right:12px',
    'z-index:2147483647',
    'padding:6px 10px',
    'border-radius:9999px',
    'font:600 12px/1.2 system-ui, -apple-system, sans-serif',
    `background:${tone.background}`,
    `color:${tone.color}`,
    'box-shadow:0 4px 14px rgba(0,0,0,0.35)',
    'pointer-events:none',
    'max-width:60vw',
    'overflow:hidden',
    'text-overflow:ellipsis',
    'white-space:nowrap',
  ].join(';');

  try {
    document.body.appendChild(badge);
  } catch (_error) {
    return;
  }

  setTimeout(() => {
    try {
      const current = document.getElementById(BADGE_ID);
      if (current && current.parentNode) current.parentNode.removeChild(current);
    } catch (_error) {
      /* already gone */
    }
  }, 8000);
}
