# ScamShield — Frontend Architecture

## Folder Structure

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.app.json
├── package.json
├── FRONTEND_ARCHITECTURE.md
└── src/
    ├── main.tsx                    # Application entry point
    ├── App.tsx                     # Root component (providers + router)
    ├── index.css                   # Global styles + Tailwind v4 + theme
    ├── app/
    │   ├── router.tsx              # React Router configuration (lazy routes)
    │   └── providers.tsx           # TanStack Query provider setup
    ├── components/
    │   ├── ui/                     # shadcn-style presentational components
    │   │   ├── badge.tsx
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── input.tsx
    │   │   ├── label.tsx
    │   │   ├── skeleton.tsx
    │   │   └── textarea.tsx
    │   ├── error-boundary.tsx      # React error boundary
    │   ├── empty-state.tsx         # Empty state placeholder
    │   ├── retry-button.tsx        # Retry action button
    │   └── toast-container.tsx     # Toast notification display
    ├── features/                   # (reserved for feature modules)
    │   ├── analysis/
    │   ├── dashboard/
    │   ├── report/
    │   └── shared/
    ├── hooks/
    │   ├── use-scamshield.ts       # TanStack Query hooks for backend
    │   └── use-toast.ts            # Toast notification state hook
    ├── layouts/
    │   ├── root-layout.tsx         # Main layout (sidebar + header + outlet + footer)
    │   ├── sidebar.tsx             # Navigation sidebar
    │   ├── header.tsx              # Top bar with theme toggle
    │   └── footer.tsx              # Application footer
    ├── pages/
    │   ├── dashboard.tsx           # System overview with status cards
    │   ├── text-analysis.tsx       # Text analysis form + result
    │   ├── image-analysis.tsx      # Image upload form + result
    │   ├── system-status.tsx       # Health / ready / live / metrics display
    │   └── not-found.tsx           # 404 page
    ├── services/
    │   ├── api.ts                  # Axios instance, interceptors, error handling
    │   └── scamshield.ts           # Typed API functions matching backend endpoints
    ├── types/
    │   ├── index.ts                # Re-exports
    │   └── api.ts                  # TypeScript interfaces for backend responses
    └── utils/
        ├── cn.ts                   # className merge utility (clsx + tailwind-merge)
        └── validation.ts           # Zod validation schemas for forms
```

## Component Hierarchy

```
<App>
  <Providers>                          # TanStack QueryClientProvider
    <RouterProvider>                   # createBrowserRouter
      <RootLayout>                     # Sidebar | Header + Outlet + Footer
        <Sidebar />                    # Navigation links
        <Header />                     # Title + theme toggle
        <Outlet>                       # Lazy-loaded pages
          <Dashboard />                # /
          <TextAnalysis />             # /analyze/text
          <ImageAnalysis />            # /analyze/image
          <SystemStatus />             # /system
          <NotFound />                 # 404
        </Outlet>
        <Footer />
        <ToastContainer />             # Fixed-position notifications
      </RootLayout>
    </RouterProvider>
  </Providers>
</App>
```

## Routing

| Path | Page | Description |
|---|---|---|
| `/` | Dashboard | System overview, health, capabilities |
| `/analyze/text` | TextAnalysis | Submit text for scam analysis |
| `/analyze/image` | ImageAnalysis | Upload image for OCR + analysis |
| `/system` | SystemStatus | Health, readiness, metrics |
| `*` | NotFound | 404 catch-all |

All pages use lazy loading (`React.lazy` + `Suspense`) with skeleton fallbacks.

## API Layer

### Architecture

```
Pages/Hooks → TanStack Query (useQuery/useMutation) → scamshield.ts (typed functions) → api.ts (Axios) → Backend
```

### Key Design Decisions

- **No API calls inside components**: All API logic is in `services/scamshield.ts`.
- **TanStack Query for data fetching**: Automatic caching, refetching, retry, loading/error states.
- **Axios interceptors**: Global error handling converts backend errors to typed `Error` messages.
- **Proxy in dev**: Vite proxy forwards `/api/*` to `localhost:8000`.

### API Functions (`services/scamshield.ts`)

| Function | Endpoint | Cache |
|---|---|---|
| `analyzeText(text)` | POST /analyze/text | Mutation (no cache) |
| `analyzeImage(file)` | POST /analyze/image | Mutation (no cache) |
| `health()` | GET /health | 30s refetch |
| `ready()` | GET /ready | 30s refetch |
| `live()` | GET /live | 15s refetch |
| `metrics()` | GET /metrics | 10s refetch |

### Custom Hooks (`hooks/use-scamshield.ts`)

- `useHealth()`, `useReady()`, `useLive()`, `useMetrics()` — polling queries
- `useAnalyzeText()`, `useAnalyzeImage()` — mutations

## State Management

| Concern | Solution |
|---|---|
| Server state | TanStack Query (cache, refetch, mutations) |
| UI state | React `useState`, custom hooks |
| Theme | `useState` + localStorage + CSS class toggle |
| Toasts | `useToast` hook (ephemeral, 5s auto-dismiss) |
| Form state | React Hook Form-ready (vanilla `useState` for now) |

## Theming

- **Tailwind CSS v4** with `@tailwindcss/vite` plugin
- **CSS custom properties** for semantic colors (background, foreground, primary, etc.)
- **Dark mode**: `.dark` class on `<html>`, toggled by header button, persisted to localStorage
- **Consistent spacing**: Tailwind's default spacing scale
- **Typography**: Inter / system-ui stack, `-webkit-font-smoothing` antialiased

## Design Decisions

1. **shadcn-style components without Radix**: Created lightweight presentational components with `cva` for variants. Avoids additional dependency weight for this phase.

2. **Lazy-loaded pages**: All page components use `React.lazy` for code splitting. Initial bundle loads only the dashboard.

3. **Zod validation on frontend**: Text and image inputs validated client-side before submission. Schema matches backend limits (10K chars, 10 MB, supported MIME types).

4. **No result visualisation yet**: Analysis results show raw predictions and indicators. Advanced visualisation will be added in a future phase.

5. **No investigation report UI**: The `investigation_report` field exists in types but has no dedicated page yet.

6. **Responsive sidebar**: Sidebar is fixed-width (256px) on desktop. The layout supports responsive breakpoints for future mobile adaptation.

7. **Accessibility**: ARIA labels on interactive elements, semantic HTML, keyboard navigation for file upload, role attributes on dynamic content.

## Security

- No API keys or secrets in frontend code.
- Backend URL configurable via `VITE_API_BASE_URL` environment variable.
- File upload validated client-side (type, size) before submission.
- Axios interceptors sanitize error messages (Zod + custom).
- Content Security Policy should be configured at deployment (nginx response headers).

## Build & Development

```bash
cd frontend
npm run dev          # Development server on :5173
npm run build        # Production build to dist/
npm run preview      # Preview production build
npm run lint         # ESLint
```
