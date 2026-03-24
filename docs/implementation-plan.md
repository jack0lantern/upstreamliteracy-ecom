# Upstream Literacy E-Commerce — Implementation Plan

**Generated:** 2026-03-23
**PRD Version:** 2.1
**Status:** Ready for Engineering

---

## Table of Contents

1. [Resolved Architectural Decisions](#1-resolved-architectural-decisions)
2. [System Architecture](#2-system-architecture)
3. [Multi-Agent Execution Model](#3-multi-agent-execution-model)
4. [Repository Structure](#4-repository-structure)
5. [Data Models](#5-data-models)
6. [API Specification](#6-api-specification)
7. [Implementation Task Graph](#7-implementation-task-graph)
8. [Local Dev Setup & Run Commands](#8-local-dev-setup--run-commands)
9. [Observability Plan](#9-observability-plan)
10. [Testing Strategy](#10-testing-strategy)
11. [PRD Traceability Matrix](#11-prd-traceability-matrix)

---

## 1. Resolved Architectural Decisions

| # | Decision | Resolution | Rationale |
|---|----------|-----------|-----------|
| 1 | Backend Framework | **Django 5 + DRF** | PRD §9.2; batteries-included admin, auth, ORM |
| 2 | Frontend Framework | **React 18 + TypeScript + Tailwind** | PRD §9.2; component reuse, strong ecosystem |
| 3 | Database | **PostgreSQL 16** | PRD §9.2; full-text search, JSONB metadata |
| 4 | API Style | **REST /api/v1/** | PRD §9.4; cursor pagination, JWT auth, CORS |
| 5 | Auth Strategy | **JWT (API) + Session (admin)** | simplejwt; refresh in httpOnly cookie, access in memory |
| 6 | Infrastructure | **Docker Compose (local) → Railway (prod)** | Managed Postgres + Redis; simpler deploys |
| 7 | Queue System | **Celery + Redis — Phase 3** | Phase 1-2: sync emails, mgmt commands + cron |
| 8 | File Storage | **Railway volume** | Media files served via WhiteNoise; backup via Railway CLI |
| 9 | Email Provider | **SendGrid (HTTP API)** | Console backend in dev; SendGrid in prod |
| 10 | Analytics | **PostHog (cloud)** | Free tier covers MVP; JS SDK + Python SDK |
| 11 | Error Monitoring | **Sentry** | Backend + frontend; replays on frontend |

---

## 2. System Architecture

### 2.1 High-Level Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Frontend (SPA)                              │
│          React 18 + TypeScript + Tailwind CSS                 │
│   TanStack Query (server state) + Zustand (client state)      │
│   PostHog JS + Sentry React                                   │
│   Routes: /shop, /shop/category/:slug, /shop/product/:slug,  │
│           /shop/cart, /shop/checkout, /shop/account            │
└──────────────────────┬───────────────────────────────────────┘
                       │ REST /api/v1/ (JSON, JWT auth, CORS)
                       │
┌──────────────────────┴───────────────────────────────────────┐
│                    Backend (Django 5 + DRF)                    │
│                                                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ catalog  │ │   cart    │ │ checkout │ │     orders       ││
│  │(products,│ │(items,   │ │(sessions,│ │(order lifecycle, ││
│  │ categories│ │ persist) │ │ tax, ship)│ │ status, email)  ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │inventory │ │ accounts │ │ payments │ │    analytics     ││
│  │(stock,   │ │(users,   │ │(stripe,  │ │(events, dashbd, ││
│  │ alerts)  │ │ auth,JWT)│ │ webhooks)│ │ abandonment)     ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘│
│  ┌──────────┐                                                │
│  │  core    │ ← shared: pagination, permissions, exceptions  │
│  └──────────┘                                                │
└──────────┬────────────┬─────────────┬────────────────────────┘
           │            │             │
    ┌──────┴──────┐ ┌───┴────┐ ┌─────┴──────────┐
    │ PostgreSQL  │ │ Redis  │ │ Railway Volume │
    │ 16 (primary)│ │(cache, │ │ (media files)  │
    │             │ │session)│ │                │
    └─────────────┘ └────────┘ └────────────────┘
```

### 2.2 Request Flow

1. React SPA → REST API call with JWT Bearer token
2. Django middleware: CORS → SecurityMiddleware → SessionMiddleware → AuthMiddleware → AuditLogMiddleware
3. DRF view: permission check → serializer validation → service layer → DB
4. Response: JSON with appropriate HTTP status + cache headers

### 2.3 Payment Flow (Stripe)

```
Frontend                    Backend                         Stripe
   │                           │                              │
   │ POST /api/v1/checkout/    │                              │
   │   sessions/{token}/submit │                              │
   │ ─────────────────────►    │                              │
   │                           │ PaymentIntent.create()       │
   │                           │ ─────────────────────────►   │
   │                           │ ◄─────────────────────────   │
   │ ◄──── client_secret ──── │                              │
   │                           │                              │
   │ stripe.confirmCardPayment(client_secret)                 │
   │ ────────────────────────────────────────────────────►    │
   │ ◄───────────────────── paymentIntent.succeeded ─────    │
   │                           │                              │
   │                           │ ◄── webhook: payment_intent  │
   │                           │     .succeeded               │
   │                           │                              │
   │                           │ verify signature ✓           │
   │                           │ create Order                 │
   │                           │ decrement stock              │
   │                           │ send confirmation email      │
```

### 2.4 Cross-App Ownership (Critic Fix)

| Concern | Owner App | Notes |
|---------|-----------|-------|
| PaymentIntent creation | `payments` | Single endpoint; checkout calls `payments.services.create_intent()` |
| Order creation on payment success | `orders` | Webhook handler in `payments` calls `orders.services.create_order()` |
| Stock decrement | `inventory` | Called from `orders.services.create_order()` inside same atomic block |
| Cart merge on login | `cart` | Endpoint: `POST /api/v1/cart/merge/`; frontend calls after login |
| Audit logging | `core` | Single `AuditLogMiddleware` in `core/middleware.py`; no duplicate |
| Email dispatch | `core` | `core/email.py` wraps `django.core.mail.send_mail`; all apps call it |

---

## 3. Multi-Agent Execution Model

This plan is designed for execution by a multi-agent system with an orchestrator, parallel implementation agents, paired QA agents, and critic agents. Below is the architecture for how agents coordinate to build the system.

### 3.1 Agent Architecture Diagram

```
                    ┌─────────────────────┐
                    │    ORCHESTRATOR      │
                    │  (LangGraph graph)   │
                    │                      │
                    │  • Parses PRD        │
                    │  • Routes decisions  │
                    │  • Manages state     │
                    │  • Controls loops    │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
     ┌─ PHASE 1 ──┐  ┌─ PHASE 2 ──┐   ┌─ PHASE 3 ──┐
     │ PRD Ingest  │  │ Decision   │   │ Parallel   │
     │ Decompose   │  │ Checkpoint │   │ Execution  │
     │             │  │ (INTERRUPT)│   │            │
     └─────────────┘  └────────────┘   └─────┬──────┘
                                              │
        ┌──────────┬──────────┬───────────────┼───────────────┬──────────┬──────────┐
        ▼          ▼          ▼               ▼               ▼          ▼          ▼
   ┌─────────┐┌─────────┐┌─────────┐  ┌───────────┐  ┌──────────┐┌─────────┐┌──────────┐
   │FRONTEND ││BACKEND  ││PAYMENTS │  │ CHECKOUT  │  │INVENTORY ││  AUTH   ││ANALYTICS │
   │ Agent   ││ Agent   ││ Agent   │  │  Agent    │  │  Agent   ││ Agent  ││  Agent   │
   └────┬────┘└────┬────┘└────┬────┘  └─────┬─────┘  └────┬─────┘└───┬────┘└────┬─────┘
        │          │          │              │              │          │          │
        ▼          ▼          ▼              ▼              ▼          ▼          ▼
   ┌─────────┐┌─────────┐┌─────────┐  ┌───────────┐  ┌──────────┐┌─────────┐┌──────────┐
   │FRONTEND ││BACKEND  ││PAYMENTS │  │ CHECKOUT  │  │INVENTORY ││  AUTH   ││ANALYTICS │
   │ QA Agent││ QA Agent││ QA Agent│  │ QA Agent  │  │ QA Agent ││QA Agent││ QA Agent │
   └────┬────┘└────┬────┘└────┬────┘  └─────┬─────┘  └────┬─────┘└───┬────┘└────┬─────┘
        │          │          │              │              │          │          │
        └──────────┴──────────┴──────────────┼──────────────┴──────────┴──────────┘
                                             ▼
                              ┌───────────────────────────────┐
                              │       CRITIC AGENTS           │
                              │  (parallel, up to 3 loops)    │
                              │                               │
                              │  ┌──────────┐ ┌────────────┐ │
                              │  │ Auditor  │ │  Security  │ │
                              │  └──────────┘ └────────────┘ │
                              │  ┌──────────┐ ┌────────────┐ │
                              │  │  Impl.   │ │Observabil. │ │
                              │  └──────────┘ └────────────┘ │
                              └───────────────┬───────────────┘
                                              │
                                              ▼
                                   ┌─────────────────┐
                                   │ FINALIZE OUTPUT  │
                                   │ (this document)  │
                                   └─────────────────┘
```

### 3.2 Orchestrator

The orchestrator is a LangGraph `StateGraph` that manages the full pipeline. It:

1. **Parses the PRD** into structured sections with requirement IDs
2. **Decomposes** into modules, bounded contexts, and dependency graph
3. **Interrupts** at decision checkpoints for human input (architectural choices)
4. **Fans out** implementation agents in parallel via `asyncio.gather()`
5. **Fans out** QA agents in parallel (one per implementation agent)
6. **Fans out** critic agents in parallel
7. **Routes** based on critic feedback: loop back (max 3x) or finalize

**State object** threads through all nodes and uses reducer annotations so parallel agents can safely write to shared lists without overwriting:

```python
class PlannerState(MessagesState):
    prd_raw: str
    prd_sections: list[dict]         # reducer: append
    modules: list[dict]              # reducer: append
    dependency_graph: dict           # reducer: merge
    decisions: list[dict]            # reducer: append
    tasks_by_agent: dict             # reducer: merge
    agent_outputs: list[dict]        # reducer: append (parallel-safe)
    qa_results: list[dict]           # reducer: append (parallel-safe)
    critic_feedback: list[dict]      # reducer: append (parallel-safe)
    iteration_count: int             # reducer: replace
    max_iterations: int = 3
    final_outputs: dict              # reducer: merge
```

### 3.3 Implementation Agents (7, Parallel)

Each agent runs concurrently and produces a domain-specific implementation plan. Agents receive the resolved architectural decisions and their assigned PRD requirements.

| Agent | Domain | PRD Scope | Outputs |
|-------|--------|-----------|---------|
| `frontend_agent` | React SPA | FR-CAT-*, FR-CART-*, FR-CHK-*, FR-ACCT-*, §7.3, §9.5 | Component tree, routes, TypeScript types, API client |
| `backend_agent` | Django core + infra | §9.1-9.5, §7.1-7.5 (excl. accounts app) | Project structure, settings, middleware, admin, orders |
| `payments_agent` | Stripe integration | FR-PAY-01-03, §7.2 | PaymentIntent flow, webhook handling, refunds |
| `checkout_agent` | Purchase flow (owns `cart` + `checkout` Django apps) | FR-CHK-01-05, FR-CART-01-03, §5.1-5.5 | State machine, session management, tax/shipping, cart models |
| `inventory_agent` | Stock + catalog | FR-INV-01-03, FR-CAT-01-02 | Models, atomic decrement, alerts, seed data |
| `auth_agent` | Identity | FR-ACCT-01-03, §7.2 | User model, JWT, encryption, audit |
| `analytics_agent` | Tracking | PRD §8.1-8.4 | Event pipeline, dashboards, abandonment |

### 3.4 QA Agents (7, Parallel, 1:1 Paired)

Each QA agent is paired with exactly one implementation agent and runs immediately after all implementation agents complete. QA agents validate **completeness** and **correctness** against the PRD.

| QA Agent | Paired With | Validation Scope |
|----------|------------|-----------------|
| `qa_frontend` | `frontend_agent` | Every FR-* has a component mapping; accessibility (§7.3) covered; URL structure (§9.5) matches |
| `qa_backend` | `backend_agent` | All endpoints defined; middleware ordering correct; settings complete for each environment |
| `qa_payments` | `payments_agent` | PCI compliance (no card data on server); webhook idempotency; refund edge cases |
| `qa_checkout` | `checkout_agent` | All 5 FR-CHK-* covered; atomicity at submit; session expiry handling |
| `qa_inventory` | `inventory_agent` | Concurrent oversell prevented; digital vs physical differentiation; bundle stock calculation |
| `qa_auth` | `auth_agent` | Password policy (min 8, 1 number, 1 special); email enumeration prevention; PII encryption audit |
| `qa_analytics` | `analytics_agent` | All 12 PRD events mapped; funnel definitions match PRD §8.2; ad-blocker fallback present |

**Each QA agent produces:**
- **Test plan**: Unit, integration, and E2E test scenarios for the paired agent's output
- **Edge case coverage**: Which PRD edge cases (§5.5) are handled vs. missing
- **Gaps**: Specific PRD requirements not addressed by the implementation agent
- **Test cases**: Structured test case list (`{id, type, title, expected_result}`)

**QA gate rule**: If any QA agent identifies a gap rated "critical," the orchestrator routes the implementation agent's output back for revision before proceeding to critics.

### 3.5 Critic Agents (4, Parallel, Up to 3 Loops)

Critics review the **combined** output of all implementation agents (not individual agents). They run in parallel and produce feedback targeting specific agents.

| Critic | Focus | Key Checks |
|--------|-------|-----------|
| **Auditor Critic** | PRD alignment | Missing requirements, scope creep, incorrect PRD references, traceability gaps |
| **Security Critic** | Vulnerability review | Auth gaps, PCI compliance, PII exposure, injection risks, CSRF/XSS, Stripe webhook verification |
| **Implementation Critic** | Feasibility | Overengineering for MVP, under-specified steps, incorrect tech usage, unrealistic effort estimates |
| **Observability Critic** | Production readiness | Missing logging, metrics, health checks, alerting rules, audit trails, error monitoring |

**Loop logic:**
```
iteration = 0
while iteration < 3:
    run all 4 critics in parallel
    if ALL critics return has_issues=False:
        break  # convergence — no further changes needed
    else:
        route feedback to relevant implementation agents
        re-run affected implementation agents
        re-run paired QA agents
        iteration += 1
finalize outputs
```

### 3.6 Graph Flow (LangGraph Wiring)

```
ingest_prd
  → decompose_prd
  → decision_checkpoint ──── INTERRUPT (human resolves architectural decisions)
  → plan_parallel_work
  → implementation_agents ─── 7 agents via asyncio.gather()
  → qa_agents ──────────────── 7 QA agents via asyncio.gather()
  → critic_agents ───────────── 4 critics via asyncio.gather()
  → critic_router
      ├── feedback exists AND iteration < 3 → increment_iteration → implementation_agents
      └── no feedback OR iteration == 3 ────→ finalize_outputs → END
```

**Human-in-the-loop** at `decision_checkpoint`:
- Uses LangGraph `interrupt()` to pause the graph
- Presents 7 architectural decisions with 2-3 options each (pros/cons/recommendation)
- Resumes via `Command(resume=user_resolutions)`
- Checkpointer (MemorySaver or PostgreSQL) persists state across the interrupt boundary

### 3.7 Running the Agent Pipeline

**One command to generate the plan from a PRD:**

```bash
# Interactive CLI (prompts for decisions at checkpoint)
python -m planner --prd docs/UpstreamLiteracy-ecom-prd_v1.md --output docs/implementation-plan.json

# Programmatic (pre-resolved decisions, no interrupt)
python planner/example_interrupt_resume.py
```

**One command to run the generated system locally:**

```bash
make dev
```

See [§8. Local Dev Setup & Run Commands](#8-local-dev-setup--run-commands) for full details.

### 3.8 Agent Output Traceability

Every agent output includes a `prd_refs` field listing which PRD requirement IDs it covers. The orchestrator's `finalize_outputs` node cross-references all `prd_refs` against the full set of PRD requirements from `ingest_prd` and flags any uncovered requirements. This ensures the final plan has zero gaps by construction — not by manual review.

---

## 4. Repository Structure

```
upstream-ecom/
├── docker-compose.yml           # postgres, redis, web, frontend
├── Dockerfile                   # Django production image (also backend/Dockerfile for dev)
├── railway.toml                 # Railway deploy config
├── Makefile                     # dev shortcuts
├── .env.example
│
├── backend/
│   ├── manage.py
│   ├── pyproject.toml           # deps, ruff, mypy, pytest config
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py          # shared settings
│   │   │   ├── local.py         # DEBUG=True, console email
│   │   │   ├── production.py    # Railway env, HTTPS, HSTS, SendGrid
│   │   │   └── test.py          # fast hasher, in-memory cache
│   │   ├── urls.py              # /api/v1/, /admin/, /health/
│   │   ├── wsgi.py
│   │   └── gunicorn.conf.py     # workers=2*CPU+1, gevent
│   │
│   ├── apps/
│   │   ├── core/
│   │   │   ├── middleware.py     # AuditLogMiddleware, RequestID
│   │   │   ├── pagination.py    # CursorPagination base
│   │   │   ├── permissions.py   # IsVerifiedUser, IsOwnerOrAdmin
│   │   │   ├── exceptions.py    # DRF exception handler
│   │   │   ├── email.py         # send_transactional_email() wrapper
│   │   │   ├── health.py        # /health/ view (DB + Redis check)
│   │   │   └── logging.py       # JSON structured logging config
│   │   │
│   │   ├── accounts/
│   │   │   ├── models.py        # User, UserProfile, Institution, Address
│   │   │   ├── tokens.py        # EmailVerificationToken, PasswordResetToken
│   │   │   ├── serializers.py
│   │   │   ├── views.py         # register, login, verify, reset, profile
│   │   │   ├── throttles.py     # LoginRateThrottle, ResetRateThrottle
│   │   │   └── admin.py
│   │   │
│   │   ├── catalog/
│   │   │   ├── models.py        # Product, Category, ProductImage, SKU, SkillTag
│   │   │   ├── serializers.py   # ProductListSerializer, ProductDetailSerializer
│   │   │   ├── views.py         # ProductViewSet, CategoryViewSet
│   │   │   ├── filters.py       # django-filter: category, grade, format, in_stock
│   │   │   ├── search.py        # PostgreSQL full-text search view
│   │   │   └── admin.py
│   │   │
│   │   ├── inventory/
│   │   │   ├── models.py        # StockLevel, StockMovement, StockAlert
│   │   │   ├── services.py      # reserve_stock, release_stock, adjust_stock
│   │   │   ├── signals.py       # post-decrement alert creation
│   │   │   ├── views.py         # admin stock adjustment, alerts
│   │   │   └── management/commands/
│   │   │       ├── reconcile_inventory.py
│   │   │       ├── send_stock_alerts.py
│   │   │       └── seed_products.py    # ~20 MVP products
│   │   │
│   │   ├── cart/
│   │   │   ├── models.py        # Cart, CartItem
│   │   │   ├── serializers.py
│   │   │   ├── views.py         # CartViewSet, merge endpoint
│   │   │   └── middleware.py    # GuestCartMiddleware (cookie-based token)
│   │   │
│   │   ├── checkout/
│   │   │   ├── models.py        # CheckoutSession, ShippingRate, TaxCalculation
│   │   │   ├── services.py      # CheckoutService, TaxService, ShippingService
│   │   │   ├── state_machine.py # step validation + transitions
│   │   │   ├── serializers.py
│   │   │   ├── views.py         # session CRUD, step advance, submit
│   │   │   └── tax_rates.json   # 50-state rate fixture
│   │   │
│   │   ├── orders/
│   │   │   ├── models.py        # Order, OrderItem, OrderStatusHistory
│   │   │   ├── services.py      # create_order, update_status, cancel_order
│   │   │   ├── serializers.py
│   │   │   ├── views.py         # order detail, history, guest tracking
│   │   │   ├── emails.py        # confirmation, shipped, delivered templates
│   │   │   └── admin.py         # order management, fulfillment actions
│   │   │
│   │   ├── payments/
│   │   │   ├── models.py        # Payment, Transaction, Refund, WebhookEvent
│   │   │   ├── services.py      # PaymentService (create_intent, process_refund)
│   │   │   ├── stripe_client.py # thin SDK wrapper, idempotency keys
│   │   │   ├── webhooks.py      # signature verify + event dispatch
│   │   │   ├── views.py         # intent endpoint, webhook endpoint, refunds
│   │   │   └── admin.py         # refund actions
│   │   │
│   │   └── analytics/
│   │       ├── models.py        # AnalyticsEvent, CartAbandonmentRecord
│   │       ├── services.py      # track_event, @track_event decorator
│   │       ├── views.py         # frontend event ingestion, dashboard endpoints
│   │       └── management/commands/
│   │           └── detect_abandoned_carts.py
│   │
│   └── templates/
│       └── emails/              # order_confirmation.html, shipped.html, etc.
│
├── frontend/
│   ├── Dockerfile               # Node dev image + nginx for production
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── .env.example             # VITE_API_BASE_URL, VITE_POSTHOG_KEY, VITE_SENTRY_DSN
│   │
│   ├── src/
│   │   ├── main.tsx             # React root, Sentry.init, PostHog.init
│   │   ├── router/
│   │   │   ├── index.tsx        # createBrowserRouter, all routes (lazy)
│   │   │   └── guards.tsx       # RequireAuth, RequireGuest, RequireCart
│   │   │
│   │   ├── lib/
│   │   │   ├── api/
│   │   │   │   ├── client.ts    # Axios instance, interceptors, token refresh
│   │   │   │   ├── auth.ts
│   │   │   │   ├── products.ts
│   │   │   │   ├── categories.ts
│   │   │   │   ├── cart.ts
│   │   │   │   ├── checkout.ts
│   │   │   │   ├── orders.ts
│   │   │   │   └── account.ts
│   │   │   ├── queryKeys.ts     # TanStack Query key factory
│   │   │   └── analytics.ts     # PostHog wrapper + backend fallback
│   │   │
│   │   ├── stores/
│   │   │   ├── authStore.ts     # Zustand: user, tokens, login/logout
│   │   │   ├── uiStore.ts       # Zustand: cart sidebar, toasts
│   │   │   └── checkoutStore.ts # Zustand: step state, sessionStorage persist
│   │   │
│   │   ├── types/
│   │   │   └── index.ts         # All TypeScript interfaces (domain objects)
│   │   │
│   │   ├── components/
│   │   │   ├── layout/          # Header, Footer, Breadcrumbs, CartIconBadge
│   │   │   ├── ui/              # Toast, ErrorBoundary, LoadingSkeleton
│   │   │   ├── catalog/         # CategorySidebar, ProductCard, ProductGrid, SortControls
│   │   │   ├── product/         # ProductImageGallery, RelatedProducts
│   │   │   ├── cart/            # CartLineItem, QuantitySelector, AddToCartBlock
│   │   │   ├── checkout/        # CheckoutProgress, AddressForm, TaxDisplay, steps/*
│   │   │   ├── account/         # AddressBook, OrderTable
│   │   │   ├── search/          # SearchBar
│   │   │   └── auth/            # LoginForm, RegisterForm
│   │   │
│   │   ├── pages/
│   │   │   ├── ShopPage.tsx
│   │   │   ├── CategoryPage.tsx
│   │   │   ├── ProductDetailPage.tsx
│   │   │   ├── CartPage.tsx
│   │   │   ├── CheckoutLayout.tsx
│   │   │   ├── OrderConfirmationPage.tsx
│   │   │   ├── SearchResultsPage.tsx
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── account/
│   │   │       ├── AccountLayout.tsx
│   │   │       ├── ProfilePage.tsx
│   │   │       └── OrderHistoryPage.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useFocusOnRouteChange.ts
│   │   │   └── useFocusTrap.ts
│   │   │
│   │   └── styles/
│   │       └── globals.css      # Tailwind directives + custom tokens
│   │
│   └── nginx.conf               # Production: serve SPA, proxy /api/ to Django
│
└── scripts/
    ├── setup.sh                 # One-command dev setup
    └── seed.sh                  # Load seed data
```

---

## 5. Data Models

### 5.1 accounts App

**User** (custom, `AUTH_USER_MODEL`)
```
id              UUID PK
email           EncryptedEmailField(unique, HMAC-indexed)
first_name      EncryptedCharField(150)
last_name       EncryptedCharField(150)
role            CharField [teacher|admin|parent|other]
is_active       BooleanField(True)
is_staff        BooleanField(False)
is_verified     BooleanField(False)
is_guest        BooleanField(False)
date_joined     DateTimeField(auto_now_add)
last_login      DateTimeField(null)
```

**Settings:** `PASSWORD_HASHERS = ['django.contrib.auth.hashers.BCryptSHA256PasswordHasher']` (cost 12 default)

**UserProfile** → OneToOne(User)
```
phone           EncryptedCharField(30, blank)
preferences     JSONField(default=dict)
pending_email   EncryptedEmailField(null, blank)  # email change flow
```

**Institution** → OneToOne(User) *(MVP: only fields; tax-exempt verification in Phase 2)*
```
school_name     CharField(255, blank)
district_name   CharField(255, blank)
tax_exempt      BooleanField(False)
exemption_cert  FileField(null, blank)
exemption_verified BooleanField(False)  # admin-set only
```

**Address** → FK(User)
```
id              UUID PK
label           CharField(100)         # "Home", "School"
recipient_name  CharField(255)
line_1          EncryptedCharField(255)
line_2          CharField(255, blank)
city            CharField(100)
state           CharField(2)           # US state code
zip             CharField(10)
country         CharField(2, default='US')
is_default      BooleanField(False)
```

**AuditLog** *(append-only, no delete)*
```
id              BigAutoField PK
actor           FK(User, null, SET_NULL)
actor_email     CharField(255)         # denormalized
action          CharField(100)
target_type     CharField(100)
target_id       CharField(100)
ip_address      GenericIPAddressField
metadata        JSONField
created_at      DateTimeField(auto_now_add, db_index)
```

**EmailVerificationToken** → OneToOne(User)
```
id              UUID PK
expires_at      DateTimeField           # now + 24h
```

**PasswordResetToken** → FK(User)
```
id              UUID PK
token_hash      CharField(64)           # SHA-256 of raw token
expires_at      DateTimeField           # now + 1h
used            BooleanField(False)
```

### 5.2 catalog App

**Category**
```
id              PK
name            CharField(120)
slug            SlugField(unique)
parent          FK(self, null)
description     TextField(blank)
display_order   PositiveIntegerField(0)
is_active       BooleanField(True)
```

**Product**
```
id              PK
title           CharField(255)
slug            SlugField(unique)
product_type    CharField [physical|digital|bundle]
description     TextField
short_description TextField(blank)
base_price      DecimalField(10,2)
categories      M2M(Category, through=ProductCategory)
skill_tags      M2M(SkillTag)
format_specs    JSONField(default=dict)
is_active       BooleanField(True)
seo_title       CharField(160, blank)
seo_description CharField(320, blank)
```

**ProductImage** → FK(Product)
```
image           ImageField(upload_to='products/')
alt_text        CharField(255, blank)
is_primary      BooleanField(False)
display_order   PositiveIntegerField(0)
```

**SKU** → FK(Product)
```
sku_code        CharField(64, unique)
variant_label   CharField(100, blank)
price_override  DecimalField(10,2, null)
is_active       BooleanField(True)
```

**BundleComponent** → FK(Product) + FK(SKU)
```
bundle_product  FK(Product, limit=BUNDLE type)
component_sku   FK(SKU)
quantity        PositiveIntegerField(1)
```

### 5.3 inventory App

**StockLevel** → OneToOne(SKU)
```
quantity_on_hand    IntegerField(0)     # can go negative (backorder)
low_stock_threshold IntegerField(5)
is_unlimited        BooleanField(False) # True for digital
backorder_enabled   BooleanField(False)
estimated_restock   DateField(null)
```

**StockMovement** → FK(SKU) *(append-only)*
```
movement_type   CharField [SALE|RETURN|ADJUSTMENT|RESTOCK|INITIAL|RECONCILE]
delta           IntegerField            # negative=decrement
quantity_after  IntegerField
order           FK(Order, null)
performed_by    FK(User, null)
reason          TextField(blank)
created_at      DateTimeField(auto_now_add)
```

**StockAlert** → FK(SKU)
```
alert_type      CharField [LOW_STOCK|OUT_OF_STOCK|BACKORDER_OVERDUE]
quantity_at_trigger IntegerField
is_active       BooleanField(True)
acknowledged_by FK(User, null)
acknowledged_at DateTimeField(null)
```

### 5.4 cart App

**Cart**
```
id              UUID PK
token           CharField(64, unique)   # guest identification
user            FK(User, null)
expires_at      DateTimeField(null)     # null=never (authenticated)
created_at      DateTimeField(auto_now_add)
updated_at      DateTimeField(auto_now)
```

**CartItem** → FK(Cart) + FK(SKU)
```
quantity        PositiveIntegerField(1)
unit_price      DecimalField(10,2)      # snapshotted at add-time
```

### 5.5 checkout App

**CheckoutSession**
```
id              UUID PK
session_token   CharField(64, unique)
user            FK(User, null)
guest_email     EmailField(null)
current_step    CharField(32, default='CONTACT')
cart_snapshot   JSONField               # frozen cart at session creation
shipping_address JSONField(null)
billing_address  JSONField(null)
billing_same_as_shipping BooleanField(True)
shipping_rate   FK(ShippingRate, null)
shipping_cost   DecimalField(10,2, null)
tax_calculation FK(TaxCalculation, null)
tax_exempt      BooleanField(False)
stripe_payment_intent_id CharField(64, null)
subtotal        DecimalField(10,2)
total           DecimalField(10,2, null)
status          CharField [active|submitted|confirmed|expired]
expires_at      DateTimeField           # now + 2h; extended on step advance
order           OneToOne(Order, null)
```

**ShippingRate**
```
name            CharField(100)          # "Standard Shipping"
flat_rate       DecimalField(8,2)       # MVP seed: $5.99
estimated_days_min PositiveSmallIntegerField(3)
estimated_days_max PositiveSmallIntegerField(7)
is_active       BooleanField(True)
```

**TaxCalculation** → FK(CheckoutSession)
```
destination_state CharField(2)
taxable_amount  DecimalField(10,2)
tax_rate        DecimalField(6,4)
tax_amount      DecimalField(10,2)
is_exempt       BooleanField(False)
provider        CharField(20, default='state_table')
```

### 5.6 orders App

**Order**
```
id              UUID PK
order_number    CharField(20, unique)   # "UL-2026-00001"
user            FK(User, null)          # null for guest
guest_email     EmailField(null)
guest_tracking_token CharField(64, null) # HMAC-signed
status          CharField [pending_payment|processing|shipped|delivered|cancelled]
shipping_address JSONField
billing_address  JSONField
shipping_method CharField(100)
subtotal        DecimalField(10,2)
shipping_cost   DecimalField(10,2)
tax_amount      DecimalField(10,2)
is_tax_exempt   BooleanField(False)
total           DecimalField(10,2)
tracking_number CharField(100, null)
tracking_url    CharField(500, null)
notes           TextField(blank)
created_at      DateTimeField(auto_now_add)
updated_at      DateTimeField(auto_now)
```

**OrderItem** → FK(Order)
```
product_title   CharField(255)          # denormalized
product_slug    CharField(255)
sku_code        CharField(64)
product_image_url CharField(500, blank)
quantity        PositiveIntegerField
unit_price      DecimalField(10,2)
line_total      DecimalField(10,2)
product_type    CharField [physical|digital|bundle]
```

**OrderStatusHistory** → FK(Order)
```
from_status     CharField(30)
to_status       CharField(30)
changed_by      FK(User, null)
note            TextField(blank)
created_at      DateTimeField(auto_now_add)
```

### 5.7 payments App

**Payment** → OneToOne(Order)
```
id              UUID PK
stripe_payment_intent_id CharField(255, unique, null)
stripe_charge_id         CharField(255, null)
idempotency_key UUID(unique)
amount_cents    PositiveIntegerField
currency        CharField(3, default='usd')
method          CharField(20) [card|manual]
status          CharField(30) [pending|processing|succeeded|failed|cancelled|refunded|partially_refunded]
failure_code    CharField(100, null)
failure_message TextField(null)
```

**Transaction** → FK(Payment) *(append-only ledger)*
```
id              UUID PK
type            CharField(20) [charge|refund|dispute]
amount_cents    IntegerField            # negative for refunds
source          CharField(20) [stripe|manual]
stripe_object_id CharField(255, null)
idempotency_key  CharField(255, unique)
notes           TextField(blank)
created_by      FK(User, null)
created_at      DateTimeField(auto_now_add)
```

**Refund** → FK(Payment)
```
id              UUID PK
initiated_by    FK(User)
amount_cents    PositiveIntegerField
reason          CharField(50) [customer_request|duplicate|fraudulent|order_cancelled]
stripe_refund_id CharField(255, unique, null)
status          CharField(20) [pending|succeeded|failed]
staff_notes     TextField(blank)
```

**WebhookEvent** *(idempotency log)*
```
stripe_event_id CharField(255, unique)
event_type      CharField(100)
payload         JSONField
processed       BooleanField(False)
processing_error TextField(blank)
related_payment FK(Payment, null)
created_at      DateTimeField(auto_now_add)
```

### 5.8 analytics App

**AnalyticsEvent** *(backend fallback store)*
```
event_name      CharField(100, db_index)
session_id      CharField(64, db_index)
user            FK(User, null, SET_NULL)
anonymous_id    CharField(64, blank)
occurred_at     DateTimeField(db_index)
received_at     DateTimeField(auto_now_add)
properties      JSONField
idempotency_key CharField(128, unique)
source          CharField(20) [frontend|backend]
```

**CartAbandonmentRecord** → OneToOne(Cart)
```
is_guest        BooleanField
cart_value      DecimalField(10,2)
item_count      IntegerField
checkout_started BooleanField(False)
last_event_at   DateTimeField
week_of         DateField(db_index)
```

---

## 6. API Specification

### 6.1 Authentication (`/api/v1/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register/` | Public | Create account (email+password) → sends verification email |
| POST | `/login/` | Public, rate-limited (5/min/IP) | Returns JWT pair; sets refresh in httpOnly cookie |
| POST | `/token/refresh/` | Public | Reads refresh from cookie or body; rotates + blacklists old |
| POST | `/logout/` | JWT | Blacklists refresh token, clears cookie |
| POST | `/verify-email/` | Public | `{token}` → marks verified, issues first JWT pair |
| POST | `/verify-email/resend/` | Public, rate-limited (3/hr) | Always returns 200 (no enumeration) |
| POST | `/password/reset/` | Public, rate-limited (3/hr) | Always returns 200 (no enumeration) |
| POST | `/password/reset/confirm/` | Public | `{token, new_password}` → invalidates all refresh tokens |
| POST | `/password/change/` | JWT | `{current_password, new_password}` |

### 6.2 Account (`/api/v1/accounts/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/PATCH | `/profile/` | JWT | User profile + institution fields |
| GET | `/addresses/` | JWT | List saved addresses |
| POST | `/addresses/` | JWT | Create address (label required) |
| GET/PATCH/DELETE | `/addresses/{id}/` | JWT (owner) | Manage address |
| POST | `/addresses/{id}/set-default/` | JWT (owner) | Set as default (atomic) |
| POST | `/claim-guest/` | Public | `{guest_session_token, email, password}` → migrate guest orders |

### 6.3 Catalog (`/api/v1/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/categories/` | Public | Category tree (hide_empty=true) |
| GET | `/categories/{slug}/` | Public | Category detail + children |
| GET | `/products/` | Public | `?category=&grade=&format=&skill=&in_stock=&sort=&cursor=` |
| GET | `/products/{slug}/` | Public | Full detail with images, SKUs, stock status |
| GET | `/products/{slug}/related/` | Public | Up to 8 related products |
| GET | `/search/` | Public | `?q=&cursor=` Full-text search |

**Product list response includes:** `slug, title, price, primary_image_url, skill_tags, product_type, format_specs, is_in_stock` (Phase 2 adds `average_rating, review_count` once Reviews model exists)

**Product image URL format:** Absolute URL constructed by serializer: `{MEDIA_URL}{image.name}` — frontend uses directly as `<img src=...>`.

### 6.4 Cart (`/api/v1/cart/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT or `X-Cart-Token` | Current cart |
| POST | `/items/` | JWT or `X-Cart-Token` | `{sku_id, quantity}` → returns updated cart (SKU identifies product variant) |
| PATCH | `/items/{id}/` | JWT or `X-Cart-Token` | `{quantity}` |
| DELETE | `/items/{id}/` | JWT or `X-Cart-Token` | Remove item |
| POST | `/merge/` | JWT | `{guest_cart_token}` → merge guest cart into user cart |

### 6.5 Checkout (`/api/v1/checkout/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/sessions/` | JWT or `X-Cart-Token` | Create session from cart (snapshots items+prices) |
| GET | `/sessions/{token}/` | Session token | Full session state |
| PATCH | `/sessions/{token}/contact/` | Session token | `{email}` (guest) or auto-fill (registered) |
| PATCH | `/sessions/{token}/address/` | Session token | `{shipping_address, billing_same_as_shipping, billing_address?}` |
| PATCH | `/sessions/{token}/shipping/` | Session token | `{shipping_rate_id}` → returns updated total |
| PATCH | `/sessions/{token}/payment/` | Session token | `{stripe_payment_method_id}` → returns `client_secret` |
| POST | `/sessions/{token}/submit/` | Session token | Atomic: validate → decrement stock → confirm payment → create order → email |
| GET | `/shipping-rates/` | Public | `?zip=` → available rates (MVP: single flat-rate $5.99) |
| GET | `/tax-estimate/` | Session token | `?state=&zip=` → `{tax_rate, tax_amount, is_exempt}` |

**Checkout step validation:** Each PATCH validates its step and returns `422` with field errors if invalid. Step transitions enforced: cannot PATCH `/payment/` before `/address/` is complete.

### 6.6 Orders (`/api/v1/orders/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | JWT | `?status=&sort=&cursor=` paginated order history |
| GET | `/{order_number}/` | JWT (owner) or `X-Order-Token` (guest) | Full order detail |
| GET | `/track/{order_number}/` | Public + `?token=` (HMAC signed) | Guest tracking |

### 6.7 Payments (`/api/v1/payments/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/intent/` | Session token | Create Stripe PaymentIntent → `{client_secret, payment_id}` |
| POST | `/intent/{id}/cancel/` | Owner | Cancel unpaid intent |
| POST | `/{id}/refunds/` | Admin | `{amount_cents, reason}` partial/full refund |
| POST | `/webhooks/stripe/` | Stripe-Signature | Webhook handler (no JWT) |

**Webhook signature verification:** `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)` — explicitly confirmed.

### 6.8 Analytics (`/api/v1/analytics/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/events/` | Public | `{events: [...]}` bulk frontend event ingestion (fallback) |
| POST | `/identify/` | JWT | `{anonymous_id}` → stitch anonymous events to user |

### 6.9 Dashboard (`/api/v1/dashboard/`) — Admin only

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/operational/` | Orders today/week/month, pending fulfillment, low stock, payment failures |
| GET | `/funnel/` | `?start=&end=` conversion funnel from AnalyticsEvent table |
| GET | `/revenue/` | `?granularity=day|week|month&start=&end=` revenue + AOV series |
| GET | `/abandonment/` | `?start=&end=` cart abandonment breakdown |
| GET | `/top-products/` | `?limit=10&start=&end=` by revenue and units |

### 6.10 Health (`/health/`)

```json
GET /health/

200: { "status": "ok", "database": "ok", "redis": "ok" }
503: { "status": "degraded", "database": "ok", "redis": "error" }
```

---

## 7. Implementation Task Graph

### Execution Model

Each workstream maps to an **implementation agent + paired QA agent**. The orchestrator launches workstreams in parallel where dependencies allow. After each workstream completes, its QA agent validates before the output feeds into dependent workstreams.

```
Orchestrator
  │
  ├── [PARALLEL] Week 1-2: Foundation
  │     ├── Workstream A (backend_agent + auth_agent) → QA-A (qa_backend + qa_auth)
  │     ├── Workstream B (inventory_agent)            → QA-B (qa_inventory)
  │     └── Workstream C (frontend_agent)             → QA-C (qa_frontend)
  │
  ├── [PARALLEL] Week 2-4: Core Features (depends on A,B,C)
  │     ├── Workstream D (checkout_agent)  → QA-D (qa_checkout)
  │     ├── Workstream E (payments_agent)  → QA-E (qa_payments)
  │     └── Workstream F (frontend_agent)  → QA-F (qa_frontend)
  │
  ├── [PARALLEL] Week 5-6: Integration
  │     ├── Workstream G-analytics (analytics_agent) → QA-G (qa_analytics)
  │     └── Workstream G-admin (backend_agent)      → QA-G2 (qa_backend)
  │
  ├── [CRITIC LOOP] Week 6: Cross-cutting review (max 3 iterations)
  │     ├── Auditor Critic    ─┐
  │     ├── Security Critic   ─┤── parallel → feedback → revise → re-validate
  │     ├── Implementation Critic ─┤
  │     └── Observability Critic ──┘
  │
  └── [SEQUENTIAL] Week 7-8: Polish + Hardening (Workstream H)
        └── All agents (security: auth_agent, perf: frontend_agent, infra: backend_agent)
            → QA-H1 (qa_auth) + QA-H2 (qa_frontend) + QA-H3 (all QA agents for E2E)
```

### Phase 1: MVP (8-10 weeks)

Organized into parallel workstreams. Tasks within a workstream are sequential; workstreams run concurrently. Each workstream has a **QA gate** that must pass before dependent workstreams start.

#### Week 1-2: Foundation (all workstreams start)

**Workstream A — Backend Core**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| A1 | Django project scaffold: settings (base/local/prod/test), urls, gunicorn | M | — |
| A2 | `core` app: pagination, permissions, exceptions, JSON logging, email wrapper | M | A1 |
| A3 | `accounts` app: User model, UserProfile, Address, migrations | L | A1 |
| A4 | JWT config (simplejwt + blacklist), LoginRateThrottle, ResetRateThrottle | M | A3 |
| A5 | Auth endpoints: register, login, verify, reset, refresh, logout | L | A4 |
| A6 | Profile + Address CRUD endpoints | M | A5 |
| A7 | AuditLogMiddleware in `core` | S | A2 |
| A8 | `/health/` endpoint (DB + Redis check) | S | A2 |

**Workstream B — Catalog + Inventory**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| B1 | `catalog` app: Category, Product, ProductImage, SKU, SkillTag models + migrations | L | A1 |
| B2 | `inventory` app: StockLevel, StockMovement, StockAlert models + migrations | M | B1 |
| B3 | Catalog API: ProductViewSet, CategoryViewSet, django-filter, full-text search | L | B1 |
| B4 | Inventory services: reserve_stock (select_for_update + nowait), release_stock, adjust_stock | M | B2 |
| B5 | Stock alert signal + admin stock adjustment endpoint | S | B4 |
| B6 | Seed data: ~20 products, categories, images, stock levels | M | B1, B2 |
| B7 | Django admin: Product, Category, SKU, StockLevel inlines | M | B1, B2 |

**Workstream C — Frontend Foundation**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| C1 | Vite + React 18 + TS scaffold, Tailwind config, ESLint, Prettier | M | — |
| C2 | TypeScript domain interfaces (all types from §5 Data Models) | M | C1 |
| C3 | Axios API client: base URL from `VITE_API_BASE_URL`, JWT interceptor, 401 refresh retry | M | C2 |
| C4 | API module stubs (auth, products, categories, cart, checkout, orders, account) | M | C3 |
| C5 | TanStack Query config + query key factory | S | C4 |
| C6 | Zustand stores: authStore, uiStore, checkoutStore | M | C2 |
| C7 | React Router: all routes with lazy imports, route guards | M | C6 |
| C8 | Layout shell: Header (logo, SearchBar, CartIconBadge, nav), Footer, Breadcrumbs | M | C7 |
| C9 | ToastProvider (aria-live), ErrorBoundary per route | S | C6 |
| C10 | PostHog init + analytics.ts wrapper (with ad-blocker fallback) | S | C1 |
| C11 | Sentry React init + ErrorBoundary | S | C1 |

**QA Gate — Foundation (all 3 QA agents run in parallel)**

| QA Task | QA Agent | Validates | Pass Criteria |
|---------|----------|-----------|---------------|
| QA-A | `qa_backend` | Workstream A | User model migrates cleanly; all auth endpoints return correct HTTP codes; `/health/` returns 200; audit middleware logs admin actions |
| QA-B | `qa_inventory` | Workstream B | All catalog models have correct indexes; `reserve_stock` prevents oversell under concurrent access (threading test); seed data loads without errors; StockAlert fires on low threshold |
| QA-C | `qa_frontend` | Workstream C | Vite builds with zero TypeScript errors; all routes render without crash; API client interceptor refreshes expired tokens; WCAG: all interactive elements keyboard-accessible |

> **Gate rule:** Workstreams D, E, F cannot start until QA-A, QA-B, and QA-C all pass. Failures route back to the responsible implementation agent for revision.

#### Week 2-4: Core Features

**Workstream D — Cart + Checkout Backend**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| D1 | `cart` app: Cart, CartItem models, CartViewSet, guest middleware | L | A3, B1 |
| D2 | Cart merge endpoint (`POST /cart/merge/`) | S | D1 |
| D3 | `checkout` app: CheckoutSession, ShippingRate, TaxCalculation models | L | D1 |
| D4 | State rate fixture (50 states), TaxService, ShippingService | M | D3 |
| D5 | Checkout step validation + state machine | M | D3 |
| D6 | Session CRUD + step PATCH endpoints | L | D5 |
| D7 | Seed: 1 flat-rate ShippingRate ($5.99 "Standard Shipping", 3-7 business days) | S | D3 |

**Workstream E — Payments + Orders Backend**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| E1 | `payments` app: Payment, Transaction, Refund, WebhookEvent models | L | A1 |
| E2 | stripe_client.py: SDK wrapper, idempotency key management | M | E1 |
| E3 | PaymentService.create_intent() → Stripe PaymentIntent | M | E2, D3 |
| E4 | `POST /payments/intent/` endpoint | M | E3 |
| E5 | Webhook endpoint: signature verify, WebhookEvent persistence, idempotency check | L | E2 |
| E6 | `orders` app: Order, OrderItem, OrderStatusHistory models | L | A3 |
| E7 | OrderService.create_order(): atomic (stock decrement + order creation + email) | L | E6, B4 |
| E8 | `payment_intent.succeeded` handler: calls OrderService.create_order() | M | E5, E7 |
| E9 | `payment_intent.payment_failed` handler | S | E5 |
| E10 | `POST /checkout/sessions/{token}/submit/`: atomic submit tying checkout→payment→order | L | D6, E4, E7 |
| E11 | Refund endpoint + `charge.refunded` webhook handler | M | E5 |
| E12 | Order confirmation email template + dispatch (SendGrid in prod, console in dev); includes signed download URLs for digital products (FR-ORD-03) | M | E7, A2 |
| E13 | Guest order tracking: HMAC token generation, `/orders/track/` endpoint | M | E6 |
| E14 | Order history + detail endpoints (authenticated) | M | E6 |

**Workstream F — Frontend Features**

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| F1 | Auth pages: Login, Register, Email Verification, Password Reset | L | C7, C3 |
| F2 | ShopPage + CategoryPage: filter sidebar (URL param sync), sort, ProductGrid | L | C8 |
| F3 | ProductCard component (image, title, price, stock badge) | M | C2 |
| F4 | ProductDetailPage: ImageGallery (keyboard zoom), info, specs, SEO meta (react-helmet-async) | L | F3 |
| F5 | SearchBar (global, debounced) + SearchResultsPage | M | C8 |
| F6 | AddToCartBlock + CartIconBadge + visual confirmation toast | M | C9 |
| F7 | CartPage: LineItems, QuantitySelector, subtotal, empty state | M | F6 |
| F8 | CartProvider: load on mount, guest token, merge trigger post-login | M | C6, F7 |
| F9 | CheckoutLayout: 4-step wizard, progress indicator, back nav blocker | L | C7 |
| F10 | Step 1: ContactStep (guest email / logged-in summary) | M | F9 |
| F11 | Step 2: ShippingStep (AddressForm, saved addresses dropdown, billing toggle, tax display) | L | F10 |
| F12 | Step 3: PaymentStep (Stripe Elements, decline handling) | L | F11 |
| F13 | Step 4: ReviewStep (order summary + PlaceOrderButton with idempotency key) | M | F12 |
| F14 | OrderConfirmationPage (guest account prompt) | M | F13 |
| F15 | AccountLayout + ProfilePage + AddressBook | M | F1 |
| F16 | OrderHistoryPage (cursor pagination, detail view) | M | F15 |

**QA Gate — Core Features (all 3 QA agents run in parallel)**

| QA Task | QA Agent | Validates | Pass Criteria |
|---------|----------|-----------|---------------|
| QA-D | `qa_checkout` | Workstream D | Checkout session creates from cart; all 4 steps validate correctly; tax calculation returns correct amounts for 5 sample states + exempt case; flat-rate shipping seed present; session expires after TTL |
| QA-E | `qa_payments` | Workstream E | Stripe PaymentIntent creates in test mode; webhook signature verification rejects invalid signatures; `payment_intent.succeeded` creates Order + decrements stock atomically; refund does not exceed payment amount; order confirmation email dispatches |
| QA-F | `qa_frontend` | Workstream F | Full checkout wizard navigable (4 steps, forward+back); Stripe Elements mounts; guest cart persists in localStorage; cart merge fires on login; PlaceOrderButton disables on click (double-submit prevention); OOS badge renders on product cards |

> **Gate rule:** Workstreams G and H cannot start until QA-D, QA-E, and QA-F all pass.

#### Week 5-6: Integration + Analytics

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| G1 | Wire all 12 PRD analytics events (frontend + backend) | M | C10, QA-D/E/F gate |
| G2 | `analytics` app: AnalyticsEvent model, event ingestion endpoint, @track_event decorator | M | A1 |
| G3 | Cart abandonment detection management command | M | G2 |
| G4 | Operational dashboard endpoint (orders, fulfillment, stock, failures) | M | E6, B5 |
| G5 | Django admin customization: Order management, stock views, refund actions | L | E6, B7 |

**QA Gate — Integration (2 QA agents run in parallel)**

| QA Task | QA Agent | Validates | Pass Criteria |
|---------|----------|-----------|---------------|
| QA-G | `qa_analytics` | G-analytics (G1-G3) | All 12 PRD events fire correctly (verify via AnalyticsEvent table); PostHog receives events in test; cart abandonment detection command identifies carts >24h old; ad-blocker fallback writes to backend |
| QA-G2 | `qa_backend` | G-admin (G4-G5) | Operational dashboard returns correct counts; Django admin shows order list with filters; refund action creates Refund record |

**Critic Loop — Week 6 (runs after QA-G/QA-G5 pass)**

All 4 critic agents run in parallel against the combined output of all workstreams A-G:

| Critic | Key Checks at This Stage |
|--------|--------------------------|
| **Auditor** | Every FR-* in PRD has at least one task covering it; no scope creep items remain in MVP |
| **Security** | Stripe webhook verify confirmed; JWT stored correctly; PII fields encrypted; rate limiting on login + reset |
| **Implementation** | No over-engineered components for 20-product MVP; all tasks have concrete file paths; effort estimates realistic |
| **Observability** | `/health/` endpoint present; Sentry on both frontend+backend; structured JSON logging configured; stock alert delivery mechanism exists |

> **Loop rule:** If any critic flags `has_issues=True`, the orchestrator routes feedback to the relevant implementation agent(s), which revise and re-run their paired QA agent. Max 3 iterations, or until all critics return clean.

> **Gate rule:** Workstream H cannot start until the Critic Loop completes (converges or exhausts 3 iterations).

#### Week 7-8: Polish + Hardening

| Task | Description | Effort | Depends |
|------|-------------|--------|---------|
| H1 | Accessibility audit: focus management, ARIA, keyboard nav, color contrast | L | all F tasks |
| H2 | CORS configuration (Railway env var for allowed origins) | S | A1 |
| H3 | HTTPS enforcement: SECURE_SSL_REDIRECT, HSTS, SECURE_PROXY_SSL_HEADER | S | A1 |
| H4 | Production logging tuning: log level=INFO, PII scrub filter, Railway log drain config | S | A2 |
| H5 | Docker Compose: postgres, redis, web, frontend, nginx | L | — |
| H6 | Railway deploy configuration: railway.toml, env vars, health check | M | H5 |
| H7 | Gunicorn config: workers=2*CPU+1, CONN_MAX_AGE=600, timeout=30 | S | A1 |
| H8 | End-to-end tests: guest checkout, registered checkout, payment failure + retry | L | all |
| H9 | Performance: code splitting, lazy routes, image srcset, LCP < 2s validation | M | all F tasks |
| H10 | Security: Stripe webhook verify test, JWT storage audit, PII encryption audit | M | E5, A5 |

**Final QA Gate — Hardening (`qa_auth` + `qa_frontend` run in parallel)**

| QA Task | QA Agent | Validates | Pass Criteria |
|---------|----------|-----------|---------------|
| QA-H1 | `qa_auth` | H3, H7, H10 | HTTPS redirect works; HSTS header present; gunicorn spawns correct worker count; BCrypt hash cost = 12; all encrypted fields unreadable in raw DB query |
| QA-H2 | `qa_frontend` | H1, H9 | axe-core reports zero critical violations; LCP < 2s on product detail page (Lighthouse); all route chunks load lazily; image `srcset` present on product images |
| QA-H3 | All QA agents | H8 | E2E: guest checkout completes; registered checkout completes; payment decline shows error and preserves cart; Playwright tests pass |

> **Ship criteria:** All QA gates pass. All critic loops converged or reached max iterations. Zero critical issues in final QA.

### Phase 2: Growth (6-8 weeks after MVP)

- Purchase orders: PurchaseOrder model, upload + approve/reject + invoicing
- PayPal: Stripe PaymentElement upgrade (supports both card + PayPal)
- Tax-exempt purchasing: certificate upload + admin verification
- Save-for-later + reorder
- Product reviews (star ratings, verified purchaser, moderation)
- USPS address validation
- Social login (Google)
- Full analytics dashboards (funnel viz, revenue charts, abandonment reports)
- Abandoned cart email recovery
- Bulk ordering improvements

### Phase 3: Optimization (8-12 weeks after Phase 2)

- Celery + Redis for async tasks (emails, analytics, stock alerts, PO notifications)
- Elasticsearch for advanced search (faceted, autocomplete, fuzzy)
- AI product recommendations
- Personalized browsing by profile
- Multi-ship-to PO orders
- Shipping integration (EasyPost/ShipStation)
- Subscription/auto-reorder

---

## 8. Local Dev Setup & Run Commands

### One-Command Setup

```bash
make setup
```

This single command handles everything — no manual steps, no prerequisites beyond Docker:

```makefile
.PHONY: setup dev stop clean test

setup:
	@echo "Setting up Upstream Literacy E-Commerce..."
	cp -n .env.example .env 2>/dev/null || true
	docker compose build
	docker compose run --rm backend python manage.py migrate
	docker compose run --rm backend python manage.py seed_products
	docker compose run --rm backend python manage.py createsuperuser --noinput || true  # uses DJANGO_SUPERUSER_EMAIL + _PASSWORD; custom User model has no username field
	docker compose run --rm frontend npm install
	@echo ""
	@echo "Setup complete. Run 'make dev' to start all services."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Admin:    http://localhost:8000/admin/"
	@echo "  Login:    admin@upstream.dev / admin123!"

# One-Command Run — starts everything
dev:
	docker compose up

# Stop all services
stop:
	docker compose down

# Full reset (wipe DB, rebuild)
clean:
	docker compose down -v
	docker compose build --no-cache

# Run all tests
test:
	docker compose run --rm backend pytest
	docker compose run --rm frontend npm test
```

### One-Command Run

```bash
make dev
```

Starts all services with live output, hot-reload on both backend and frontend:

- **Backend** (Django): http://localhost:8000 — file watcher auto-reloads on Python changes
- **Frontend** (Vite): http://localhost:5173 — HMR for instant React updates
- **Admin**: http://localhost:8000/admin/ — `admin@upstream.dev` / `admin123!`
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Stripe webhooks** (dev): `stripe listen --forward-to localhost:8000/api/v1/payments/webhooks/stripe/`

Press `Ctrl+C` to stop everything. Run `make stop` to clean up containers.

### Environment Variables (`.env.example`)

```bash
# Django
DJANGO_SETTINGS_MODULE=config.settings.local
SECRET_KEY=change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://upstream:upstream@localhost:5432/upstream_ecom

# Redis
REDIS_URL=redis://localhost:6379/0

# Auth (createsuperuser --noinput reads these; no USERNAME needed — custom User uses email)
DJANGO_SUPERUSER_EMAIL=admin@upstream.dev
DJANGO_SUPERUSER_PASSWORD=admin123!

# Stripe (test keys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email (console in dev)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
# Production: django.core.mail.backends.smtp.EmailBackend
# SENDGRID_API_KEY=SG.xxx

# PII Encryption
FIELD_ENCRYPTION_KEY=change-me-in-production

# PostHog
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://app.posthog.com

# Sentry
SENTRY_DSN=https://xxx@sentry.io/xxx

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_POSTHOG_KEY=phc_...
VITE_POSTHOG_HOST=https://app.posthog.com
VITE_SENTRY_DSN=https://xxx@sentry.io/xxx
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Docker Compose

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: upstream_ecom
      POSTGRES_USER: upstream
      POSTGRES_PASSWORD: upstream
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U upstream"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python manage.py runserver 0.0.0.0:8000
    ports: ["8000:8000"]
    volumes:
      - ./backend:/app
      - media_data:/app/media
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    command: npm run dev -- --host 0.0.0.0
    ports: ["5173:5173"]
    volumes:
      - ./frontend:/app
      - /app/node_modules
    env_file: .env
    depends_on:
      - backend

volumes:
  pgdata:
  media_data:
```

**New developer experience:** Clone the repo → `make setup` → `make dev`. Under 5 minutes to first page load. No local Python, Node, or Postgres installation required — only Docker.

---

## 9. Observability Plan

### 9.1 Logging

- **Format:** JSON structured logging via `python-json-logger`
- **Fields per log line:** timestamp, level, logger, message, request_id, user_id, path
- **Levels by environment:** local=DEBUG, production=INFO
- **PII scrubbing:** Custom filter strips email, address fields from log output
- **Correlation:** `X-Request-ID` header set by middleware, propagated through all logs

### 9.2 Error Monitoring (Sentry)

- **Backend:** `sentry-sdk[django]`, `traces_sample_rate=0.1`, PII scrub in `before_send`
- **Frontend:** `@sentry/react`, `BrowserTracing`, `Replay(sessionSampleRate=0.1, errorSampleRate=1.0)`
- **Alert rules:**
  - Error rate > 1% over 5 minutes → Sentry alert
  - Payment failure rate > 10% over 5 minutes → critical alert
  - Unhandled exception → immediate alert

### 9.3 Health Checks

- **`/health/`** — checks DB connectivity (`SELECT 1`) + Redis ping; returns JSON status
- **Railway config:** health check path = `/health/`, interval = 30s, timeout = 5s
- **External monitor:** UptimeRobot free tier pinging `/health/` every 5 minutes; alerts on 2 consecutive failures

### 9.4 Performance Monitoring

- **API latency:** Sentry Performance (traces_sample_rate=0.1); alert if p95 > 300ms
- **Database:** `log_min_duration_statement=200` in PostgreSQL (Railway config); Django `assertNumQueries` in tests
- **Frontend:** Sentry Web Vitals (LCP, FID, CLS); alert if LCP > 2s

### 9.5 Business Metrics (PostHog)

- All 12 PRD events tracked (PRD §8.1)
- Primary + secondary funnels defined in PostHog
- Cart abandonment detected nightly via management command
- Operational dashboard via custom Django API (live DB queries, 60s cache)

### 9.6 Alerting Summary

| Alert | Source | Threshold | Channel |
|-------|--------|-----------|---------|
| Uptime | UptimeRobot | 2 consecutive failures | Email |
| Error spike | Sentry | >1% error rate / 5min | Email + Slack |
| Payment failures | Sentry | >10% / 5min | Email (critical) |
| Low stock | StockAlert model | Configurable per-SKU | Admin dashboard + email (daily cron) |
| Backorder overdue | StockAlert model | Past estimated_restock_date | Admin dashboard + email (daily cron) |
| Checkout abandonment | Weekly report | N/A | Email to leadership (weekly cron) |

---

## 10. Testing Strategy

### 10.1 Unit Tests

- **Framework:** pytest + pytest-django
- **Coverage target:** 80% on service layer (`services.py` files)
- **Key test areas:**
  - `reserve_stock` concurrent access (threading test with `select_for_update`)
  - Password validators (min length, digit, special char)
  - Tax calculation (all 50 states + exempt)
  - Cart merge logic
  - Idempotency key generation
  - Stripe client wrapper (mocked SDK)

### 10.2 Integration Tests

- **Framework:** DRF `APITestCase` + pytest
- **Stripe:** `stripe-mock` or `pytest-stripe` with test keys
- **Key test flows:**
  - Full auth flow: register → verify → login → refresh → logout
  - Full checkout flow: cart → session → steps → submit → order created
  - Payment failure → retry → success
  - Stock conflict at submit (concurrent checkout)
  - Webhook idempotency (duplicate event)
  - Refund: full and partial

### 10.3 End-to-End Tests

- **Framework:** Playwright
- **Key scenarios:**
  - Guest checkout: browse → add to cart → checkout → pay → confirmation
  - Registered user: login → add to cart → checkout with saved address → pay
  - Search → product detail → add to cart
  - Cart persistence: add item, close tab, return, cart intact
  - Out-of-stock: verify badge + disabled button
  - Payment decline: error message shown, cart preserved

### 10.4 Accessibility Tests

- **Automated:** axe-core in CI (Playwright integration)
- **Manual:** Screen reader testing (VoiceOver) before launch on:
  - Product detail page
  - Checkout flow (all 4 steps)
  - Cart management

### 10.5 Frontend Unit Tests

- **Framework:** Vitest + React Testing Library
- **Coverage:** Form validation, route guards, Zustand store logic, analytics event fire

---

## 11. PRD Traceability Matrix

| PRD Requirement | Backend | Frontend | Tests |
|-----------------|---------|----------|-------|
| **FR-CAT-01** Category taxonomy | catalog: Category model, CategoryViewSet | CategorySidebar, CategoryPage, breadcrumbs | B3, F2 |
| **FR-CAT-02** Product detail | catalog: ProductDetailSerializer, images | ProductDetailPage, ImageGallery, SEO meta | B3, F4 |
| **FR-CAT-03** Search | catalog: full-text search view | SearchBar, SearchResultsPage | B3, F5 |
| **FR-CAT-04** Reviews | Phase 2 | Phase 2 | — |
| **FR-CART-01** Add to cart | cart: CartViewSet POST | AddToCartBlock, CartIconBadge, toast | D1, F6 |
| **FR-CART-02** Cart management | cart: PATCH/DELETE items | CartPage, QuantitySelector, empty state | D1, F7 |
| **FR-CART-03** Cart persistence | cart: server-side + guest token | CartProvider, localStorage, merge on login | D1, D2, F8 |
| **FR-CART-04** Save for later | Phase 2 | Phase 2 | — |
| **FR-CHK-01** Guest checkout | checkout: guest_email on session | ContactStep, email-only flow, account prompt | D6, F10, F14 |
| **FR-CHK-02** Registered checkout | checkout: user FK, saved addresses | ShippingStep dropdown, ≤4 steps | D6, F11 |
| **FR-CHK-03** Shipping address | checkout: address JSON fields | AddressForm, billing toggle | D6, F11 |
| **FR-CHK-04** Tax calculation | checkout: TaxService + state table | TaxDisplay, exempt label | D4, F11 |
| **FR-CHK-05** Order review + confirm | checkout: submit endpoint | ReviewStep, PlaceOrderButton, ConfirmationPage | E10, F13, F14 |
| **FR-PAY-01** Card payments | payments: Stripe PaymentIntent | Stripe Elements, decline handling | E3-E5, F12 |
| **FR-PAY-02** PayPal | Phase 2 | Phase 2 | — |
| **FR-PAY-03** Purchase orders | Phase 2 | Phase 2 | — |
| **FR-ORD-01** Order status | orders: Order model, status transitions | OrderHistoryPage, guest tracking | E6, E13, F16 |
| **FR-ORD-02** Email notifications | orders: confirmation email via SendGrid | — (server-side only) | E12 |
| **FR-ORD-03** Digital delivery | orders: signed URL in confirmation email | Download link on confirmation page | E7, F14 |
| **FR-INV-01** Stock tracking | inventory: StockLevel, atomic decrement, alerts | Stock badge, disabled purchase | B4, B5, F3 |
| **FR-INV-02** Digital vs physical | catalog: product_type field, is_unlimited | Conditional shipping display | B1, B4 |
| **FR-INV-03** Backorder | inventory: backorder_enabled, restock date | "Ships by [date]" label | B2, F3 |
| **FR-ACCT-01** Registration + auth | accounts: User, JWT, verify, reset | LoginPage, RegisterPage, verification | A3-A5, F1 |
| **FR-ACCT-02** Profile + institution | accounts: UserProfile, Institution, Address | ProfilePage, AddressBook | A6, F15 |
| **FR-ACCT-03** Order history | orders: OrderViewSet + filters | OrderHistoryPage | E14, F16 |
| **§7.1** Performance | gunicorn, CONN_MAX_AGE, cursor pagination | Code split, lazy routes, LCP < 2s | H7, H9 |
| **§7.2** Security | BCrypt(12), PII encryption, RBAC, audit log, Stripe webhook verify | JWT in memory, httpOnly refresh cookie | H10 |
| **§7.3** Accessibility | — | WCAG 2.1 AA, focus mgmt, ARIA, contrast | H1 |
| **§7.4** Scalability | Gunicorn workers, CONN_MAX_AGE, stateless app | CDN for static (Railway) | H7 |
| **§7.5** Reliability | /health/, Sentry, daily DB backups (Railway), graceful errors | Sentry React, ErrorBoundary | H6, C11 |
| **§8.1-8.4** Analytics | analytics: events, abandonment, dashboards | PostHog JS, analytics.ts | G1-G4 |
