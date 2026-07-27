# UX Audit Report — ScamShield v1.0.0

**Date:** July 2026  
**Auditor:** UX Engineering  
**Application:** ScamShield — AI-Powered Scam Detection Platform  
**Stack:** React 19 + TypeScript (frontend), FastAPI + Python (backend)

---

## 1. Executive Summary

ScamShield delivers a polished, task-oriented user interface for scam detection analysis, investigation, and reporting. The frontend maintains 244 passing unit tests and the underlying ML model achieves 83.3% benchmark accuracy. Navigation is intuitive, feedback states (loading, error, empty) are consistently handled, and dark mode is fully supported. The investigation workspace — the most complex surface — demonstrates strong architectural separation with skeleton loaders per tab and animated transitions. Areas for improvement centre on accessibility completeness (ARIA labelling on demo case cards, screen reader cues for tab state changes), graph state persistence across tab switches, and a missing hydration loading indicator. Overall the application scores well across all usability dimensions with minor refinements recommended.

---

## 2. Methodology

This audit employed three complementary evaluation methods:

- **Heuristic Evaluation** — Systematic inspection against Nielsen's 10 usability heuristics (visibility of system status, match with real world, user control and freedom, consistency and standards, error prevention, recognition over recall, flexibility and efficiency, aesthetic and minimalist design, help users recognise/diagnose/recover from errors, help and documentation).
- **WCAG 2.1 AA Accessibility Audit** — Conformance review covering perceivable (alt text, colour contrast, captions), operable (keyboard navigation, focus indicators, skip links, sufficient time), understandable (predictable behaviour, input assistance), and robust (ARIA, semantic markup) criteria.
- **Task Completion Testing** — Scripted walkthrough of ten core user tasks with pass/fail assessment, timing observations, and qualitative notes on friction points.

---

## 3. Task Completion Analysis

| # | Task | Result | Observations |
|---|---|---|---|
| a | Submit SMS text for analysis | **Pass** | Form validates with Zod, shows character count (10k limit), spinner on submit, inline error messages with `role="alert"`, and skeleton loader during processing. |
| b | Upload an image for analysis | **Pass** | Drag-and-drop zone with clear focus/active states, file type and size validation (10 MB max), preview thumbnail with remove button, spinner during OCR. |
| c | View analysis results | **Pass** | Rich multi-card layout with summary, classification, evidence, entities, threats, risk scores, recommendations, confidence breakdown, and full investigation report. Responsive grid adapts from single to two-column layout. |
| d | Navigate investigation workspace (Graph, Timeline, Campaigns, Report tabs) | **Pass** | Tab bar with icons and labels, animated transitions (Framer Motion `AnimatePresence`), per-tab skeleton loaders, descriptive sub-headers showing node/event/campaign counts. Tab switching resets graph layout state (see Issue #1). |
| e | Generate and export a report | **Pass** | Four template options (Technical, Executive, Law Enforcement, Customer Friendly) with live preview. Export buttons for copy-to-clipboard, JSON download, Markdown download, and Print/PDF. |
| f | Load a demo case | **Pass** | Demo panel displays six pre-built sample cases as cards with difficulty badges (beginner/intermediate/advanced), category tags, and descriptions. Simulated 800 ms loading delay. Cases populate full investigation workspace. Demo case cards lack visible labels for screen readers on difficulty/category (see Issue #2). |
| g | Walk through the guided tour | **Pass** | Six-step modal walkthrough with progress dots, Previous/Next navigation, and auto-tab-switching. Covers Graph, Timeline, Campaigns, Report Builder, Fusion Engine, and Final Assessment. Close button and overlay for dismissal. |
| h | Check system status | **Pass** | Four parallel queries (health, readiness, liveness, metrics) with skeleton loaders per card, error states with retry buttons, and rich dependency/resource/metrics display. Frontend diagnostics panel included. |
| i | Toggle dark/light mode | **Pass** | Header button with Sun/Moon icon, smooth CSS transition, persists to `localStorage`, respects `prefers-color-scheme` on first load. |
| j | Navigate via keyboard only | **Conditional Pass** | Skip-to-content link present, sidebar links are focusable `<NavLink>` elements, tab panels use `role="tab"` and `aria-selected`. Some investigation controls lack explicit tab stops (see Issue #5). |

---

## 4. UI Responsiveness

**Loading States:** Skeleton loaders are implemented at multiple granularities — full-page `PageSkeleton` variants (dashboard, analysis, report, system) in `Suspense` wrappers, per-tab skeletons (Graph, Timeline, Campaigns, Report) in the investigation workspace, and inline skeletons inside `SystemStatus` and `Dashboard` card bodies. All skeletons use `animate-pulse` and carry `aria-busy="true"` with descriptive labels.

**Tab Transitions:** Investigation tabs use `AnimatePresence mode="wait"` with 150 ms fade + vertical slide. The 200 ms simulated loading delay per tab shows a skeleton before content, preventing jarring instant-swaps. This also means the graph component unmounts and remounts on every tab switch, which resets zoom/pan state.

**Error States:** Consistent pattern across the app — error boundaries at layout level (`ErrorBoundary` wrapping `<Outlet />`), mutation error cards with retry buttons on analysis forms, query error states with inline retry on system status cards, and `ErrorPanel` UI component for reusable error display.

**Empty States:** The investigation page shows an `EmptyPanel` with icon, title, description, and two CTA buttons ("Analyze a URL or message" and "Browse Demo Cases"). The analysis result page renders an `EmptyAnalysisState` component when no current analysis exists. System status cards degrade gracefully with "info unavailable" text.

**Mobile/Tablet Layout:** Tailwind responsive grid classes used throughout (e.g., `grid-cols-1 lg:grid-cols-4` in investigation, `grid-cols-2 sm:grid-cols-3 lg:grid-cols-5` in metrics, `sm:grid-cols-2 lg:grid-cols-3` in demo panel). Investigation sidebar navigation is visible on desktop but has no hamburger/collapse on narrow viewports — sidebar remains fixed at `w-64` which may crowd smaller screens.

---

## 5. Accessibility Review (WCAG 2.1 AA)

| Criterion | Status | Notes |
|---|---|---|
| Skip-to-content link | **Pass** | Present in `RootLayout` at line 33, uses `sr-only focus:not-sr-only` pattern with visible focus ring. |
| ARIA labels on navigation | **Pass** | Sidebar `<nav>` has `aria-label="Main navigation"`. Header theme toggle has dynamic `aria-label="Switch to dark/light mode"`. Tab buttons use `role="tab"` and `aria-selected`. |
| Keyboard navigation | **Pass** | All interactive elements are reachable via Tab. Image upload drop zone handles `Enter` and `Space` keydown. Demo case cards handle `Enter` for selection. |
| Focus indicators | **Pass** | Custom focus-visible rings defined (`focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2`). Skip link has visible focus styles. |
| Colour contrast (dark mode) | **Pass** | Zinc palette (`zinc-50` on `zinc-950`, `zinc-900` on `zinc-50`) provides sufficient contrast in both modes. Emerald accent colours maintain 4.5:1+ ratio. |
| Screen reader compatibility | **Conditional Pass** | Demo case cards use `aria-label="Load {title}"` but difficulty and category badges are unstyled `<span>`/`<Badge>` elements without visible text alternatives. Tab content uses `aria-live="polite"` on character count but tab panel content region lacks `role="tabpanel"` and `aria-labelledby`. |

---

## 6. Issues Found

### Issue #1 — Tab switching resets graph state (Medium)
**Location:** `investigation.tsx:87-95`  
**Description:** Switching tabs in the investigation workspace unmounts the `GraphProvider` and `EvidenceGraph` components completely (via `AnimatePresence mode="wait"`). Any zoom level, pan position, or selected node is lost on return.  
**Observation:** The graph data is recalculated via `useMemo` dependencies but the interactive state (zoom, pan, selection) lives in `GraphProvider` internal state which is discarded on unmount.

### Issue #2 — Demo mode cases lack visible labels for screen readers (Low)
**Location:** `demo-panel.tsx:69-77`  
**Description:** Difficulty badges (`beginner`/`intermediate`/`advanced`) and category tags are rendered as styled `<Badge>` components with colour-only differentiation. Screen readers announce only the text content of these elements, but the colour-coded semantic meaning (beginner = green, advanced = red) is not conveyed textually. No `aria-label` or `aria-describedby` augments the visual-only distinction.

### Issue #3 — No loading indicator on initial page load before React hydrates (Medium)
**Location:** `frontend/index.html` (root div)  
**Description:** On first visit or slow networks, the page displays a blank white screen while the React bundle loads, parses, and hydrates. No CSS-only loading spinner or skeleton is rendered in the static HTML before the JS executes. The `Suspense` fallbacks only cover lazy-loaded route components after hydration.

### Issue #4 — Image analysis accepts oversized files without clear error (Low)
**Location:** `image-analysis.tsx:20-29`  
**Description:** The `imageAnalysisSchema` validates file size (max 10 MB) and type. If validation fails, the error message is shown in red text below the drop zone. However, if the backend enforces a stricter limit (e.g., Nginx `client_max_body_size`), the user receives a generic network error rather than a size-specific message. There is no client-side size warning prior to upload initiation.

### Issue #5 — Investigation report text is not focusable/scrollable in print (Low)
**Location:** `export-report.ts:70-94`  
**Description:** The print function opens a new window with inline styles. The report `div.section` uses `white-space: pre-wrap` but no `overflow` or `max-height` constraints are set for non-print contexts. More critically, the generated report body is not focusable — users relying on keyboard scrolling cannot navigate long exported reports in the print preview window.

---

## 7. Improvements Recommended

| Issue | Recommended Fix |
|---|---|
| 1 — Tab switching resets graph state | Lift graph viewport/selection state into the parent `Investigation` component (or a context) so it persists across tab switches. Pass `initialZoom`/`initialPan` props to `GraphProvider`. Alternatively, use CSS `display: none` instead of conditional rendering to keep the graph mounted. |
| 2 — Demo cases lack screen reader labels | Add visually hidden text (`.sr-only` span) inside badges with the semantic meaning, e.g., `<span class="sr-only">Difficulty: </span>` prepended to the badge text, or use `aria-description` on the badge container. |
| 3 — No pre-hydration loading indicator | Add a CSS-only centring spinner or skeleton in `index.html` inside the `<div id="root">` element, hidden via a class that React removes on first render. Example: inline SVG spinner with `display: flex` and `@media (scripting: enabled)` guard. |
| 4 — Oversized file upload error unclear | Add a human-readable file size hint below the upload area ("Max 10 MB — your file is X MB"). Compute and display the selected file size in real time before submit. Also check `Content-Length` against the backend limit and surface a translated error. |
| 5 — Report text not focusable/scrollable in print | Add `tabindex="0"` to the print window's report body container or set `document.body` as focus target before calling `win.print()`. Apply `max-height` and `overflow-y: auto` for screen rendering while keeping print style unconstrained. |

---

## 8. Usability Scorecard

| Area | Rating | Rationale |
|---|---|---|
| **Navigation** | 9/10 | Clear sidebar with icons and labels, consistent header, logical route hierarchy, skip-to-content link. Deducted for no mobile sidebar collapse. |
| **Task Completion** | 8/10 | All core tasks pass with clear feedback. Graph state loss across tabs is the main friction point. Demo case loading animation is slightly slow (800 ms). |
| **Accessibility** | 7/10 | Solid foundation (skip link, ARIA nav, keyboard support) but missing `role="tabpanel"`, hidden semantic labels on badges, and no pre-hydration fallback. |
| **Responsiveness** | 9/10 | Excellent skeleton coverage, smooth animated transitions, responsive grids, loading/error/empty states everywhere. Sidebar not collapsible on mobile. |
| **Learnability** | 8/10 | Guided tour walkthrough covers all investigation features. Consistent UI patterns. Terminology (confidence breakdown, fusion engine) may require domain familiarity. |
| **Error Prevention** | 7/10 | Zod validation on all inputs, disabled buttons during pending state, retry buttons on failures. Backend/client size limit mismatch is a gap. No confirmation dialog for destructive actions (clear analysis). |

---

*Report generated by the ScamShield UX Engineering team.*
