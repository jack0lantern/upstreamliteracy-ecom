# Product Context

**Source:** `docs/UpstreamLiteracy-ecom-prd_v1.md` (PRD v2.0)

## Personas

### Ms. Carter — Classroom Teacher
- 2nd-grade teacher, $200/year out-of-pocket; shops evenings
- Needs decodable readers aligned to phonics scope; clear pricing (incl. shipping)
- Pain: Can't browse without calling; no self-serve discovery

### Dr. Reeves — Curriculum Director
- K-5 director, 12-school district; $50K budget
- Needs bulk orders, PO workflow, multi-ship-to, tax-exempt
- Pain: Phone/email incompatible with procurement; no formal quotes/invoices

### Maria — Parent / Homeschool
- Parent of struggling reader; $50–150 budget
- Needs skill-level guidance; guest checkout; reviews
- Pain: Overwhelmed by options; wants low-friction purchase

---

## Core Journeys

1. **Browse → Cart → Checkout (Individual):** Land on shop → browse/search → product detail → add to cart → guest or account checkout → payment → confirmation
2. **Guest vs Account:** Guest = email only; optional post-purchase account creation
3. **PO/Bulk:** Add items → "Pay by PO" → PO number + PDF upload → multiple ship-to → Pending Approval → staff approves → invoice → Net 30/60
4. **Reorder:** Account → Order History → Reorder → adjust quantities → checkout

---

## Functional Scope (MVP)

- **Catalog:** Categories (grade, skill, format), search, product detail, reviews
- **Cart:** Add/remove, quantity, persistence (30 days guest; server-side for accounts), save for later
- **Checkout:** Guest + registered; shipping; tax + exemption; order review
- **Payment:** Stripe (cards, PayPal); PO option with approval workflow
- **Orders:** Status tracking; email notifications; digital download delivery
- **Inventory:** Stock tracking; out-of-stock handling
- **Accounts:** Registration; order history; saved addresses; tax-exempt flag

---

## Edge Cases (PRD)

- Out-of-stock: badge, disable add; "Notify me"; cart validation
- Payment failure: retain cart, clear error
- Tax-exempt: account flag, certificate upload, staff approval
- PO: Pending Approval; staff review; approve/reject
- Cart merge: guest cart → account on login (quantities summed)
