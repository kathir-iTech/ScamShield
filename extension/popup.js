const DEFAULT_API_BASE = 'http://localhost:8000';

const apiBaseInput = document.getElementById('api-base');
const apiTokenInput = document.getElementById('api-token');
const saveButton = document.getElementById('save');
const scanButton = document.getElementById('scan');
const statusEl = document.getElementById('status');
const resultEl = document.getElementById('result');
const verdictEl = document.getElementById('result-verdict');
const confidenceEl = document.getElementById('result-confidence');
const categoryEl = document.getElementById('result-category');
const summaryEl = document.getElementById('result-summary');
const indicatorsEl = document.getElementById('result-indicators');

document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  loadLastScan();
  saveButton.addEventListener('click', () => {
    saveSettings().then(() => setStatus('Settings saved.', 'ok'));
  });
  scanButton.addEventListener('click', runScan);
});

function normalizeBase(value) {
  return String(value || DEFAULT_API_BASE).trim().replace(/\/+$/, '') || DEFAULT_API_BASE;
}

async function loadSettings() {
  try {
    const stored = await chrome.storage.sync.get({ apiBase: DEFAULT_API_BASE, apiToken: '' });
    apiBaseInput.value = stored.apiBase || DEFAULT_API_BASE;
    apiTokenInput.value = stored.apiToken || '';
  } catch (error) {
    setStatus(`Could not read settings: ${error.message}`, 'error');
  }
}

async function saveSettings() {
  const settings = {
    apiBase: normalizeBase(apiBaseInput.value),
    apiToken: apiTokenInput.value.trim(),
  };
  apiBaseInput.value = settings.apiBase;
  await chrome.storage.sync.set(settings);
  return settings;
}

async function loadLastScan() {
  try {
    const stored = await chrome.storage.local.get({ lastScan: null });
    if (stored.lastScan) renderResult(stored.lastScan);
  } catch (error) {
    setStatus(`Could not read the last scan: ${error.message}`, 'error');
  }
}

async function runScan() {
  scanButton.disabled = true;
  setStatus('Scanning…', '');
  try {
    await saveSettings();

    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const tab = tabs && tabs[0];
    if (!tab || tab.id === undefined || tab.id === null) {
      setStatus('No active tab found.', 'error');
      return;
    }

    const text = await getScanTarget(tab.id);
    if (!text) {
      setStatus('No text found on this page to scan.', 'error');
      return;
    }

    const response = await chrome.runtime.sendMessage({ type: 'scamshield:scan', text, tabId: tab.id });
    if (!response || !response.ok) {
      setStatus((response && response.error) || 'The scan failed.', 'error');
      return;
    }

    renderResult(response.result);
    setStatus('Scan complete.', 'ok');
  } catch (error) {
    setStatus(error && error.message ? error.message : 'The scan failed.', 'error');
  } finally {
    scanButton.disabled = false;
  }
}

async function getScanTarget(tabId) {
  try {
    const reply = await chrome.tabs.sendMessage(tabId, { type: 'scamshield:get-selection' });
    if (reply && reply.ok) return String(reply.text || '');
  } catch (error) {
    /* content script missing on this page — inject it and retry once */
  }

  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: ['content.js'] });
    const reply = await chrome.tabs.sendMessage(tabId, { type: 'scamshield:get-selection' });
    if (reply && reply.ok) return String(reply.text || '');
  } catch (error) {
    setStatus('This page does not allow extensions to read its text.', 'error');
  }
  return '';
}

function setStatus(message, kind) {
  statusEl.textContent = message;
  statusEl.className = kind || '';
}

function colorFor(riskLevel) {
  const level = String(riskLevel || '').toUpperCase();
  if (level === 'CRITICAL' || level === 'HIGH') return '#f87171';
  if (level === 'MEDIUM' || level === 'SUSPICIOUS') return '#fbbf24';
  if (level === 'LOW') return '#4ade80';
  return '#c9c9d4';
}

function renderResult(result) {
  if (!result) return;
  resultEl.classList.add('visible');

  verdictEl.textContent = result.prediction || result.risk_level || 'unknown';
  verdictEl.style.color = colorFor(result.risk_level);

  confidenceEl.textContent =
    typeof result.confidence === 'number' && Number.isFinite(result.confidence)
      ? `${Math.round(result.confidence * 100)}%`
      : '';

  categoryEl.textContent = result.scam_category ? `Category: ${result.scam_category}` : '';
  summaryEl.textContent = result.summary || '';

  indicatorsEl.innerHTML = '';
  const indicators = Array.isArray(result.detected_indicators) ? result.detected_indicators : [];
  indicators.forEach((indicator) => {
    const item = document.createElement('li');
    item.textContent = String(indicator);
    indicatorsEl.appendChild(item);
  });
}
