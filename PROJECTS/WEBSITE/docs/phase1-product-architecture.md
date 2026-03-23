# Prompts Vault — Phase 1: Product & System Design

**Backend resolution:** The project brief mandates **Python** with Clean Architecture. A later section references Go; this plan uses **Python 3.12+** and **FastAPI** (async, OpenAPI, strong typing). Layers remain **handler → service → repository**.

---

## 1. Core features

| Area | Features |
|------|----------|
| **Library** | Hierarchical categories, tags, techniques (zero-shot, few-shot, CoT, etc.), full-text search + filters, prompt detail with copy/export |
| **Accounts** | Register/login, profile, saved prompts, submission history |
| **Contributions** | Submit prompts, moderation queue (pending/approved/rejected), incentives (e.g. tier discounts after N approved) |
| **Monetization** | Free + 3 paid tiers, feature gating (saved limit, premium prompts, lessons, API rate if added later) |
| **Education** | Curricula: lessons, articles, skill paths; gated by tier where needed |
| **Safety** | Restricted categories (e.g. medical, military), visibility rules, admin moderation |
| **Growth** | SEO catalog and lesson pages, structured data where appropriate |

---

## 2. Primary user flows

1. **Visitor → subscriber:** Land on homepage → CTA (browse / sign up) → catalog → prompt detail → register → choose plan → pay (Stripe/similar) → unlock gated content.
2. **Learner:** Dashboard → education → lesson → related prompts → save.
3. **Contributor:** Dashboard → submit prompt → pending → (email/in-app) notification on approval → discount eligibility.
4. **Moderator/admin:** Review queue → approve/reject with reason → audit trail.

---

## 3. Homepage conversion goal

- **Primary:** Start using the library (browse/search) with one click.
- **Secondary:** Start learning (education entry) or sign up for full access.
- **Tertiary:** Transparent value props (quality, structure, techniques, tiers) without clutter.

---

## 4. System architecture

### 4.1 High-level

```
[Next.js] ──HTTPS──▶ [API Gateway / FastAPI]
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   [Auth/JWT]      [Application services]   [Postgres]
         │                 │                 │
         └──────── Redis (sessions, cache, rate limits optional)
```

### 4.2 Bounded contexts (modules)

| Module | Responsibility |
|--------|----------------|
| **identity** | Users, credentials, sessions/JWT, roles (user, moderator, admin) |
| **billing** | Plans, subscriptions, webhooks, entitlements |
| **catalog** | Categories (tree), prompts, techniques, tags, search index sync |
| **contributions** | Submissions, moderation workflow |
| **education** | Courses/lessons, progress (optional v1) |
| **compliance** | Restricted categories, policy flags |

**Boundaries:** Handlers depend on service interfaces only; services orchestrate; repositories encapsulate SQL/ORM; domain models live in `model` or `domain` packages.

---

## 5. Entities & relationships (high-level)

### 5.1 Core entities

- **User** — id, email, hashed password, display_name, role, created_at.
- **Subscription** — user_id, plan_tier, status, current_period_end, provider refs.
- **Category** — id, parent_id (nullable), slug, name, sort_order, **is_restricted** (bool).
- **Prompt** — id, slug, title, body, summary, status (draft/published/archived), **technique** enum, category_id, author_id (nullable for curated), **moderation_state** for UGC, created_at.
- **Tag** — many-to-many with Prompt.
- **SavedPrompt** — user_id + prompt_id (unique).
- **Submission** (optional separate table or prompt with type=submission) — links to Prompt + reviewer + decided_at.
- **Lesson** — id, slug, title, body_md, tier_required, order.
- **ModerationEvent** — prompt_id, actor_id, action, reason, created_at.

### 5.2 ER sketch

```
User 1──* Subscription
User 1──* SavedPrompt *──1 Prompt
Category 1──* Prompt
Prompt *──* Tag
Prompt *──1 User (author, optional)
Category (self FK parent_id) — tree
Lesson — tier gating only (no hard FK to Prompt required; optional related_prompt_ids)
```

### 5.3 Search

- **PostgreSQL:** `tsvector` on prompt title/body + GIN index; filter by category, technique, tags, exclude restricted unless admin.
- **Optional later:** Meilisearch for typo-tolerance and facets.

---

## 6. API structure (grouped by domain)

Base: `/api/v1`

| Domain | Endpoints (representative) |
|--------|----------------------------|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| **Users** | `GET/PATCH /users/me`, `GET /users/me/saved-prompts` |
| **Catalog** | `GET /categories` (tree), `GET /prompts`, `GET /prompts/{slug}`, `GET /techniques` |
| **Search** | `GET /search?q=&category=&technique=&tag=` |
| **Billing** | `GET /plans`, `POST /checkout/session`, `POST /webhooks/stripe` |
| **Contributions** | `POST /prompts/submit`, `GET /users/me/submissions` |
| **Moderation** | `GET /moderation/queue`, `POST /moderation/{prompt_id}/decision` |
| **Education** | `GET /lessons`, `GET /lessons/{slug}` |
| **Health** | `GET /health`, `GET /ready` |

**Cross-cutting:** JWT bearer; problem+json errors; pagination (`cursor` or `page/limit`); `Idempotency-Key` on POST where payments apply.

---

## 7. Folder structure

### 7.1 Backend (Python, Clean Architecture)

```
backend/
  app/
    main.py                 # FastAPI app factory, lifespan, routers
    config.py               # pydantic-settings from env
    dependencies.py       # DB session, current user, tier checks
    api/
      v1/
        routers/
          auth.py
          users.py
          catalog.py
          search.py
          billing.py
          contributions.py
          moderation.py
          education.py
        deps.py
    core/
      security.py         # JWT, password hashing
      errors.py
    modules/
      identity/
        handler/            # route handlers thin → call service
        service/
        repository/
        model/
      catalog/
        handler/
        service/
        repository/
        model/
      billing/
        ...
      contributions/
        ...
      education/
        ...
    infrastructure/
      db/
        session.py
        base.py
      cache/               # optional Redis
  alembic/                 # migrations
  tests/
  pyproject.toml / requirements.txt
  Dockerfile
```

*Note:* If you prefer a flatter layout, `handler/service/repository` can live under each module only (as above).

### 7.2 Frontend (Next.js App Router)

```
frontend/
  app/
    (marketing)/
      page.tsx              # homepage
      layout.tsx
    catalog/
      page.tsx
      [slug]/page.tsx       # prompt detail
    learn/
      [slug]/page.tsx
    auth/
      login/page.tsx
      signup/page.tsx
    dashboard/
      page.tsx
      saved/page.tsx
      submit/page.tsx
    layout.tsx
    api/                    # optional route handlers for BFF
  components/
    layout/ Header.tsx Footer.tsx Nav.tsx
    ui/                     # cards, buttons (minimal design system)
  lib/
    api-client.ts
    auth.ts
  public/
  next.config.js
  package.json
```

---

## 8. Technical decisions (brief)

| Decision | Choice | Why |
|----------|--------|-----|
| API framework | FastAPI | Python per spec, async, OpenAPI, ecosystem |
| DB access | SQLAlchemy 2 + Alembic | Mature, fits repository pattern |
| Auth | JWT access + optional refresh | Stateless API, fits Next.js |
| Payments | Stripe (placeholder in foundation) | Standard for subscriptions |
| Search v1 | Postgres FTS | Fewer moving parts; upgrade path to Meilisearch |

---

## 9. Next steps (Phase 2)

1. Scaffold `backend/` with FastAPI, config, Postgres, Alembic, one vertical slice (e.g. health + categories list).
2. Scaffold `frontend/` with Next.js, layout, homepage + catalog shell, env-based API URL.
3. Implement first full CRUD on **Prompt** or **Category** through handler → service → repository.

---

*End of Phase 1.*
