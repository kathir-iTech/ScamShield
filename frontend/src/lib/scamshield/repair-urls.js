// URL-repair pass: reconstruct URLs mangled by OCR (dropped/spaced punctuation)
// so the strict https?:// extractor inside pipeline.js can recognize them.
// Applied to OCR-extracted text BEFORE it enters the pipeline, on both JS and
// Python OCR paths, so OCR-engine differences don't silence URL phishing signals.

const SEG = /[a-z0-9][a-z0-9-]*/i;
// "http"/"htp"(+ typo variants hitp/htip) rarely appear inside a normal word,
// so no strict word boundary: lets OCR space-merges ("athttp"), letter-drops
// ("htp") and transpositions ("hitp","htip") still be seen as URL starts.
const ANCHOR_RE = /(?:https?|htps?|htp|hitp|htip)[\s:/.\\|_’‘]{0,4}/gi;

// Known/generic TLDs. A whitespace-separated trailing token may rejoin the host
// as a dotted TLD ONLY if it is in this set (e.g. OCR rendering "host.in" as
// "host in"). This avoids swallowing sentence prose that follows a URL.
const TLD_SET = new Set([
  "xyz", "in", "tk", "com", "co", "net", "org", "info", "io", "me", "tv",
  "us", "uk", "ca", "au", "de", "fr", "es", "it", "mx", "br", "ru", "top",
  "online", "site", "app", "store", "cloud", "live", "world", "club", "asia",
  "gov",
]);

const MAX_HOST_SEGMENTS = 6;
const NON_SPACE_SEP = /[.:/\\|’‘]/;

function isSegStart(c) {
  return !!c && /[a-z0-9]/i.test(c);
}

// Read one segment ([a-z0-9][a-z0-9-]*) starting at s[pos]; returns
// {seg, next} where next is the index just past the segment.
function readSeg(s, pos) {
  const m = SEG.exec(s.slice(pos));
  if (!m || m.index !== 0) return null;
  return { seg: m[0], next: pos + m[0].length };
}

function tryParseUrl(s, start) {
  const head = s.slice(start, start + 8).toLowerCase();
  let scheme;
  let j;
  if (head.startsWith("https")) {
    scheme = "https";
    j = start + 5;
  } else if (head.startsWith("http")) {
    scheme = "http";
    j = start + 4;
  } else if (head.startsWith("hitp") || head.startsWith("htip") || head.startsWith("htp")) {
    // OCR typos: hitp/htip (transposition) or htp (letter-drop)
    scheme = head.startsWith("htps") ? "https" : "http";
    j = start + 3;
    if (head.startsWith("hitp") || head.startsWith("htip")) j = start + 4;
  } else if (head.startsWith("www")) {
    scheme = "www";
    j = start + 3;
  } else {
    return null;
  }

  const n = s.length;
  // skip partially-eaten "://" and stray smart-quote artifacts
  let rp = s.slice(j, j + 16).match(/^[\s:/.\\|_’‘]*/);
  j += rp ? rp[0].length : 0;

  const segs = [];
  let k = j;

  // Always take the first host segment.
  const first = readSeg(s, k);
  if (!first) return null;
  segs.push(first.seg);
  k = first.next;

  while (segs.length < MAX_HOST_SEGMENTS) {
    // Case A: non-space separator(s) already consumed right after a segment,
    // meaning a real dotted/path continuation (http://a.b /c /d).
    // Case B: whitespace gap — possible missing dot before a TLD.
    let scroll = 0;
    while (k + scroll < n && NON_SPACE_SEP.test(s[k + scroll])) scroll++;

    if (scroll > 0 && k + scroll < n && isSegStart(s[k + scroll])) {
      // dot/slash-joined continuation
      k += scroll;
      const nxt = readSeg(s, k);
      segs.push(nxt.seg);
      k = nxt.next;
      continue;
    }

    // Not a dotted continuation. Check whitespace-separated TLD rejoin.
    if (k < n && /\s/.test(s[k])) {
      let w = k;
      while (w < n && /\s/.test(s[w])) w++;
      while (w < n && NON_SPACE_SEP.test(s[w])) w++; // stray '.' before TLD
      const nxt = readSeg(s, w);
      if (nxt && TLD_SET.has(nxt.seg.toLowerCase()) && segs.length >= 1) {
        segs.push(nxt.seg);
        k = nxt.next; // stop right after the TLD; do NOT consume following text
      }
    }
    break;
  }

  const host = segs.join(".");
  const url = scheme === "www" ? "www." + host : scheme + "://" + host;
  return { start, end: k, url };
}

function repairUrls(text) {
  if (!text || typeof text !== "string") return text;
  const replacements = [];
  let m;
  ANCHOR_RE.lastIndex = 0;
  while ((m = ANCHOR_RE.exec(text)) !== null) {
    const parsed = tryParseUrl(text, m.index);
    if (parsed && parsed.url && parsed.end > parsed.start) {
      replacements.push(parsed);
      ANCHOR_RE.lastIndex = Math.max(ANCHOR_RE.lastIndex, parsed.end);
    }
  }
  replacements.sort((a, b) => b.start - a.start);
  let out = text;
  for (const r of replacements) {
    // If the URL was merged into a preceding word (e.g. OCR turned "at http"
    // into "athttp"), restore the lost word boundary so downstream tokenization
    // and the strict extractor see a clean URL token.
    let prefix = "";
    if (r.start > 0 && /[\w]/.test(out[r.start - 1])) prefix = " ";
    out = out.slice(0, r.start) + prefix + r.url + out.slice(r.end);
  }
  return out;
}

export { repairUrls };
