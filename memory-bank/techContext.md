# Tech Context

**Source:** PRD §9 (Technology Stack)

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18 + TypeScript + Tailwind CSS |
| Backend | Django 5 + Django REST Framework |
| Database | PostgreSQL 16 |
| Cache | Redis |
| Task Queue | Celery + Redis |
| File Storage | AWS S3 (or compatible) |
| CDN | CloudFront or Cloudflare |
| Search (MVP) | PostgreSQL full-text |
| Search (Phase 2) | Elasticsearch |

---

## Integrations

| Purpose | Provider |
|---------|----------|
| Payment | Stripe (cards, PayPal) |
| Email (tx) | SendGrid or Amazon SES |
| Tax | TaxJar or manual state table (MVP) |
| Address validation | USPS or SmartyStreets |
| Shipping (MVP) | Flat-rate table |
| Analytics | PostHog or Mixpanel |
| Error monitoring | Sentry |

---

## API Design

- **Versioned:** `/api/v1/`
- **Authenticated:** JWT tokens; CORS for frontend domain(s)
- **Paginated:** Cursor-based on lists
- **Filterable:** Query params on catalog (`?grade=2&category=phonics`)

---

## Non-Functional

- **Accessibility:** WCAG 2.1 AA
- **Performance:** Product page < 2s
- **Security:** PCI via Stripe; encrypted PII; regular dependency updates
- **Load:** Stateless design; connection pooling; CDN for static/media
