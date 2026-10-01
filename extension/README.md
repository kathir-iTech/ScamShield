# ScamShield Browser Extension (MV3)

An **unofficial companion** to the ScamShield web app. It sends selected text (or the visible text of a page) to a
ScamShield API you control and shows the verdict.

> This extension is not published by, endorsed by, or affiliated with any official ScamShield distribution channel.
> It is a repo-local companion that talks to the same API as the web app. Nothing is sent anywhere except the API
> base URL you configure yourself.

## Load it unpacked

1. Open `chrome://extensions`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked** and select this `extension/` directory.
4. Pin "ScamShield" from the puzzle-piece menu if you want the popup one click away.

No build step is required: `manifest.json`, `background.js`, `content.js`, `popup.html`, and `popup.js` are plain
static files, and the manifest contains no remote code.

## Point it at an API

Open the popup and set:

| Field | Example | Notes |
| --- | --- | --- |
| API base URL | `http://localhost:8000` | Scheme + host + port only. No trailing slash, no path. The extension appends `/analyze/text`. |
| API token | `eyJhbGciOi...` | Optional. Sent as `Authorization: Bearer <token>` when non-empty. |

Settings are stored in `chrome.storage.sync`; the last scan is kept in `chrome.storage.local`.

**Local API** — run the backend on `http://localhost:8000` and keep the default base URL. The backend must allow the
extension origin in CORS (`SCAMSHIELD_CORS_ORIGINS`).

**Deployed API** — set the base URL to your HTTPS deployment, for example `https://api.example.com`. The token comes
from `POST /auth/login` or `POST /auth/token` against that same host.

## What you can do

- **Context menu** — select text on any page, right click, **Scan selection with ScamShield**.
- **Popup** — press **Scan page text**. It scans the current selection, or the visible page text when nothing is
  selected.
- The result appears in the popup (verdict, risk level, confidence, category, summary, indicators) and as a small
  non-blocking badge in the page. The badge disappears on the next scan and after 8 seconds.

## Permissions and why they are needed

| Permission | Why |
| --- | --- |
| `activeTab` | Read the selection/text of the tab you explicitly act on. |
| `storage` | Save the API base URL and optional token (`chrome.storage.sync`) and the last scan (`chrome.storage.local`). |
| `contextMenus` | Add the "Scan selection with ScamShield" right-click item. |
| `scripting` | Re-inject `content.js` into the active tab when the popup cannot reach it (e.g. after a manual reload). |
| `host_permissions` (`http://*/*`, `https://*/*`) | The API base URL is user-configurable and content scripts run on `<all_urls>`. |
| `content_scripts` on `<all_urls>` | Read the page text you asked to scan and show the result badge on that page. |

## Behaviour on errors

- **Offline / unreachable API** — "Could not reach the API at … Check the API base URL, CORS, and your connection."
- **401 / 403** — "Unauthorized — check the API token in the extension settings."
- **429** — "Too many requests — the API rate limit was hit. Wait a moment and try again."
- **404** — usually a wrong base URL that already contains a path.
- Pages that block extensions (`chrome://`, the Chrome Web Store, PDF viewer) show "This page does not allow extensions
  to read its text."

## Scope and privacy

- Only the text you scan leaves the browser, and only to the API base URL you configured.
- The badge is appended to `document.body` with `position: fixed` and `pointer-events: none`, so it never reflows or
  blocks clicks on the page.
- The content script is defensive: every DOM access is wrapped in `try/catch`, and a re-scan removes the previous
  badge and outline before adding a new one.
