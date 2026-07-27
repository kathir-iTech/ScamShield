# Frontend State Report

**Date**: 2026-07-26

---

## 1. Overview

The frontend is a React 18 SPA with TypeScript strict mode, React Router v6, TanStack React Query v5, and axios HTTP client. It uses feature-based directory organization with lazy-loaded routes.

---

## 2. Pages

| Route | Component | Status | Notes |
|---|---|---|---|
| `/` | `landing.tsx` | **Complete** | Hero, metrics, features, architecture diagram, tech stack, FAQ, CTA, GitHub buttons |
| `/dashboard` | `dashboard.tsx` | Built | Analytics/metrics overview |
| `/analyze/text` | `text-analysis.tsx` | Built | Text input for scam analysis |
| `/analyze/image` | `image-analysis.tsx` | Built | Image upload + OCR analysis |
| `/analysis/result` | `analysis-result.tsx` | Built | Analysis result display |
| `/investigation` | `investigation.tsx` | Built | Multi-artefact investigation |
| `/system` | `system-status.tsx` | Built | Health/metrics dashboard |
| `*` | `not-found.tsx` | Built | 404 page |
| `/deployment-health` | `deployment-health.tsx` | Present | Additional health view |

---

## 3. Feature Modules

### 3.1 Analysis (`features/analysis/`)
- 13 display components (summary, assessment, category, confidence, entity, evidence, recommendation, risk, technical, threat, timeline cards)
- 1 custom hook (`use-analysis-navigation`)
- 1 context module
- 1 types definition
- Architecture documentation (`ANALYSIS_UI_ARCHITECTURE.md`)

**Quality**: Well-factored with clear component separation. Each card handles a specific analysis section.

### 3.2 Graph (`features/graph/`)
- 7 components: `evidence-graph.tsx`, `graph-context.tsx`, `graph-edge.tsx`, `graph-node.tsx`, `graph-toolbar.tsx`, `legend.tsx`, `node-details-panel.tsx`
- Custom hooks, types, utils

**Quality**: Well-modularized with D3 or Canvas-based graph rendering. Context provider pattern for state sharing.

### 3.3 Report (`features/report/`)
- 2 components: `report-builder.tsx`, `report-section-view.tsx`
- Types and utilities

**Quality**: Minimal — report builder and section viewer. Investigation report rendering lives here.

### 3.4 Timeline (`features/timeline/`)
- 5 components: `campaign-view.tsx`, `event-detail-panel.tsx`, `investigation-timeline.tsx`, `timeline-controls.tsx`, `timeline-event.tsx`
- Types, utils

**Quality**: Well-structured for investigation timeline visualization.

### 3.5 Demo (`features/demo/`)
- `demo-panel.tsx`, `demo-walkthrough.tsx`
- Sample cases data (`sample-cases.ts`)

**Quality**: Demo/walkthrough for showcasing capabilities.

### 3.6 Shared (`features/shared/`)
- `investigation-skeleton.tsx` — Loading skeleton

**Quality**: Minimal shared module.

---

## 4. State Management

| State Type | Solution | Notes |
|---|---|---|
| Server state | `@tanstack/react-query` (useQuery/useMutation) | Health polls every 30s, live every 15s, metrics every 10s |
| Client state | `useState` | Toast notifications, navigation |
| React Context | Used in graph module | `graph-context.tsx` |
| No global store | — | No Zustand/Redux/Jotai |

---

## 5. Routing

- `react-router-dom` v6 with `createBrowserRouter`
- All pages lazy-loaded with `React.lazy()` + `Suspense`
- `PageSkeleton` loading states per variant (dashboard, analysis, report, system)
- Root layout wraps all routes (sidebar + header + footer)

---

## 6. API Integration

- `api.ts`: Axios instance with base URL from env var, interceptors for error recording
- `scamshield.ts`: 6 API functions (analyzeText, analyzeImage, health, ready, live, metrics)
- `use-scamshield.ts`: React Query hooks wrapping all API functions

---

## 7. Issues & Gaps

### Critical:
- **No comprehensive page-level tests** — landing, analysis, investigation pages untested
- **No E2E tests** — no Playwright/Cypress configuration

### Major:
- **No global state management** — investigation data sharing between pages relies on prop drilling or URL state
- **Toast system is basic** — module-level counter, no animation library
- **No error boundary per route** — single `error-boundary.tsx`, not applied to lazy routes
- **No responsive design verification** — mobile layout unknown

### Minor:
- `dashboard` feature directory is empty (no components)
- `analysis-result.tsx` re-renders on every keystroke in parent? (not verified)
- No PWA support (manifest, service worker)
- No accessibility audit beyond UX_AUDIT.md
- Bundle not analyzed for tree-shaking opportunities

---

## 8. Recommendations

1. **Add page-level tests** with React Testing Library for all 9 pages
2. **Add Playwright E2E** tests for critical user flows (analyze → view result)
3. **Wrap lazy routes** with error boundaries
4. **Consider Zustand** for shared investigation/results state
5. **Verify responsive design** — test mobile layouts
6. **Add bundle analysis** — use `vite-bundle-analyzer`
7. **Add PWA support** — manifest + service worker for offline capability
8. **Improve toast system** — use react-hot-toast or Sonner
