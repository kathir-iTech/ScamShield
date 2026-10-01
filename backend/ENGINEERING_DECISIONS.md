# Engineering Decisions

Record of the significant technical decisions behind ScamShield, why they were
made, and what was deliberately rejected. Newest decisions are at the top of
each section.

---

## 1. Password hashing: `bcrypt` directly

**Decision:** Use `bcrypt` as an explicit dependency and call it directly in
`core/auth/passwords.py`.

**Why:** `passlib` has been effectively unmaintained and ships a
`crypt`-module deprecation warning on Python 3.13+, which turns into a hard
failure on 3.16. Calling `bcrypt` directly removes that transitive risk, keeps
the dependency count at one, and matches what the library is actually for.

**Rejected:**
- `passlib` — maintenance risk, extra dependency, no benefit for our needs.
- `argon2-cffi` — stronger KDF, but a C extension that complicates the
  hardened, `read_only` Docker image. Revisit if we ever store server-side
  password material at scale.

**Trade-off accepted:** `bcrypt` truncates inputs at 72 bytes. Passwords are
length-validated at 8–128 characters upstream, well inside that limit for
practical input, and the pre-hash is documented in code.

---

## 2. Persistence: stdlib `sqlite3`, not an ORM

**Decision:** A small hand-written storage layer in `core/storage/`, with
`db.py` owning connections and `repositories.py` owning queries.

**Why:** ScamShield must run fully offline from a single container. SQLite in
WAL mode gives crash-safe durability and concurrent readers with zero
configuration and zero extra process. An ORM would have added a dependency,
a migration tool, and a second configuration surface for no query-complexity
benefit — every query here is a handful of rows against nine tables.

**Rejected:**
- SQLAlchemy + Alembic — right answer for PostgreSQL, wrong weight for an
  embedded single-file store.
- Redis as primary store — already used as a cache; using it as source of
  truth would make the app unusable offline.

**Concurrency contract:** connections are thread-local; reads take no lock;
writes are serialised by an `RLock` held across `BEGIN … COMMIT` so that
`RETURNING` reads stay consistent with the transaction that produced them.
`busy_timeout` is 5s. This replaced an earlier global lock that deadlocked
under the reliability concurrency suite.

---

## 3. Auth design: stateless access tokens + persistent refresh tokens

**Decision:** Short-lived JWT access tokens signed with a configurable secret,
plus opaque refresh tokens persisted in SQLite and individually revocable.

**Why:** Access tokens stay stateless so `/analyze` never touches the database
on the hot path. Revocation, which genuinely matters for "log out everywhere",
is pushed onto the refresh path where a single indexed lookup is irrelevant to
latency.

**Rejected:**
- Fully stateless refresh tokens — cannot revoke a stolen session.
- Fully stateful access tokens — a DB read on every analysis request.
- `python-jose` / `PyJWT` — see §4.

**Operational requirement:** `AUTH_JWT_SECRET` must be non-empty in
production; startup validation refuses to boot otherwise. Secrets are supplied
through the environment, never committed.

---

## 4. JWT: retain the in-repo implementation

**Decision:** Keep `core/auth/jwt.py` as a thin HS256 signer/verifier rather
than swapping in `PyJWT`.

**Why:** We only need one algorithm, one claim set, and no JWKs, X.509, or
asymmetric rotation. The implementation is deliberately narrow, covered by
tests that pin header/claim behaviour, and avoids a dependency whose API has
churned across major versions.

**Rejected:** `PyJWT`, `python-jose` — more surface than we use.

**Constraint:** if key rotation or asymmetric signing is ever required, this
decision must be revisited rather than extended in place.

---

## 5. Model thresholds: frozen

**Decision:** Decision thresholds live in `evaluation/thresholds.json` and are
consumed at inference; they are **not** to be re-tuned against the existing
gold set.

**Why:** `MODEL_STATUS.md` records the full-pipeline baseline at 308 samples
(FPR 14.06% / Recall 77.2%). Tuning against that same set would silently
optimise for it and destroy the signal the evaluation provides. Accuracy work
is therefore limited to infrastructure — gold-set pipeline, CI gate, scheduled
evaluation, active-learning queue — until more labelled data exists.

**Rejected:** threshold sweep in CI — would be self-confirming.

**Companion:** `evaluation/scripts/ci_gate.py` fails a build on metric
regression rather than on absolute value, so quality can only move one way.

---

## 6. Unicode normalisation: whitelist, not allow-all

**Decision:** `utils/text.py` restricts NFKC-normalised output to a known-safe
character set instead of accepting arbitrary normalised code points.

**Why:** entity extraction runs before classification, and homoglyph
substitution is a standard way to smuggle a phishing URL past both the rules
and the model. A whitelist fails closed: unknown characters are dropped rather
than passed through.

**Trade-off accepted:** rare legitimate characters are lost. Coverage of the
Indian-language and Latin sets in the whitelist is the mitigation.

---

## 7. Rate limiting: per-route budgets inside a global guard

**Decision:** `SlidingWindowRateLimitMiddleware` applies a coarse global
budget, while individual routes (registration, login) declare stricter limits
via `RateLimitRepo.hit()`.

**Why:** registration and credential endpoints need abuse-resistant budgets;
the general API surface does not. Encoding both in one place produced the bug
where the global guard overwrote the per-route `X-RateLimit-Limit` header with
its own much larger number.

**Fix:** headers are written with `setdefault`, so a route-specific limit wins
and the global value only appears when the route has none.

---

## 8. Documentation gating in production

**Decision:** `DocsRouteGuardMiddleware` serves `/docs`, `/redoc` and
`/openapi.json` only when explicitly enabled *and* the environment is not
`production` or `staging`.

**Why:** auto-generated API docs disclose the full attack surface. Development
keeps them because they are genuinely useful; production must not.

---

## 9. New channels: contracts, not implementations

**Decision:** WhatsApp, Telegram and Android SMS forwarding ship as
`scaffolds/*` documentation against the contracts in
`docs/CHANNEL_CONTRACTS.md`. The browser extension is a real implementation.

**Why:** the three bots each require an external provider account, credentials
and a review process that cannot be completed from inside this repository.
Shipping stub code that appears to work would be worse than shipping an honest
specification. The extension needs no third party, so it was built.
