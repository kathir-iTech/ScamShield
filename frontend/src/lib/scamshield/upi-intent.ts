// UPI Intent parser — deterministic, zero network, offline
// Parses upi://pay?pa=...&am=... intents and bare VPA fallback.
// Never asserts RECEIVE without proof. UNKNOWN when amount missing.
// Handles QR prefixes QR_CODE_URL:/QR_CODE_UPI:/QR_CODE_TEXT:, OCR garbles like "upi : // pay ? pa = foo @ ybl & am = 1000",
// and spaces around ?, =, &, @.

export type UpiIntentMode = 'PAY' | 'COLLECT' | 'UNKNOWN';
export type UpiIntentKind = 'UPI_INTENT' | 'BARE_VPA';

export interface UpiIntent {
  raw: string;                // matched substring (normalized)
  kind: UpiIntentKind;        // UPI_INTENT = upi://, BARE_VPA = handle@bank
  mode: UpiIntentMode;        // PAY for pay, COLLECT for collect/request, UNKNOWN otherwise
  pa: string | null;          // payee VPA e.g. ramesh@okaxis
  pn: string | null;          // payee name
  am: string | null;          // amount raw string
  amount: number | null;      // parsed numeric or null
  cu: string | null;          // currency (INR)
  tn: string | null;          // transaction note
  tr: string | null;          // transaction ref
  handle: string | null;      // handle part after @ (e.g. ybl, okaxis)
  confidence: number;         // 0-1 for UI ranking (not model)
  source: string;             // always "upi_intent"
}

const UPI_HANDLES = new Set(["paytm","gpay","phonepe","axisbank","hdfcbank","icici","sbi","okicici","okaxis","ybl","ibl","apl","upi","fam","airtel","jio","freecharge","mobikwik"]);

function normalizeQrPrefixes(s: string): string {
  // Strip QR_CODE_* prefixes that scamshield.ts appends, preserving payload
  return s
    .replace(/QR_CODE_URL:\s*/gi, '')
    .replace(/QR_CODE_UPI:\s*/gi, '')
    .replace(/QR_CODE_TEXT:\s*/gi, '');
}

function normalizeUpiGarbles(s: string): string {
  // Normalize common OCR/spacing garbles before parsing
  // "upi : // pay" -> "upi://pay", "upi: // pay ?" -> "upi://pay?"
  // also collapse spaces around ?, =, &, @, ;
  let out = s;
  // collapse upi scheme spacing: allow upi with any spaces around : and //
  out = out.replace(/upi\s*:\s*\/\s*\/\s*/gi, 'upi://');
  // also handle bare "upi//" OCR drop of colon
  out = out.replace(/\bupi\s*\/\s*\/\s*/gi, 'upi://');
  return out;
}

function parseQueryToMap(qs: string): Map<string,string> {
  const map = new Map<string,string>();
  // qs may contain & or ; or &amp; or spaces; normalize
  const cleaned = qs
    .replace(/&amp;/gi, '&')
    .replace(/;/g, '&');
  // split on & (with optional surrounding spaces)
  const parts = cleaned.split(/&/);
  for (const p of parts) {
    const seg = p.trim();
    if (!seg) continue;
    // allow spaces around =
    const eqIdx = seg.indexOf('=');
    if (eqIdx === -1) continue;
    const k = seg.slice(0, eqIdx).trim().toLowerCase();
    let v = seg.slice(eqIdx + 1).trim();
    // remove leading/trailing spaces and decode
    try { v = decodeURIComponent(v.replace(/\+/g, ' ')); } catch { /* keep raw */ }
    // normalize VPA spacing: "foo @ ybl" -> "foo@ybl"
    if (k === 'pa') v = v.replace(/\s*@\s*/g, '@').replace(/\s+/g, '');
    else v = v.trim();
    if (k) map.set(k, v);
  }
  return map;
}

function parseAmount(raw: string | null): number | null {
  if (!raw) return null;
  const s = raw.trim().replace(/,/g, '');
  const n = parseFloat(s);
  if (Number.isNaN(n) || !Number.isFinite(n)) return null;
  if (n < 0 || n > 1e9) return null;
  return n;
}

function extractHandle(pa: string | null): string | null {
  if (!pa || !pa.includes('@')) return null;
  const parts = pa.split('@');
  return parts[1]?.toLowerCase() || null;
}

function isAllowedHandle(handle: string | null): boolean {
  if (!handle) return false;
  return UPI_HANDLES.has(handle.toLowerCase());
}

// Try to extract a single UPI intent from a normalized string
function tryParseSingleIntent(cand: string): UpiIntent | null {
  // cand is expected to be like "upi://pay?pa=foo@bar&pn=Name&am=500&..."
  // We already normalized leading "upi://"
  const lower = cand.toLowerCase();
  // detect mode from path segment after upi://
  let mode: UpiIntentMode = 'UNKNOWN';
  if (lower.startsWith('upi://pay')) mode = 'PAY';
  else if (lower.includes('upi://collect') || lower.includes('upi://request')) mode = 'COLLECT';
  else if (lower.startsWith('upi://')) {
    // unknown scheme but still treat as PAY if it has pa+am (safer to warn as PAY)
    // keep UNKNOWN but UI will still warn as PAY-like unknown amount if am missing
    mode = 'UNKNOWN';
  }
  // Find '?' boundary
  const qIdx = cand.indexOf('?');
  if (qIdx === -1) return null;
  const qs = cand.slice(qIdx + 1);
  // qs may contain trailing fragments after intent (extra text, spaces, newlines).
  // Cut at first whitespace + non-query char boundary? Query should be \S+ but garbles may have spaces.
  // We already collapsed scheme, but query may still contain spaces around & and = which we handle.
  // To avoid capturing following sentence, split qs at line break or at double-space + word not containing = &
  // Simpler: treat entire qs up to next "upi://" or end, but for now take whole qs and let parseQuery ignore trailing junk not containing =
  const map = parseQueryToMap(qs);
  const paRaw = map.get('pa') || null;
  if (!paRaw) return null;
  // Validate pa shape minimally: must contain @ and handle at least 3 chars
  if (!/^[a-z0-9._-]+@[a-z]{2,}$/i.test(paRaw)) return null;
  const handle = extractHandle(paRaw);
  // allow any handle for UI, but mark confidence lower if not in allowlist — still show warning
  const pn = map.get('pn') || null;
  const am = map.get('am') || null;
  const cu = map.get('cu') || null;
  const tn = map.get('tn') || null;
  const tr = map.get('tr') || map.get('tid') || map.get('txn') || null;
  const amount = parseAmount(am);

  // Determine final mode: if explicit collect, keep COLLECT; if pay or unknown with pa+am, keep PAY; else UNKNOWN
  let finalMode: UpiIntentMode = mode;
  if (finalMode === 'UNKNOWN') {
    // Heuristic: if text around intent contains "collect" + "request" words, mark COLLECT, else assume PAY for QR context
    // We keep UNKNOWN here; caller can refine with surrounding text outside.
    finalMode = 'PAY'; // safest for QR: warn as pay intent unless proven otherwise; UI will say "YOU WILL PAY" even without receive proof
    // But if qs contains mode-like keys or surrounding text indicates collect, caller can override; we default to PAY for UI safety
    // Exception: if mode was UNKNOWN and we have no am and no pn, still PAY-like unknown
  }
  if (mode === 'COLLECT') finalMode = 'COLLECT';

  return {
    raw: cand.trim(),
    kind: 'UPI_INTENT',
    mode: finalMode,
    pa: paRaw,
    pn,
    am,
    amount,
    cu,
    tn,
    tr,
    handle,
    confidence: isAllowedHandle(handle) ? 0.98 : 0.85,
    source: 'upi_intent',
  };
}

const UPI_INTENT_RE = /upi:\/\/[^\s]*\?[^\s]+/gi;
// Fallback for spaced garbles that survived normalization but still have spaces inside query (e.g. "upi://pay?pa=foo @ ybl & am=500")
// That RE above stops at whitespace, so "foo @" would break. We also try a more permissive capture that allows spaces inside value segments up to & or end.
const UPI_INTENT_SPACED_RE = /upi:\/\/\s*pay[^\n]*?pa\s*=\s*[^\n&]+/gi;

function extractUpiIntents(text: string): UpiIntent[] {
  if (!text || typeof text !== 'string') return [];
  const normalized = normalizeUpiGarbles(normalizeQrPrefixes(text));
  const out: UpiIntent[] = [];
  const seen = new Set<string>();
  const seenPaAmount = new Set<string>();

  function dedupKey(p: UpiIntent): string {
    // Use pa + numeric amount + mode to avoid duplicates from truncated vs full window
    // Do NOT use raw am string which may contain trailing junk ("100 and Pay 2")
    return (p.pa || '').toLowerCase() + '|' + (p.amount != null ? String(p.amount) : '__noamt') + '|' + p.mode;
  }

  // First pass: strict contiguous intents — use window to capture full query including spaced tn values
  let m: RegExpExecArray | null;
  const strictRe = new RegExp(UPI_INTENT_RE.source, UPI_INTENT_RE.flags);
  while ((m = strictRe.exec(normalized)) !== null) {
    // Use a 500-char window from match start to capture full query (handles tn with spaces)
    const start = m.index;
    let window = normalized.slice(start, start + 500);
    const nextUpi = window.indexOf('upi://', 6);
    if (nextUpi !== -1) window = window.slice(0, nextUpi);
    window = window.split('\n')[0];
    let cand = window.trim().replace(/[.,;:!?)"]+$/, '');
    // If the window was truncated by strict RE's whitespace stop but tn has spaces, window already includes them.
    // For spaced VPA like "pa=foo @ybl", ensure we keep it — tryParse handles via normalizeUpiGarbles again inside parseQuery
    // But if our strict m[0] was truncated at "pa=foo" without handle, fallback to extended cand already fixes.
    // If cand still lacks handle, try old extension logic as fallback
    if (cand.includes('pa=') && !/@[a-z]{2,}/i.test(cand)) {
      const tailSlice = normalized.slice(start + (m[0].length), start + (m[0].length) + 120);
      const contMatch = tailSlice.match(/^\s*@\s*[a-z]{2,}[^\s]*/i);
      if (contMatch) {
        cand = m[0] + contMatch[0];
        const afterAt = normalized.slice(start + cand.length, start + cand.length + 120);
        const extra = afterAt.match(/^[\s&;]*[a-z]{1,5}\s*=\s*[^\s&;]+(?:\s*&\s*[a-z]{1,5}\s*=\s*[^\s&;]+)*/i);
        if (extra) cand = cand + extra[0];
        strictRe.lastIndex = start + cand.length;
      } else {
        // No handle extension, keep window cand but ensure we don't produce truncated duplicate
        // If window cand parsed pa missing, we will skip; else keep window
      }
    }
    // Trim trailing " and ..." junk that is not part of query (e.g. "upi://pay?pa=a@ybl&am=100 and Pay 2")
    const andIdx = cand.indexOf(' and ');
    if (andIdx !== -1) {
      const beforeAnd = cand.slice(0, andIdx);
      if (beforeAnd.includes('pa=') && beforeAnd.includes('am=')) {
        const tnIdx = beforeAnd.indexOf('&tn=');
        const andAfterAm = andIdx > beforeAnd.indexOf('&am=');
        const hasTnAfterAnd = cand.indexOf('&tn=', andIdx) !== -1;
        if (andAfterAm && tnIdx === -1 && !hasTnAfterAnd) {
          cand = beforeAnd.trim();
          strictRe.lastIndex = start + cand.length;
        }
      }
    }
    const parsed = tryParseSingleIntent(cand);
    if (parsed) {
      const key = dedupKey(parsed);
      const seenKey = parsed.pa + '|' + (parsed.am || '') + '|' + parsed.mode; // also check raw for backward compat
      if (!seen.has(key) && !seen.has(seenKey) && !seenPaAmount.has(key)) {
        seen.add(key); seenPaAmount.add(key);
        // Also mark raw to prevent spaced pass duplicate
        seen.add(seenKey);
        out.push(parsed);
      }
    }
  }

  // Second pass: spaced garbles (allow spaces around @ and &)
  // This handles cases where strict RE cut early; we re-scan with a pattern that allows spaces
  const spacedRe = new RegExp(UPI_INTENT_SPACED_RE.source, UPI_INTENT_SPACED_RE.flags);
  while ((m = spacedRe.exec(normalized)) !== null) {
    // Capture up to end of line or next upi:// (approx 300 chars)
    const start = m.index;
    // Take 500 chars window from start, then normalize spaces inside query for parsing
    let window = normalized.slice(start, start + 500);
    // cut at line break or at next "upi://" beyond first
    const nextUpi = window.indexOf('upi://', 6);
    if (nextUpi !== -1) window = window.slice(0, nextUpi);
    // also cut at sentence terminator followed by capital word? keep simple: cut at newline
    window = window.split('\n')[0];
    let cand = window.trim().replace(/[.,;:!?)"]+$/, '');
    // Trim trailing junk after last key=value: keep only up to last "& key=value" and drop trailing "and Pay 2" etc.
    // Heuristic: if cand contains " and " after last &, drop trailing " and ..." unless it contains "="
    // We look for last "&" and check tail after it
    const lastAmp = cand.lastIndexOf('&');
    const lastEq = cand.lastIndexOf('=');
    if (lastAmp !== -1 && lastEq !== -1 && lastEq < lastAmp) {
      // malformed — ignore, will be handled by parse
    }
    // If tail after last value contains " and " without "=", trim tail from first " and " onward
    // This prevents "upi://pay?pa=a@ybl&am=100 and Pay 2:" becoming am="100 and Pay 2"
    // Detect " and " after the amount value's numeric prefix
    // Simpler: if cand contains " and " after a numeric am value, cut at " and "
    const andIdx = cand.indexOf(' and ');
    if (andIdx !== -1) {
      const beforeAnd = cand.slice(0, andIdx);
      // If beforeAnd already contains a complete intent (has pa= and am=), trim
      if (beforeAnd.includes('pa=') && beforeAnd.includes('am=')) {
        // Check if " and " is not part of tn value (tn would have &tn= before it)
        // If " and " appears after "&am=" but before next "&", it's trailing junk
        const tnIdx = beforeAnd.indexOf('&tn=');
        const andAfterAm = andIdx > beforeAnd.indexOf('&am=');
        const hasTnAfterAnd = cand.indexOf('&tn=', andIdx) !== -1;
        if (andAfterAm && tnIdx === -1 && !hasTnAfterAnd) {
          cand = beforeAnd.trim();
        }
      }
    }
    const parsed = tryParseSingleIntent(cand);
    if (parsed) {
      const key = dedupKey(parsed);
      const rawKey = parsed.pa + '|' + (parsed.am || '') + '|' + parsed.mode;
      if (!seen.has(key) && !seen.has(rawKey)) { seen.add(key); seen.add(rawKey); out.push(parsed); }
    }
    // Also try a collapsed-spaces candidate: replace "\s*=\s*" -> "=", "\s*@\s*" -> "@", "\s*&\s*" -> "&"
    const collapsed = cand.replace(/\s*=\s*/g, '=').replace(/\s*@\s*/g, '@').replace(/\s*&\s*/g, '&').replace(/\s+/g, ' ').trim();
    if (collapsed !== cand) {
      const p2 = tryParseSingleIntent(collapsed);
      if (p2) {
        const k2 = dedupKey(p2);
        const rawK2 = p2.pa + '|' + (p2.am || '') + '|' + p2.mode;
        if (!seen.has(k2) && !seen.has(rawK2)) { seen.add(k2); seen.add(rawK2); out.push(p2); }
      }
    }
  }

  return out;
}

// Bare VPA fallback: find handles@bank not already covered by intent pa
function extractBareVpas(text: string, alreadyPaSet: Set<string>): UpiIntent[] {
  const normalized = normalizeQrPrefixes(text);
  const out: UpiIntent[] = [];
  const seen = new Set<string>();
  const re = /\b[a-z0-9._-]+@[a-z]{3,}\b/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(normalized)) !== null) {
    const raw = m[0].toLowerCase();
    if (alreadyPaSet.has(raw)) continue;
    const handle = raw.split('@')[1] || '';
    if (!UPI_HANDLES.has(handle)) continue;
    if (seen.has(raw)) continue;
    seen.add(raw);
    out.push({
      raw,
      kind: 'BARE_VPA',
      mode: 'UNKNOWN',
      pa: raw,
      pn: null,
      am: null,
      amount: null,
      cu: null,
      tn: null,
      tr: null,
      handle: handle || null,
      confidence: 0.75,
      source: 'upi_intent',
    });
  }
  return out;
}

export function parseUpiIntents(text: string): UpiIntent[] {
  const intents = extractUpiIntents(text);
  const paSet = new Set(intents.map(i => (i.pa || '').toLowerCase()));
  const bare = extractBareVpas(text, paSet);
  // Intents first, then bare
  return [...intents, ...bare];
}

export function parseUpiIntent(text: string): UpiIntent | null {
  const all = parseUpiIntents(text);
  return all[0] || null;
}

// Helper for UI: format amount with INR
export function formatInr(amount: number | null | undefined): string | null {
  if (amount == null || Number.isNaN(amount)) return null;
  try {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(amount);
  } catch {
    return `Rs. ${amount}`;
  }
}

// Deterministic brand vs domain helper (light, no network)
// Used by Inspector when suspicious URL present but not as core feature
export function extractClaimedBrand(text: string): string | null {
  const brands = [
    { pat: /\b(hdfc|sbi|icici|axis|kotak|pnb|canara|bob|indusind|rbi|sebi)\b/i, canon: (m:string)=>m.toUpperCase() },
    { pat: /\b(gpay|phonepe|paytm|bhim|amazon pay)\b/i, canon: (m:string)=>m.toLowerCase() },
    { pat: /\b(india post|speed post|sarkari|government of india)\b/i, canon: (m:string)=>m },
  ];
  for (const b of brands) {
    const m = text.match(b.pat);
    if (m) return b.canon(m[1]);
  }
  return null;
}

export default { parseUpiIntents, parseUpiIntent, formatInr };