# ScamShield Master Audit — Report 08: Things Not to Build

**Date:** 2026-07-26

This is the most important report for engineering discipline. These are features that SHOULD NOT be built, based on current codebase evidence.

---

## 1. Microservices Architecture

**Do not:** Split the 12-stage pipeline into separate microservices.  
**Why not:** 
- The pipeline is sequential with tight data dependencies. Each stage reads and writes to a shared result dict.
- The system is ~10K lines — microservices would add Kubernetes complexity, network latency, serialization overhead, and distributed tracing requirements for zero benefit.
- Current limitations (sync processing, no caching) are solvable within the monolith.
- **There is no performance evidence that any single service is a bottleneck requiring isolation.**

## 2. Real-Time Streaming Engine

**Do not:** Add Kafka/PubSub event streaming.  
**Why not:**
- The system processes individual SMS messages on request. There is no event stream, no high-volume feed, no real-time requirement.
- The average latency is 200ms — well within acceptable range for SMS analysis.
- Adding streaming would require new infrastructure (Kafka cluster, schema registry, stream processors) for no use case benefit.
- If async processing is needed for investigations, use Celery or BackgroundTasks — not a full streaming platform.

## 3. Separate ML Serving Infrastructure

**Do not:** Deploy ML model as a separate Flask/FastAPI service with Docker.  
**Why not:**
- The model is a 41KB LogisticRegression with 192KB vectorizer — trivially small. Inference takes 45ms average.
- Network overhead of a separate service would likely exceed inference time.
- The current in-process approach is simpler, faster, and equally scalable (just add more app workers).
- If you need GPU inference later, consider ONNX Runtime in-process rather than a separate service.

## 4. User Authentication System (OAuth/SSO)

**Do not:** Build a full user authentication system with registration, login, password reset, OAuth providers.  
**Why not:**
- The question "who would use this?" is unanswered. Building auth before knowing the user model is premature.
- For API protection, a simple API key in header or query parameter is sufficient for v2.
- Adding user management (database, auth UI, session management, password policies) is 4-6 weeks of work that delays security fixes.
- **Build a simple API key system first, then add user auth only if a multi-user use case emerges.**

## 5. Database Persistence Layer

**Do not:** Add PostgreSQL/MySQL for storing analysis results.  
**Why not:**
- The system is currently stateless with no persistence requirement.
- Analysis results are returned to the client and not needed server-side after response.
- Adding a database adds deployment complexity, migration management, connection pooling, backup strategy, and operational burden.
- If historical analysis storage becomes necessary, start with a simple document store (SQLite) or log-based storage.

## 6. Duplicate Reasoning Engine

**Do not:** Build a separate "reasoning API" or "evidence graph service".  
**Why not:**
- `reasoning_service.py` (646 lines) and `evidence_service.py` (445 lines) already handle evidence correlation, graph building, and family classification.
- The evidence graph is tightly coupled to the rest of the pipeline — extracting it would require defining interfaces for all evidence types.
- The current implementation works. Focus on maintaining it, not re-architecting it.

## 7. Advanced ML Model Zoo

**Do not:** Add support for multiple ML models (BERT, GPT, LLaMA, etc.) as swappable backends.  
**Why not:**
- The current LogisticRegression model achieves 72.8% accuracy. Before adding model complexity, tune the existing model first.
- LLMs would add 100x+ latency and cost for uncertain accuracy improvement on scam SMS detection.
- A simple model with good features (TF-IDF char n-grams + word n-grams) often matches complex models on text classification.
- If you try other models, do it in evaluation notebooks, not as a production abstraction.

## 8. Plugin System for Scam Patterns

**Do not:** Build a plugin/DSL system for users to define custom scam patterns.  
**Why not:**
- The rule engine is 172 lines with 4 composite check functions. There is no evidence that external users need to define custom rules.
- A plugin system would require a pattern language, validation, sandboxed execution, and documentation — all for a use case that may not exist.
- If custom patterns are needed, users can submit PRs to `rules.py` or contribute to `core/constants.py`.

## 9. Mobile App (Android/iOS)

**Do not:** Build native mobile apps.  
**Why not:**
- Before building native apps, validate product-market fit with simpler interfaces (WhatsApp bot, Telegram bot, SMS forwarder).
- Native apps require platform-specific codebases, app store submissions, push notification infrastructure, and ongoing maintenance.
- The web dashboard works. Prove users want mobile access before investing in native development.

## 10. Multi-Tenancy / Organization Support

**Do not:** Add workspaces, teams, organizations, role-based access.  
**Why not:**
- The product has no users. Building multi-tenancy before knowing the user model is premature.
- This would require auth infrastructure (see #4), database (see #5), invitation flows, billing integration — months of work.
- When you understand who uses the system and how, you can design the right tenancy model.

## 11. Compliance Certifications (SOC2, ISO 27001)

**Do not:** Pursue formal security certifications.  
**Why not:**
- The system processes no user data (no accounts, no storage). Certification has no use case.
- The compliance paperwork alone would be more effort than the entire codebase.
- If enterprise customers require compliance, they'll ask for it — and that's the right time to start.

## 12. GraphQL API

**Do not:** Add a GraphQL endpoint alongside REST.  
**Why not:**
- The API has 6 endpoints with well-defined response shapes. No client needs to select specific fields.
- GraphQL adds complexity (resolvers, schemas, N+1 problems, caching complications) for no benefit.
- REST works fine for this use case. If clients need different response shapes, add query parameters to the REST API.

---

## Guiding Principle

Build things when there is evidence they are needed, not because they seem like good ideas. Every feature not built is time saved for improving accuracy, security, and reliability.

**If in doubt, don't build it.**
