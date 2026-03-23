# System Patterns & Architecture

**Source:** PRD §9 (Technical Considerations)

## High-Level Architecture

```
Frontend (React + TypeScript + Tailwind)
    ↓ REST API (JSON)
Backend (Django + Django REST Framework)
    ├── Catalog, Cart, Checkout, Orders
    ├── Inventory, Accounts, Payment, Analytics
    ↓
PostgreSQL | Redis | S3/CDN
```

- **Stateless app design** for scaling (e.g. back-to-school load)
- **RESTful, versioned** APIs: `/api/v1/products/`, `/api/v1/cart/`, etc.
- **JWT** for API auth; session-based for web app
- **Cursor-based pagination** on list endpoints
- **Filterable catalog:** `?grade=2&category=phonics`

---

## Service Layout

| Service | Responsibility |
|---------|----------------|
| Catalog | Products, categories, search |
| Cart | Add/remove, persistence, merge |
| Checkout | Addresses, tax, order review |
| Orders | Status, notifications, fulfillment |
| Inventory | Stock tracking, decrements |
| Accounts | Auth, profiles, tax-exempt |
| Payment | Stripe integration, PO handling |
| Analytics | Events, funnel, dashboards |

---

## Key Patterns

- **PCI compliance:** Stripe Elements (hosted fields) — no raw card data on our servers
- **Atomic stock decrement:** Database-level; avoid overselling
- **Guest cart merge:** On login, merge guest cart with account cart (quantities summed)
- **Digital delivery:** Signed URLs, 7-day validity, re-generable from account

---

## Future Extensibility (PRD §9.5)

- Subscriptions (recurring orders)
- Digital content platform (beyond downloads)
- Multi-currency (avoid hardcoding USD)
- API-first for LMS/library integrations
