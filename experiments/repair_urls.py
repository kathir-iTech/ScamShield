"""URL-repair pass mirroring repair_urls.js for the Python OCR path.

Reconstructs URLs mangled by OCR (dropped/spaced punctuation) so the strict
https?:// extractor can recognize them. Applied to OCR-extracted text BEFORE it
enters the pipeline so both OCR engines are treated consistently.
"""

import re

_SEG = re.compile(r"[a-z0-9][a-z0-9-]*", re.I)
# "http"/"htp"(+ typos hitp/htip) rarely appear inside a normal word, so no
# strict word boundary: catches OCR space-merges, letter-drops and transposes.
_ANCHOR_RE = re.compile(r"(?:https?|htps?|htp|hitp|htip)[\s:./\\|_\u2018\u2019]{0,4}", re.I)

# Known/generic TLDs (mirrors repair_urls.js).
_TLD_SET = frozenset({
    "xyz", "in", "tk", "com", "co", "net", "org", "info", "io", "me", "tv",
    "us", "uk", "ca", "au", "de", "fr", "es", "it", "mx", "br", "ru", "top",
    "online", "site", "app", "store", "cloud", "live", "world", "club", "asia",
    "gov",
})

_MAX_HOST_SEGMENTS = 6
_NON_SPACE_SEP = re.compile(r"[.:/\\|\u2018\u2019]")


def _is_seg_start(c):
    return bool(c and (c.isalnum()))


def _read_seg(s, pos):
    m = _SEG.match(s, pos)
    if not m:
        return None
    return {"seg": m.group(0), "next": m.end()}


def _try_parse_url(s, start):
    head = s[start:start + 8].lower()
    if head.startswith("https"):
        scheme, j = "https", start + 5
    elif head.startswith("http"):
        scheme, j = "http", start + 4
    elif head.startswith("hitp") or head.startswith("htip") or head.startswith("htp"):
        scheme = "https" if head.startswith("htps") else "http"
        j = start + 3
        if head.startswith("hitp") or head.startswith("htip"):
            j = start + 4
    elif head.startswith("www"):
        scheme, j = "www", start + 3
    else:
        return None

    n = len(s)
    rp = re.match(r"^[\s:./\\|_\u2018\u2019]*", s[j:j + 16])
    j += len(rp.group(0)) if rp else 0

    segs = []
    k = j

    first = _read_seg(s, k)
    if not first:
        return None
    segs.append(first["seg"])
    k = first["next"]

    while len(segs) < _MAX_HOST_SEGMENTS:
        scroll = 0
        while k + scroll < n and _NON_SPACE_SEP.match(s[k + scroll]):
            scroll += 1

        if scroll > 0 and k + scroll < n and _is_seg_start(s[k + scroll]):
            k += scroll
            nxt = _read_seg(s, k)
            segs.append(nxt["seg"])
            k = nxt["next"]
            continue

        if k < n and s[k].isspace():
            w = k
            while w < n and s[w].isspace():
                w += 1
            while w < n and _NON_SPACE_SEP.match(s[w]):
                w += 1
            nxt = _read_seg(s, w)
            if nxt and nxt["seg"].lower() in _TLD_SET and len(segs) >= 1:
                segs.append(nxt["seg"])
                k = nxt["next"]
        break

    host = ".".join(segs)
    url = ("www." + host) if scheme == "www" else (scheme + "://" + host)
    return {"start": start, "end": k, "url": url}


def repair_urls(text):
    if not text or not isinstance(text, str):
        return text
    replacements = []
    for m in _ANCHOR_RE.finditer(text):
        parsed = _try_parse_url(text, m.start())
        if parsed and parsed["url"] and parsed["end"] > parsed["start"]:
            replacements.append(parsed)
    replacements.sort(key=lambda r: r["start"], reverse=True)
    out = text
    for r in replacements:
        prefix = ""
        if r["start"] > 0 and out[r["start"] - 1].isalnum():
            prefix = " "
        out = out[:r["start"]] + prefix + r["url"] + out[r["end"]:]
    return out
