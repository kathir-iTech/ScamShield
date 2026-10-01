const MENU_ID = 'scamshield-scan-selection';
const DEFAULT_API_BASE = 'http://localhost:8000';

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: MENU_ID,
      title: 'Scan selection with ScamShield',
      contexts: ['selection'],
    });
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId !== MENU_ID) return;
  const text = (info.selectionText || '').trim();
  if (!text) return;
  scanText(text, tab && tab.id);
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || typeof message !== 'object') return false;
  if (message.type === 'scamshield:scan') {
    scanText(message.text || '', message.tabId)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: describeError(error) }));
    return true;
  }
  if (message.type === 'scamshield:ping') {
    sendResponse({ ok: true });
    return false;
  }
  return false;
});

async function getSettings() {
  const stored = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE, apiToken: '' });
  const apiBase = String(stored.apiBase || DEFAULT_API_BASE).trim().replace(/\/+$/, '');
  return { apiBase, apiToken: String(stored.apiToken || '').trim() };
}

async function scanText(text, tabId) {
  const content = (text || '').trim();
  if (!content) {
    return { ok: false, error: 'No text to scan. Select some text on the page first.' };
  }

  const { apiBase, apiToken } = await getSettings();
  const headers = { 'Content-Type': 'application/json' };
  if (apiToken) headers.Authorization = `Bearer ${apiToken}`;

  let response;
  try {
    response = await fetch(`${apiBase}/analyze/text`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ text: content.slice(0, 10000) }),
    });
  } catch (_error) {
    return {
      ok: false,
      error: `Could not reach the API at ${apiBase}. Check the API base URL, CORS, and your connection.`,
    };
  }

  if (!response.ok) {
    return { ok: false, error: describeHttpError(response.status), status: response.status };
  }

  let payload;
  try {
    payload = await response.json();
  } catch (_error) {
    return { ok: false, error: 'The API returned a response that was not valid JSON.' };
  }

  const result = summarize(payload);
  await chrome.storage.local.set({ lastScan: { ...result, scannedAt: Date.now() } });

  if (tabId) {
    try {
      await chrome.tabs.sendMessage(tabId, { type: 'scamshield:scan-result', result });
    } catch (_error) {
      /* the content script is not reachable on this page — the popup still shows the result */
    }
  }

  return { ok: true, result };
}

function summarize(payload) {
  return {
    prediction: String(payload.prediction || 'unknown'),
    risk_level: String(payload.risk_level || 'UNKNOWN'),
    confidence: typeof payload.confidence === 'number' ? payload.confidence : null,
    scam_category: String(payload.scam_category || ''),
    summary: String(payload.summary || ''),
    detected_indicators: Array.isArray(payload.detected_indicators) ? payload.detected_indicators.slice(0, 8) : [],
  };
}

function describeHttpError(status) {
  if (status === 401 || status === 403) {
    return 'Unauthorized — check the API token in the extension settings.';
  }
  if (status === 404) {
    return 'Endpoint not found — check the API base URL (it should not include /analyze/text).';
  }
  if (status === 429) {
    return 'Too many requests — the API rate limit was hit. Wait a moment and try again.';
  }
  if (status >= 500) {
    return 'The API server returned an error. Try again shortly.';
  }
  return `The API rejected the request (HTTP ${status}).`;
}

function describeError(error) {
  if (error && error.message) return error.message;
  return 'The scan failed for an unknown reason.';
}
