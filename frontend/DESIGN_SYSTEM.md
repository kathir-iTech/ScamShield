# ScamShield — Design System

## Tokens (`src/design/tokens.ts`)

| Token           | Values                                              |
|-----------------|-----------------------------------------------------|
| `spacing`       | 1, 2, 3, 4, 5, 6, 8, 10, 12 (multiply by 0.25rem) |
| `radius`        | sm: 0.375rem, md: 0.5rem, lg: 0.75rem, xl: 1rem    |
| `shadow`        | sm / md / lg                                        |
| `fontSize`      | xs / sm / base / lg / xl / 2xl / 3xl               |
| `fontWeight`    | normal / medium / semibold / bold                   |
| `animation`     | fast: 150ms, normal: 200ms, slow: 300ms             |
| `iconSize`      | sm: 16, md: 20, lg: 24                              |
| `layout`        | maxContent: 1440px, sidebarWidth: 256px              |

## Status System (`src/design/status.ts`)

Seven status functions returning `{ variant, icon, label }`:

- `riskStatus(level)` — critical/high/medium/low/very low
- `decisionStatus(action)` — block/review/monitor/allow
- `priorityStatus(priority)` — critical/high/medium/low
- `assessmentStatus(band)` — immediate action / investigation / assessment required / normal
- `severityStatus(severity)` — critical/high/medium/low/info
- `confidenceStatus(level)` — very high/high/medium/low/very low
- `predictionStatus(prediction)` — scam/not scam/suspicious

## Component Library (`src/components/ui/`)

| Component        | Purpose                                                    |
|------------------|------------------------------------------------------------|
| `StatusBadge`    | Consumes `StatusConfig`; variant-coloured badge with icon  |
| `Section`        | Title + description + children wrapper (`section`/`div`)   |
| `Metric`         | Label + value + optional icon, size variants               |
| `InfoRow`        | Label/value in `flex justify-between` row                  |
| `CopyButton`     | Clipboard API copy with checkmark feedback (1.5s)          |
| `EmptyPanel`     | Icon + title + description + action slot                   |
| `PageSkeleton`   | 4 variants: dashboard, analysis, report, system            |
| `ErrorPanel`     | 5 types: validation, network, unavailable, timeout, unexpected |
| `PageTransition` | Framer Motion fade+slide wrapper (0.2s easeOut)           |

## Motion Guidelines

- Keep animations under 0.3s (prefer 0.15–0.25s).
- Use `easeOut` for enter, `easeInOut` for state changes.
- Respect `prefers-reduced-motion` via Framer Motion's `reduceMotion`.
- Stagger children at 0.05–0.08s intervals for list/group entries.

## Accessibility

- All color combinations meet WCAG AA (AAA where practical).
- Interactive roles on non-button clickable elements.
- `aria-label` / `aria-describedby` on inputs, icons, buttons.
- Error states use `role="alert"`.

## Responsive Breakpoints

- 320px–640px: single column, compact spacing.
- 768px: 2-column grid for cards.
- 1024px: 3–4 column grid, full content width.
- Max content width: 1440px.
