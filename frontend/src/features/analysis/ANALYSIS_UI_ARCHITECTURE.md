# Analysis UI Architecture

## Component Hierarchy

```
AnalysisResult
├── AnalysisSummaryCard        # Section 1: Executive Summary (prediction, confidence, risk, assessment)
├── CategoryCard               # Section 2: Scam Classification (category, summary, reasons)
├── AssessmentCard             # Section 2: Assessment (band, score, confidence, summary)
├── EvidenceCard               # Section 3: Evidence (supporting + conflicting)
├── EntityCard                 # Section 4: Detected Entities (grouped by type)
├── ThreatCard                 # Section 5: Threat Intelligence (threats, indicators, risk breakdown)
├── RiskScoreCard              # Section 5: Risk & Scoring (rule score, decision score, risk level)
├── RecommendationCard         # Section 6: Recommended Actions (immediate actions, review)
├── ConfidenceCard             # Section 6: Confidence Breakdown (ML, rules, entities, explanation)
├── TimelineCard               # Section 7: Investigation Timeline (vertical timeline)
├── TechnicalDetailsCard       # Section 8: Technical Details (ML conf, scores, counts)
└── ReportSummaryCard          # Section 9: Full Investigation Report (raw report data)
```

## Data Flow

```
TextAnalysis/ImageAnalysis
  → useAnalyzeText / useAnalyzeImage (TanStack Query mutation)
  → navigateToResult (useAnalysisNavigation hook)
    → AnalysisContext.storeAnalysis()   # stores result in React context
    → router.navigate('/analysis/result')
      → AnalysisResult page
        → useCurrentAnalysis()          # reads from context
        → passes typed props to each card component
```

```
User Input → API Call → Context Store → Route Nav → Read Context → Render Cards
```

## State Transitions

```
IDLE ──submit──▶ LOADING ──success──▶ NAVIGATE_TO_RESULT
                      │
                      └──error──▶ ERROR (inline error card with Retry)
                                  │
                                  └──retry──▶ LOADING
```

- **IDLE**: Form displayed, no analysis in progress
- **LOADING**: Skeleton cards shown during API call
- **NAVIGATE_TO_RESULT**: On success, result stored in context, page navigated to `/analysis/result`
- **ERROR**: Error card shown with retry button on the form page (not result page)

On the result page itself:
- **Has result**: Full investigation dashboard rendered
- **No result (null)**: EmptyAnalysisState with links to submit pages

## Component Design Principles

### Single Responsibility
Each card component receives only the props it needs. No card accesses context or external state directly. Components are pure functions of their props.

### Performance
- `RiskScoreCard`, `EvidenceCard`, `EntityCard`, `ThreatCard`, `ConfidenceCard` use `React.memo` to avoid re-renders when parent state changes but props haven't.
- Analysis result page reads from context once (no re-render cascades).
- All pages lazy-loaded via `React.lazy`.

### Accessibility
- Each section in the result page has an `aria-label` for screen reader navigation.
- Semantic heading hierarchy (`h2` for page title, `h3` for card titles via `CardTitle`).
- Colour is not the only indicator of severity — text labels accompany coloured badges.
- ARIA roles on dynamic content areas (`role="alert"` for errors).
- Keyboard accessible: all interactive elements are buttons or links.

### Visual Design
- Cards with consistent `rounded-xl`, shadow, border styling.
- Semantic colours only:
  - **Green** (emerald): safe, success, positive indicators
  - **Amber** (warning): medium risk, caution
  - **Red** (destructive): scam, critical, high risk
  - **Blue** (info): neutral information
  - **Grey** (zinc): secondary text, backgrounds
- No gradients, no glassmorphism, no decorative animations.
- Information hierarchy: most important metrics (prediction, confidence, risk) top-left in summary card.

### Responsiveness
- Single-column on mobile, 2-column on tablet (`md:grid-cols-2`), 2-column on desktop (`lg:grid-cols-2`).
- Summary card uses 5-column grid on desktop, single column on mobile.
- Entity badges wrap naturally. Evidence items stack vertically.
- No horizontal scrolling at any breakpoint.

### Error Handling
- API errors show inline error cards with retry button on form pages.
- Empty state shown when navigating directly to `/analysis/result` without a stored result.
- React ErrorBoundary wraps the entire layout outlet to catch unexpected render errors.

## Card Components Reference

| Component | Props Source | Memo'd | Section |
|---|---|---|---|
| `AnalysisSummaryCard` | prediction, confidence, riskLevel, assessmentBand, assessmentScore | No | Executive Summary |
| `CategoryCard` | scamCategory, summary, reasons, businessReason, technicalReason | No | Scam Classification |
| `AssessmentCard` | assessmentScore, assessmentBand, assessmentConfidence, assessmentSummary, businessReason, technicalReason | No | Assessment |
| `EvidenceCard` | supporting[], conflicting[] | Yes | Evidence |
| `EntityCard` | entities[] | Yes | Entities |
| `ThreatCard` | threats[], detectedIndicators[], decisionLevel, recommendedPriority, riskBreakdown | Yes | Threat Intelligence |
| `RiskScoreCard` | ruleScore, ruleLabel, decisionScore, decisionLevel, riskLevel, scamCategory | Yes | Risk & Scoring |
| `RecommendationCard` | recommendedActions[], suggestedAction, recommendedAction, reviewRequired, manualReviewReason | No | Recommended Actions |
| `ConfidenceCard` | ml, rules, entities, explanation, overall | Yes | Confidence Breakdown |
| `TimelineCard` | steps[] (optional, defaults to 5 completed steps) | No | Investigation Timeline |
| `TechnicalDetailsCard` | mlConfidence, decisionScore, ruleScore, assessmentScore, evidenceCount, entityCount | No | Technical Details |
| `ReportSummaryCard` | report (Record<string, unknown>) | No | Investigation Report |
| `EmptyAnalysisState` | none | - | (fallback) |
| `AnalysisLoadingState` | none | - | (loading) |
| `AnalysisErrorState` | message, onRetry, onReset | - | (error) |

## Context API

`AnalysisContext` stores the 20 most recent analyses in memory. It is not persisted across page reloads. This is intentional — analysis results are ephemeral and retrieved fresh from the backend as needed.

```typescript
interface AnalysisContextValue {
  current: StoredAnalysis | null;          // most recent analysis
  history: StoredAnalysis[];               // up to 20 previous analyses
  storeAnalysis: (...) => string;          // stores and returns ID
  clearCurrent: () => void;
}
```
