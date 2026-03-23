# Product Requirements Document: Upstream Literacy E-Commerce Platform

**Version:** 2.1
**Date:** 2026-03-23
**Status:** Stakeholder Questions Resolved — Ready for Engineering
**Category:** AI-ACCELERATED

---

## Table of Contents

1. [Company Research & Market Context](#1-company-research--market-context)
2. [Product Strategy & Synthesis](#2-product-strategy--synthesis)
3. [Overview](#3-overview)
4. [User Personas](#4-user-personas)
5. [User Journeys](#5-user-journeys)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Data & Analytics](#8-data--analytics)
9. [Technical Considerations](#9-technical-considerations)
10. [Risks & Mitigations](#10-risks--mitigations)
11. [Phased Rollout Plan](#11-phased-rollout-plan)

---

## 1. Company Research & Market Context

### 1.1 Organization Profile

**Upstream Literacy** is an early-stage literacy education organization registered under the entity "Understanding How," based in Illinois. The organization operates in the structured literacy and science-of-reading space, providing curriculum materials, decodable readers, and educator resources to schools, districts, and individual teachers.

- **Domain:** upstreamliteracy.org (registered October 2025)
- **Current state:** Pre-launch website; active manual sales via phone and email
- **Business model:** Product sales (physical and potentially digital literacy materials) with likely future expansion into training and professional development services
- **Legal structure:** Not a 501(c)(3) nonprofit; standard business entity

### 1.2 Target Audience

| Segment | Description | Buying Behavior |
|---------|-------------|-----------------|
| **K-5 Educators** | Classroom teachers implementing structured literacy curricula | Individual purchases, often out-of-pocket; price-sensitive; need materials aligned to science of reading |
| **Literacy Coaches & Specialists** | School-based reading interventionists | Buy supplemental and intervention materials; influenced by training programs they attend |
| **School Administrators** | Principals, curriculum directors | Bulk purchases; require purchase orders; need alignment to state standards |
| **District Procurement** | Central office buyers | Large orders; formal PO/invoicing workflows; tax-exempt; multi-school distribution |
| **Parents / Homeschool Educators** | Families supporting reading at home | Individual purchases; credit card / PayPal; motivated by child's specific reading level |

### 1.3 Products & Services (Inferred)

Based on the literacy education market and the organization's positioning:

- **Decodable readers** — phonetically controlled texts organized by skill progression
- **Phonics and phonemic awareness materials** — teacher-facing instructional resources
- **Curriculum kits / bundles** — grade-level or intervention-level packages
- **Professional development materials** — training guides, implementation manuals
- **Digital resources** — downloadable lesson plans, assessment tools, printable materials (ready for digital delivery at launch)

### 1.4 Competitive Landscape

| Competitor | Type | E-commerce Maturity | Key Strength |
|-----------|------|---------------------|-------------|
| Heggerty (shop.heggerty.org) | Direct competitor | Full Shopify store | Strong brand in phonemic awareness; clean shopping UX |
| Really Great Reading | Direct competitor | Basic e-commerce | Intervention-focused; school PO support |
| Learning A-Z (Raz-Plus) | Digital platform | Subscription model | Massive digital library; per-seat licensing |
| Teachers Pay Teachers | Marketplace | Mature marketplace | Teacher-created content; low prices; instant digital delivery |
| Scholastic Education | Large publisher | Enterprise e-commerce | Brand recognition; school book fairs; bulk ordering |
| Amplify / Lexia | EdTech platform | Enterprise sales | District-level contracts; integrated assessment |

### 1.5 Key Differentiators & Gaps

**Differentiators for Upstream Literacy:**
- Focused specifically on structured literacy / science of reading (vs. balanced literacy)
- Nimble and educator-founded (assumed), allowing faster iteration than large publishers
- Potential to combine physical materials with digital delivery

**Current Experience Gaps:**
- **No online purchasing** — phone/email only, creating massive friction
- **No product browsing** — customers cannot self-serve to discover products
- **No order tracking** — customers have no visibility after placing an order
- **No analytics** — organization has zero data on customer behavior
- **2-3 hours daily** spent on manual order processing that could be automated

---

## 2. Product Strategy & Synthesis

### 2.1 Core User Problems

| Problem | Impact | Severity |
|---------|--------|----------|
| Cannot browse or purchase products online | Lost sales from educators who expect self-serve purchasing | Critical |
| Phone/email ordering creates friction and delays | Abandoned purchases; limits sales to business hours and staff availability | Critical |
| No bulk ordering workflow for schools | District buyers go elsewhere or delay purchases | High |
| No order status visibility | Support burden; poor customer experience | Medium |
| Manual inventory tracking | Overselling; fulfillment delays; staff time waste | High |

### 2.2 E-Commerce Opportunities

- **Self-serve purchasing** removes the #1 barrier to sales — friction
- **24/7 availability** captures purchases outside business hours (teachers shop evenings/weekends)
- **Bulk ordering with PO support** opens the school/district sales channel properly
- **Digital delivery** enables instant access to downloadable resources (zero fulfillment cost)
- **Reorder flows** increase lifetime value from returning educators and schools
- **Data-driven optimization** enables targeted outreach, inventory planning, and product development

### 2.3 Key Success Metrics

| Metric | Target (MVP) | Target (6-month) | Rationale |
|--------|-------------|-------------------|-----------|
| **Conversion rate** (visitor → purchase) | 2.0% | 3.5% | Education e-commerce benchmarks |
| **Cart abandonment rate** | < 75% | < 65% | Industry average ~70%; education slightly higher |
| **Average order value** | $45 | $65 | Increase via bundles and bulk pricing |
| **Time-to-purchase** (browse → checkout) | < 8 min | < 5 min | Reduce friction from current phone/email flow |
| **Manual processing time** | < 30 min/day | < 15 min/day | Down from current 2-3 hours/day |
| **Checkout success rate** | > 95% | > 98% | Payment + form completion |
| **Repeat purchase rate** | — | 25% | Loyalty and reorder flow effectiveness |

### 2.4 Constraints

- **Budget sensitivity:** Schools and individual teachers have limited budgets; pricing transparency and value framing are essential
- **Purchase order workflows:** Schools cannot use credit cards for institutional purchases; PO/invoicing support is a must-have for the school segment
- **Tax exemptions:** Most schools and districts are tax-exempt; the system must handle exemption certificates
- **Accessibility:** WCAG 2.1 AA compliance is both legally required (ADA) and ethically necessary for an education organization
- **Trust & compliance:** PCI DSS compliance for payment processing; COPPA awareness (if any student-facing components); FERPA irrelevant unless student data is collected
- **Seasonality:** School purchasing spikes in July-September (back-to-school) and January (second semester); system must handle 3-5x traffic surges

---

## 3. Overview

### 3.1 Product Name

**Upstream Literacy E-Commerce Platform** (internal); customer-facing as the shop section of upstreamliteracy.org

### 3.2 Problem Statement

Upstream Literacy currently processes all orders through phone and email, consuming 2-3 hours of staff time daily, creating purchase friction that results in lost sales, and providing zero visibility into customer behavior or inventory status. Educators, who predominantly shop during evenings and weekends, cannot discover or purchase products outside of business hours.

The organization needs a modern, self-serve e-commerce platform tailored to the education market — one that supports individual teacher purchases alongside school/district procurement workflows (including purchase orders and tax exemptions), and provides the analytics foundation to grow revenue and optimize the product catalog.

### 3.3 Goals

| Goal | Measurable Outcome |
|------|-------------------|
| Eliminate manual order processing bottleneck | Reduce daily processing time from 2-3 hours to < 30 minutes |
| Enable self-serve purchasing | 80%+ of orders placed through the e-commerce platform within 3 months of launch |
| Support school/district procurement | PO-based checkout flow operational at launch |
| Establish analytics foundation | Funnel tracking, cart abandonment, and conversion dashboards live at launch |
| Improve customer experience | Order status tracking, email confirmations, and account-based reordering |

---

## 4. User Personas

### 4.1 Persona: Ms. Carter — Classroom Teacher (Individual Buyer)

- **Role:** 2nd-grade teacher, Title I school in suburban Illinois
- **Budget:** $200/year out-of-pocket for supplemental materials; occasionally receives small classroom grants
- **Tech comfort:** Moderate; shops on Amazon, Teachers Pay Teachers regularly

**Jobs to Be Done:**
- Find decodable readers matched to the phonics skills her students are currently learning
- Purchase materials quickly during evening planning time
- Track when her order will arrive so she can plan lessons around new materials

**Pain Points:**
- Cannot browse products or check prices without calling/emailing during school hours
- Unsure which products align with her curriculum scope and sequence
- Small budget means she needs to know exact costs upfront (including shipping)

**Buying Motivations:**
- Student reading outcomes; materials aligned to structured literacy
- Convenience and speed of ordering
- Clear product descriptions with grade/skill alignment

---

### 4.2 Persona: Dr. Reeves — Curriculum Director (Bulk Purchaser)

- **Role:** K-5 Curriculum Director for a 12-school district in Indiana
- **Budget:** $50,000 annual curriculum materials budget; allocated across schools
- **Tech comfort:** High; manages vendor relationships, procurement portals

**Jobs to Be Done:**
- Evaluate and select literacy materials for district-wide adoption
- Place bulk orders for multiple schools with different shipping addresses
- Process purchases through the district's purchase order system (not personal credit cards)
- Track fulfillment across multiple shipment destinations

**Pain Points:**
- Current phone/email ordering is incompatible with district procurement workflows
- Cannot generate formal quotes or invoices needed for budget approval
- No way to track order status across multiple schools
- Needs tax-exempt purchasing without extra steps each time

**Buying Motivations:**
- Evidence-aligned materials (science of reading)
- Bulk pricing / volume discounts
- PO/invoicing support and tax-exempt purchasing
- Reliable fulfillment before the school year starts

---

### 4.3 Persona: Maria — Parent / Homeschool Educator (Individual Consumer)

- **Role:** Homeschooling parent of a 6-year-old struggling reader
- **Budget:** Variable; willing to spend $50-150 on the right materials
- **Tech comfort:** High; shops online frequently

**Jobs to Be Done:**
- Find reading materials appropriate for her child's current skill level
- Understand what she's buying before purchasing (previews, reviews, skill descriptions)
- Get materials delivered quickly or access digital resources immediately

**Pain Points:**
- Overwhelmed by literacy product options; needs guidance on what's appropriate
- Doesn't want to create an account just to make one purchase
- Wants to see other parents'/educators' reviews before buying

**Buying Motivations:**
- Child's reading progress
- Clear skill-level labeling and product descriptions
- Recommendations and reviews from educators
- Easy checkout (guest option)

---

## 5. User Journeys

### 5.1 Journey: Browse → Add to Cart → Checkout (Individual Purchase)

```
1. User lands on upstreamliteracy.org/shop
2. Browses by category (grade level, phonics skill, product type) or uses search
3. Views product detail page (description, skill alignment, preview, price, reviews)
4. Selects quantity → clicks "Add to Cart"
5. Cart sidebar/overlay shows updated cart with subtotal
6. User continues shopping or clicks "Checkout"
7. Checkout: enters email → shipping address → selects shipping method
8. Enters payment (credit card or PayPal)
9. Reviews order summary (items, shipping, tax, total)
10. Submits order
11. Confirmation page displayed + confirmation email sent
12. User can track order status via email link (or account if registered)
```

### 5.2 Journey: Guest Checkout vs. Account-Based Checkout

**Guest Checkout:**
```
1. No login required
2. Email collected at checkout for order confirmation and tracking
3. Post-purchase: prompted to create an account to save order history
4. Account creation is optional, low-friction (email already captured; just add password)
```

**Account-Based Checkout:**
```
1. User logs in or creates account before/during checkout
2. Saved addresses and payment methods pre-fill checkout fields
3. Order added to account history automatically
4. Institutional info (school name, tax-exempt status) persisted across orders
```

### 5.3 Journey: Bulk Purchasing / School Purchase Order

```
1. Dr. Reeves browses catalog, adds items for multiple schools
2. Adjusts quantities per school (or uses a bulk order form)
3. At checkout, selects "Purchase Order" as payment method
4. Enters PO number, uploads PO document (PDF)
5. Enters billing address (district office) and multiple shipping addresses (schools)
6. Selects "Bill me / Net 30" payment terms
7. Order submitted with "Pending PO Approval" status
8. Upstream Literacy staff reviews and approves the PO
9. Invoice generated and emailed to district
10. Order fulfilled; payment collected per agreed terms (Net 30/60)
```

### 5.4 Journey: Returning User Reorder

```
1. Logged-in user visits account → Order History
2. Finds previous order → clicks "Reorder"
3. Items added to cart with same quantities (with stock availability check)
4. User adjusts quantities if needed
5. Proceeds to checkout with saved address/payment
6. One-click-style checkout (review → submit)
```

### 5.5 Edge Cases

| Edge Case | Handling |
|-----------|---------|
| **Out-of-stock item** | Display "Out of Stock" badge on product page; disable "Add to Cart" button; offer "Notify me when available" email signup; if item goes OOS while in cart, alert user at checkout with option to remove or wait |
| **Payment failure** | Display clear error message ("Card declined — please check your card details or try another payment method"); retain cart and form state; log failure event for analytics |
| **Tax-exempt institution** | Account-level flag for tax-exempt status; upload exemption certificate during registration or checkout; staff reviews and approves exemption; tax removed from future orders automatically |
| **Purchase order** | PO payment option visible to all users; PO orders enter "Pending Approval" state; staff reviews PO document and approves/rejects; approved orders proceed to fulfillment with Net 30/60 invoicing |
| **Partial availability (bundle)** | If a bundle contains OOS items, display which items are unavailable; offer to ship available items now and backorder the rest, or wait for full availability |
| **Cart expiration** | Persistent cart for logged-in users (no expiration); guest carts persist for 30 days via cookie/local storage |
| **Shipping address validation** | Validate addresses via USPS/address verification API; prompt user to confirm suggested corrections |
| **Digital + physical mixed cart** | Show separate delivery sections: digital items available immediately post-purchase; physical items show estimated shipping date |

---

## 6. Functional Requirements

### 6.1 Product Catalog

#### FR-CAT-01: Category Taxonomy

- **Description:** Hierarchical product categories enabling educators to find materials by grade level, literacy skill focus, product format, and curriculum alignment.
- **Categories:**
  - By grade level: Pre-K, Kindergarten, Grade 1, Grade 2, Grade 3, Grade 4, Grade 5
  - By literacy focus: Phonemic Awareness, Phonics, Fluency, Vocabulary, Comprehension
  - By format: Decodable Readers, Teacher Guides, Student Workbooks, Kits/Bundles, Digital Downloads
  - By curriculum alignment: (configurable; e.g., aligned to specific scope & sequence)
- **User value:** Educators can rapidly narrow to relevant products using familiar educational terminology.
- **Acceptance criteria:**
  - Products can belong to multiple categories simultaneously
  - Category pages display product count and support sorting (price, newest, popularity)
  - Breadcrumb navigation shows category hierarchy
  - Empty categories are hidden from navigation

#### FR-CAT-02: Product Detail Pages

- **Description:** Rich product pages with all information an educator needs to make a purchasing decision.
- **Content:** Title, price, description, skill/grade alignment, images (cover + interior samples), format/specs, related products, educator reviews
- **User value:** Reduces purchase uncertainty; replaces the phone call currently required to learn about a product.
- **Acceptance criteria:**
  - Product page loads in < 2 seconds
  - At least one product image displayed; image zoom supported
  - Price and stock status clearly visible above the fold
  - "Add to Cart" button visible without scrolling
  - Related/recommended products shown below main content
  - SEO meta tags populated (title, description, Open Graph)

#### FR-CAT-03: Search

- **Description:** Full-text search across product titles, descriptions, and metadata.
- **User value:** Fast path to finding specific products, especially for educators who know what they need.
- **Acceptance criteria:**
  - Search bar accessible from every page (header)
  - Results displayed with product thumbnail, title, price, and relevance ranking
  - Supports partial matching and common misspellings (e.g., "fonics" → "phonics")
  - No-results page suggests categories or popular products
  - Search queries logged for analytics

#### FR-CAT-04: Product Reviews

- **Description:** Educator-submitted reviews with star ratings and text feedback.
- **User value:** Social proof from peers increases purchase confidence, especially for educators spending limited personal funds.
- **Acceptance criteria:**
  - Only verified purchasers can submit reviews
  - Reviews display reviewer name (or "Verified Educator"), rating (1-5 stars), date, and text
  - Average rating displayed on product cards and detail pages
  - Reviews moderated by staff before publishing (to prevent spam/inappropriate content)
  - Minimum 1 star, maximum 5 stars; text is optional but encouraged

---

### 6.2 Shopping Cart

#### FR-CART-01: Add to Cart

- **Description:** Users can add products to a persistent shopping cart from product pages and category listings.
- **User value:** Standard e-commerce interaction; reduces friction from current phone-based process.
- **Acceptance criteria:**
  - "Add to Cart" button on product detail pages and optionally on product cards
  - Visual confirmation when item is added (toast notification or cart sidebar animation)
  - Cart icon in header updates with item count badge
  - Adding an item already in cart increments quantity (does not create duplicate line)
  - Cannot add more than available stock quantity

#### FR-CART-02: Cart Management

- **Description:** Users can view and modify cart contents: adjust quantities, remove items, and see running totals.
- **User value:** Control over order before committing to purchase.
- **Acceptance criteria:**
  - Cart accessible via header icon (sidebar/overlay or dedicated page)
  - Each line item shows: product name, thumbnail, unit price, quantity selector, line total
  - Quantity adjustable via +/- buttons or direct input (minimum 1, maximum = stock)
  - Remove item button per line
  - Cart subtotal updates in real-time on quantity change
  - Empty cart state shows "Your cart is empty" with link to shop

#### FR-CART-03: Cart Persistence

- **Description:** Cart contents persist across browser sessions for both guests and logged-in users.
- **User value:** Teachers may browse on their phone during lunch and complete the purchase on their laptop at home.
- **Acceptance criteria:**
  - Logged-in users: cart stored server-side, accessible from any device
  - Guest users: cart stored in local storage / cookie, persisted for 30 days
  - On login, guest cart merges with any existing server-side cart (quantities summed, duplicates merged)
  - Cart items validated against current stock on cart load (stale items flagged)

#### FR-CART-04: Save for Later

- **Description:** Users can move items from active cart to a "Saved for Later" list.
- **User value:** Lets budget-conscious educators bookmark products without cluttering the cart.
- **Acceptance criteria:**
  - "Save for Later" action available per cart line item
  - Saved items displayed below the active cart
  - "Move to Cart" action on saved items
  - Saved items persist with same rules as cart (server-side for accounts, local storage for guests)
  - Saved items do not reserve inventory

---

### 6.3 Checkout System

#### FR-CHK-01: Guest Checkout

- **Description:** Users can complete a purchase without creating an account.
- **User value:** Reduces abandonment from forced registration; critical for first-time buyers and parents.
- **Acceptance criteria:**
  - "Checkout as Guest" option clearly presented alongside login
  - Only email address required as identifier (for order confirmation)
  - Full checkout flow functional without account
  - Post-purchase: prompt to create account with pre-filled email
  - Guest orders trackable via email link (order ID + email verification)

#### FR-CHK-02: Registered User Checkout

- **Description:** Logged-in users experience a streamlined checkout with saved information.
- **User value:** Faster repeat purchases; essential for the reorder flow.
- **Acceptance criteria:**
  - Saved shipping addresses selectable from dropdown
  - Option to add new address during checkout
  - Saved payment methods available (if supported by payment provider)
  - Institutional info (school name, tax-exempt status) auto-applied
  - Checkout completable in ≤ 4 steps/screens

#### FR-CHK-03: Shipping Address Handling

- **Description:** Collect and validate shipping and billing addresses; support separate addresses.
- **User value:** Accuracy in delivery; support for school shipping (different from home billing).
- **Acceptance criteria:**
  - Standard address fields: name, street 1, street 2, city, state, ZIP, country (US-only at MVP)
  - "Same as shipping" checkbox for billing address (default checked)
  - Address validation via USPS API or equivalent
  - For PO orders: support multiple shipping addresses (different schools in a district)
  - Address saved to account for logged-in users (with option to save or not)

#### FR-CHK-04: Tax Calculation & Exemptions

- **Description:** Calculate applicable sales tax; support tax-exempt purchases for qualifying institutions.
- **User value:** Accurate totals; no surprises at checkout; schools aren't overcharged.
- **Acceptance criteria:**
  - Tax calculated based on shipping destination (state + local rates)
  - Tax-exempt flag on customer accounts (set by staff after certificate review)
  - Tax-exempt certificate upload during checkout or account setup
  - Exempt orders show $0.00 tax with "Tax Exempt" label
  - Tax calculation service integrated (e.g., TaxJar, Avalara, or state-rate table for MVP)

#### FR-CHK-05: Order Review & Confirmation

- **Description:** Final review step before order submission; confirmation page and email after submission.
- **User value:** Confidence in the order; no post-purchase anxiety.
- **Acceptance criteria:**
  - Order review shows: all items with quantities and prices, subtotal, shipping cost, tax, total
  - "Place Order" button clearly labeled with total amount
  - On successful submission: confirmation page with order number, estimated delivery, and summary
  - Confirmation email sent within 60 seconds with same information
  - Email includes link to track order status

---

### 6.4 Payment Processing

#### FR-PAY-01: Credit / Debit Card Payments

- **Description:** Accept Visa, Mastercard, American Express, and Discover via a PCI-compliant payment processor.
- **User value:** Standard payment method for individual educators and parents.
- **Acceptance criteria:**
  - Payment form embedded via processor's hosted fields (Stripe Elements or equivalent) — no raw card data touches our servers
  - Real-time card validation (number, expiry, CVV)
  - Clear error messages for declined cards
  - Payment captured only on order submission (not on card entry)
  - Refunds processable from admin panel

#### FR-PAY-02: PayPal

- **Description:** PayPal as an alternative payment method.
- **User value:** Preferred by some educators; provides buyer protection perception.
- **Acceptance criteria:**
  - PayPal button displayed alongside credit card form
  - Redirects to PayPal for authentication, returns to order confirmation
  - Supports PayPal balance, linked bank account, and PayPal Credit
  - Order created in our system upon PayPal payment completion callback

#### FR-PAY-03: Purchase Orders (Schools/Districts)

- **Description:** Purchase order payment method for institutional buyers, enabling Net 30/60 invoicing.
- **User value:** This is the primary purchasing mechanism for schools and districts — without it, institutional sales are blocked.
- **Acceptance criteria:**
  - "Pay by Purchase Order" option at checkout
  - PO number field (required) and PO document upload (PDF, required)
  - Order status set to "Pending PO Review" on submission
  - Admin interface for staff to review, approve, or reject PO orders
  - On approval: invoice generated and emailed to buyer with Net 30 terms (configurable)
  - Payment status tracked separately from order fulfillment status
  - Overdue PO payments flagged in admin dashboard

---

### 6.5 Order Management

#### FR-ORD-01: Order Status Tracking

- **Description:** Customers can view the status of their orders; statuses update as orders are processed and shipped.
- **User value:** Eliminates "Where's my order?" phone calls; critical for educators planning lessons around material arrival.
- **Acceptance criteria:**
  - Order statuses: Received → Processing → Shipped → Delivered (physical); Received → Complete (digital)
  - PO orders add: Pending PO Review → PO Approved before Processing
  - Status viewable via account dashboard (logged-in) or email link (guest)
  - Each status change triggers an email notification
  - Shipped status includes tracking number and carrier link

#### FR-ORD-02: Email Notifications

- **Description:** Transactional emails at key order lifecycle points.
- **User value:** Keeps customers informed without requiring them to check the website.
- **Acceptance criteria:**
  - Emails triggered for: order confirmation, PO approved/rejected, order shipped (with tracking), order delivered, digital download ready
  - Emails branded with Upstream Literacy identity
  - Emails include order summary and link to order detail page
  - Unsubscribe not required for transactional emails (CAN-SPAM compliant)
  - Email delivery monitored (bounce rate, delivery rate)

#### FR-ORD-03: Digital Product Delivery

- **Description:** Immediate access to downloadable products upon purchase completion.
- **User value:** Instant gratification; no shipping wait for digital materials.
- **Acceptance criteria:**
  - Download links included in confirmation email and order detail page
  - Links are time-limited and access-controlled (signed URLs, valid for 7 days, re-generable from account)
  - Download count tracked per order (for license enforcement if needed)
  - File hosting on CDN for fast downloads
  - Supported formats: PDF (primary), ZIP for multi-file products

---

### 6.6 Inventory Management

#### FR-INV-01: Stock Tracking

- **Description:** Real-time inventory counts for physical products; stock decremented on order placement.
- **User value:** Prevents overselling; accurate availability information.
- **Acceptance criteria:**
  - Each physical product SKU has a stock count in the system
  - Stock decremented when order is placed (not when added to cart)
  - Low-stock threshold configurable per product (triggers admin alert)
  - Out-of-stock products display "Out of Stock" badge and disable purchase
  - Admin interface for manual stock adjustments with audit log

#### FR-INV-02: Digital vs. Physical Differentiation

- **Description:** System distinguishes between physical products (shipped, stock-tracked) and digital products (downloadable, unlimited stock).
- **User value:** Appropriate fulfillment flow per product type.
- **Acceptance criteria:**
  - Product type flag: physical, digital, or bundle (mixed)
  - Digital products always show "In Stock" (unlimited)
  - Mixed carts handled correctly: digital items delivered immediately, physical items follow shipping flow
  - Shipping calculated only on physical items
  - Admin can set product type on creation/edit

#### FR-INV-03: Backorder Support

- **Description:** Allow orders for out-of-stock items with extended fulfillment timeline.
- **User value:** Schools planning purchases months ahead can place orders even for temporarily unavailable items.
- **Acceptance criteria:**
  - Configurable per product: allow backorder yes/no
  - Backorderable products show "Available for Backorder — Ships by [date]"
  - Backorder items clearly labeled in cart and order confirmation
  - Admin can set estimated restock date per product

---

### 6.7 Customer Accounts

#### FR-ACCT-01: Registration & Authentication

- **Description:** Account creation and login system.
- **User value:** Enables saved information, order history, and streamlined reordering.
- **Acceptance criteria:**
  - Registration: email + password (minimum 8 characters, 1 number, 1 special character)
  - Email verification required before first login
  - Login via email + password
  - Password reset via email link
  - Session timeout after 30 days of inactivity
  - Optional: social login (Google) in Phase 2

#### FR-ACCT-02: Account Profile & Institution

- **Description:** User profile with personal info and optional institutional affiliation.
- **User value:** Saved info speeds up checkout; institutional affiliation enables tax-exempt purchasing and school-specific features.
- **Acceptance criteria:**
  - Profile fields: name, email, phone (optional), role (teacher, admin, parent, other)
  - Institution fields: school/district name, address, tax-exempt status, exemption certificate
  - Multiple saved shipping addresses (labeled: "Home," "School," etc.)
  - Profile editable from account dashboard

#### FR-ACCT-03: Order History & Reordering

- **Description:** View past orders and reorder with one click.
- **User value:** Teachers who reorder the same materials each year save significant time.
- **Acceptance criteria:**
  - Order history displays: order number, date, status, total, item summary
  - Sortable and filterable by date, status
  - "View Details" shows full order with line items, tracking, and payment info
  - "Reorder" button adds all items from a past order to the current cart
  - If any reorder item is out of stock, user is notified and item is excluded (with option to backorder if available)

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Metric | Target | Rationale |
|--------|--------|-----------|
| Page load time (product pages) | < 2 seconds (LCP) | Education users often on school networks with moderate bandwidth |
| Add-to-cart response | < 500ms | Instant feedback critical for UX confidence |
| Checkout page load | < 1.5 seconds | Abandonment increases 7% per second of delay |
| Search results | < 1 second | Educator time is limited; fast results keep engagement |
| API response time (95th percentile) | < 300ms | Snappy UI depends on fast backend |

### 7.2 Security

- **PCI DSS compliance:** No raw card data stored or transmitted through our servers; use Stripe Elements or equivalent hosted fields
- **HTTPS everywhere:** TLS 1.2+ on all pages; HSTS header enforced
- **Authentication:** Passwords hashed with bcrypt (cost factor 12+); rate-limiting on login attempts
- **Data protection:** Customer PII encrypted at rest; database access restricted to application service accounts
- **Admin access:** Role-based access control; admin actions logged in audit trail
- **Dependency security:** Automated vulnerability scanning on dependencies (Dependabot or equivalent)

### 7.3 Accessibility

- **Standard:** WCAG 2.1 AA compliance across all customer-facing pages
- **Keyboard navigation:** All interactive elements operable via keyboard; visible focus indicators
- **Screen reader support:** Semantic HTML; ARIA labels on dynamic components (cart updates, modals)
- **Color contrast:** Minimum 4.5:1 for normal text, 3:1 for large text
- **Form accessibility:** Labels associated with inputs; error messages programmatically linked to fields
- **Testing:** Automated accessibility testing in CI (axe-core); manual testing with screen reader before launch

### 7.4 Scalability

- **Normal load:** Support 500 concurrent users with no degradation
- **Peak load (back-to-school):** Support 2,000 concurrent users (3-5x normal) during July-September purchasing season
- **Database:** Indexed queries on product catalog, orders, and user accounts; query performance monitored
- **Static assets:** Served via CDN (CloudFront, Cloudflare, or equivalent)
- **Horizontal scaling:** Application server stateless; session data in Redis or database; can add instances behind load balancer

### 7.5 Reliability

- **Uptime target:** 99.5% (allows ~44 hours downtime/year; appropriate for early stage)
- **Checkout availability:** 99.9% during business hours (checkout is revenue-critical)
- **Backup:** Daily automated database backups; 30-day retention; tested restore procedure
- **Error handling:** Graceful degradation on payment provider outage (display message, don't break); retry logic on transient failures
- **Monitoring:** Application error tracking (Sentry or equivalent); uptime monitoring with alerting

---

## 8. Data & Analytics

### 8.1 Event Tracking

All events should be tracked with a consistent schema and sent to an analytics platform (e.g., Mixpanel, Amplitude, or a self-hosted solution via PostHog).

| Event Name | Trigger | Key Properties |
|-----------|---------|----------------|
| `product_viewed` | Product detail page loaded | product_id, product_name, category, price, source (search, category, direct) |
| `product_searched` | Search submitted | query, results_count, page_number |
| `added_to_cart` | Item added to cart | product_id, product_name, quantity, price, cart_total |
| `removed_from_cart` | Item removed from cart | product_id, product_name, quantity, cart_total |
| `cart_viewed` | Cart page/overlay opened | item_count, cart_total |
| `checkout_started` | Checkout page loaded | item_count, cart_total, is_guest |
| `checkout_step_completed` | Each checkout step completed | step_name (email, shipping, payment, review), time_on_step |
| `payment_method_selected` | Payment method chosen | method (card, paypal, purchase_order) |
| `checkout_completed` | Order successfully placed | order_id, order_total, item_count, payment_method, is_guest, is_tax_exempt |
| `checkout_failed` | Payment or submission failed | error_type, payment_method, cart_total |
| `account_created` | New account registered | source (checkout, standalone), role |
| `reorder_initiated` | "Reorder" clicked on past order | original_order_id, item_count |

### 8.2 Funnel Tracking

**Primary conversion funnel:**
```
Product Viewed → Added to Cart → Checkout Started → Checkout Completed
```

**Secondary funnels:**
```
Search → Product Viewed → Added to Cart (search effectiveness)
Category Browse → Product Viewed → Added to Cart (browse effectiveness)
Cart Viewed → Checkout Started (cart-to-checkout intent)
```

### 8.3 Cart Abandonment Tracking

- **Definition:** Cart abandoned = items in cart + checkout_started but no checkout_completed within 24 hours
- **Segmentation:** By user type (guest vs. registered), payment method attempted, cart value, number of items
- **Alerting:** Weekly report on abandonment rate and top abandoned products
- **Future (Phase 2):** Abandoned cart email recovery (requires email capture at checkout start)

### 8.4 Dashboard Requirements

**Operational Dashboard (Staff):**
- Orders today / this week / this month (count and revenue)
- Orders pending fulfillment
- PO orders pending approval
- Low-stock product alerts
- Payment failures (last 7 days)

**Analytics Dashboard (Leadership):**
- Conversion funnel visualization with drop-off rates
- Revenue trend (daily, weekly, monthly)
- Average order value trend
- Top products by revenue and unit sales
- Customer acquisition (new vs. returning)
- Cart abandonment rate trend
- Payment method distribution

---

## 9. Technical Considerations

### 9.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Frontend (SPA)                       │
│              React + TypeScript + Tailwind               │
│    Product pages, Cart, Checkout, Account Dashboard      │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JSON)
                       │
┌──────────────────────┴──────────────────────────────────┐
│                   Backend (API Server)                    │
│                  Django + Django REST Framework           │
│                                                          │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Catalog  │ │   Cart   │ │ Checkout │ │   Orders    │ │
│  │ Service  │ │ Service  │ │ Service  │ │  Service    │ │
│  └─────────┘ └──────────┘ └──────────┘ └─────────────┘ │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │Inventory│ │ Accounts │ │ Payment  │ │  Analytics  │ │
│  │ Service  │ │ Service  │ │ Service  │ │  Service    │ │
│  └─────────┘ └──────────┘ └──────────┘ └─────────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┼────────────────┐
          │            │                │
   ┌──────┴──────┐ ┌──┴───┐ ┌─────────┴────────┐
   │ PostgreSQL  │ │Redis │ │ File Storage     │
   │ (Primary DB)│ │Cache │ │ (S3 / CDN)       │
   └─────────────┘ └──────┘ └──────────────────┘
```

### 9.2 Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | React 18 + TypeScript | Component reusability; strong ecosystem; TypeScript for type safety |
| **Styling** | Tailwind CSS | Rapid UI development; consistent design system; excellent accessibility utilities |
| **Backend** | Django 5 + Django REST Framework | Batteries-included (admin, auth, ORM); mature ecosystem; strong security defaults |
| **Database** | PostgreSQL 16 | Reliable, performant; full-text search built-in; JSON support for flexible product metadata |
| **Cache** | Redis | Session storage, cart persistence for guests, page caching |
| **Task Queue** | Celery + Redis | Async email sending, PO notification processing, analytics event batching |
| **File Storage** | AWS S3 (or compatible) | Digital product hosting, product images, PO document uploads |
| **CDN** | CloudFront or Cloudflare | Static assets and media delivery |
| **Search** | PostgreSQL full-text search (MVP); Elasticsearch (Phase 2) | Start simple; upgrade if search complexity grows |

### 9.3 Integration Points

| Integration | Provider Options | Purpose |
|------------|-----------------|---------|
| **Payment processing** | Stripe (test/sandbox mode for demo; production keys at launch) | Card payments, PayPal (via Stripe), refunds, PCI compliance via hosted fields |
| **Email (transactional)** | SendGrid or Amazon SES | Order confirmations, shipping notifications, password resets |
| **Email (marketing)** | Mailchimp or ConvertKit (Phase 2) | Abandoned cart recovery, product announcements |
| **Tax calculation** | TaxJar or manual state-rate table (MVP) | Sales tax by destination; exemption management |
| **Address validation** | USPS Web Tools API (free) or SmartyStreets | Shipping address verification |
| **Shipping rates** | Flat-rate table (confirmed for MVP); EasyPost or ShipStation (Phase 2) | Flat-rate shipping; no rate-shopping API needed initially |
| **Analytics** | PostHog (self-hosted, free) or Mixpanel | Event tracking, funnel analysis, dashboards |
| **Error monitoring** | Sentry | Application error tracking and alerting |
| **File storage** | AWS S3 | Product images, digital downloads, PO documents |

### 9.4 API Design Principles

- **RESTful:** Resource-oriented URLs (`/api/v1/products/`, `/api/v1/cart/`, `/api/v1/orders/`)
- **Versioned:** URL-based versioning (`/api/v1/`) for future backward compatibility
- **Authenticated:** JWT tokens for API authentication; session-based for web app
- **Paginated:** Cursor-based pagination on list endpoints
- **Filterable:** Query parameter-based filtering on catalog endpoints (`?grade=2&category=phonics`)
- **CORS:** Configured for frontend domain(s) only

### 9.5 Future Extensibility

- **Subscriptions:** Data model should support recurring orders (subscription SKUs, billing cycles) even if not implemented at MVP
- **Digital delivery platform:** Architecture supports expanding from downloadable PDFs to a full digital content platform (interactive exercises, streaming)
- **Multi-currency / international:** Not in scope for MVP, but avoid hardcoding USD assumptions in the data model
- **API-first:** Third-party integrations (school LMS platforms, library systems) can consume the same API
- **URL structure:** Shop lives at upstreamliteracy.org/shop; frontend routes: `/shop`, `/shop/category/:slug`, `/shop/product/:slug`, `/shop/cart`, `/shop/checkout`, `/shop/account`

---

## 10. Risks & Mitigations

### 10.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Payment processing failures | Medium | High | Use Stripe (99.999% uptime SLA); implement retry logic; display clear user-facing errors; monitor failure rate |
| Scaling under back-to-school load | Low (MVP) | High | Stateless app design; load testing before first August; CDN for static assets; database connection pooling |
| Inventory sync errors (overselling) | Medium | Medium | Database-level stock decrement (atomic operation); reconciliation job daily; admin alerts on discrepancies |
| Security breach / data leak | Low | Critical | PCI compliance via Stripe (no card data on our servers); encrypted PII; regular dependency updates; penetration testing before launch |

### 10.2 Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Low adoption (customers continue calling) | Medium | High | Communicate new ordering option to existing customers; offer first-order incentive; make online ordering significantly easier than phone |
| Pricing mismatch with market | Medium | Medium | Research competitor pricing before launch; support flexible pricing (bulk discounts, bundles); A/B test pricing in Phase 2 |
| PO workflow too complex for small team | Medium | Medium | Start with manual PO review in admin panel; automate approval for trusted accounts in Phase 2 |
| Cart abandonment higher than expected | High | Medium | Implement guest checkout (reduces friction); clear pricing upfront (no surprise shipping costs); Phase 2: abandoned cart email recovery |

### 10.3 Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Order fulfillment delays | Medium | Medium | Order management dashboard with clear queue; email customers proactively on delays |
| Inventory data accuracy | High (early) | Medium | Initial full inventory audit before launch; regular reconciliation; admin audit log for stock changes |
| Staff overwhelmed with PO approvals | Low (initially) | Low | Simple admin workflow; batch approval interface; auto-approve for repeat institutional buyers (Phase 2) |
| Tax compliance errors | Medium | Medium | Use TaxJar or equivalent for rate accuracy; exempt certificate review process; quarterly compliance check |

---

## 11. Phased Rollout Plan

### Phase 1: MVP (Core Commerce) — Target: 8-10 weeks

**Goal:** Replace phone/email ordering with a functional online store at upstreamliteracy.org/shop.

**Catalog:** ~20 products (physical + digital); product content (photos, descriptions, metadata) to be created during this phase.

**Demo strategy:** All third-party services run in sandbox/test mode (Stripe test keys, console email backend). Seed data provided for demo purposes. Admin panel designed for non-technical single-operator workflow.

**Scope:**
- Product catalog with categories, search, and detail pages (~20 products)
- Shopping cart (add, remove, quantity adjust, persistence)
- Guest and registered checkout
- Credit card payments via Stripe (test mode for demo)
- Flat-rate shipping (configurable in admin)
- Digital product delivery (signed download URLs for purchased digital items)
- Order confirmation emails (console backend for demo; SendGrid for production)
- Basic order status tracking (admin-updated)
- Inventory management (stock tracking, out-of-stock handling; digital = unlimited stock)
- Customer account registration with order history
- Admin panel for product, order, and inventory management (Django admin customized)
- Basic analytics event tracking (product viewed, added to cart, checkout completed)
- Seed data: sample products with placeholder images and descriptions for demo

**Not in MVP scope:** PayPal, purchase orders, bulk/volume discounts, reviews, save-for-later, reorder flow, abandoned cart emails, advanced analytics dashboards

---

### Phase 2: Growth (Accounts, Analytics, School Workflows) — Target: 6-8 weeks after MVP

**Goal:** Enable institutional purchasing and optimize conversion.

**Scope:**
- Purchase order payment method (PO upload, approval workflow, invoicing)
- Tax-exempt purchasing (certificate upload, account-level flag)
- PayPal integration
- Save-for-later functionality
- One-click reorder from order history
- Product reviews and ratings
- Abandoned cart email recovery
- Full analytics dashboards (conversion funnel, revenue, abandonment)
- Address validation (USPS API)
- Bulk ordering improvements (quantity pricing tiers)
- Google social login
- Email marketing integration (Mailchimp/ConvertKit)

---

### Phase 3: Optimization (Personalization & Advanced Features) — Target: 8-12 weeks after Phase 2

**Goal:** Increase average order value, lifetime value, and operational efficiency.

**Scope:**
- AI-powered product recommendations ("Educators also bought...", "Recommended for Grade 2 Phonics")
- Personalized browsing based on account profile (grade level, school type)
- Advanced search (Elasticsearch, faceted filtering, autocomplete)
- Subscription/auto-reorder for consumable materials
- Multi-ship-to ordering (single PO, multiple school addresses)
- Shipping integration (EasyPost or ShipStation for rate shopping and label generation)
- Customer segmentation and targeted promotions
- Wishlist / school supply lists (shareable with parents)
- API documentation for potential LMS integrations
- Performance optimization (server-side rendering, image optimization, lazy loading)

---

## Appendix A: Glossary

| Term | Definition |
|------|-----------|
| **Decodable reader** | A text written with controlled phonics patterns to support early reading instruction |
| **Purchase order (PO)** | A formal document from a school/district authorizing a purchase; payment follows after delivery (Net 30/60) |
| **Tax-exempt** | Schools and districts are exempt from sales tax in most states; requires valid exemption certificate |
| **Science of reading** | Evidence-based approach to reading instruction emphasizing phonemic awareness, phonics, fluency, vocabulary, and comprehension |
| **SKU** | Stock Keeping Unit; unique identifier for each product variant |
| **LCP** | Largest Contentful Paint; Core Web Vital measuring perceived page load speed |

---

## Appendix B: Stakeholder Decisions (Resolved)

| # | Question | Decision | Implications |
|---|----------|----------|-------------|
| 1 | **Product catalog size** | ~20 products at launch | Simple catalog; PostgreSQL full-text search sufficient; no need for Elasticsearch at MVP; manageable data entry |
| 2 | **Digital products at MVP** | Yes — digital downloads ready at launch | Digital delivery (signed S3 URLs) required in MVP scope; mixed cart handling (digital + physical) needed from day one |
| 3 | **Shipping strategy** | Flat rate | Simple flat-rate shipping table (configurable in admin); no shipping API integration needed at MVP |
| 4 | **Pricing structure** | No bulk/volume discounts | Single price per product; no discount engine needed at MVP; simplifies cart and checkout logic |
| 5 | **Legal entity status** | Not a 501(c)(3) nonprofit | Standard Stripe processing fees (2.9% + $0.30); no nonprofit rate available; standard business entity |
| 6 | **Existing customer database** | No existing customer list | No migration needed; all customers are new; focus on acquisition UX rather than migration tooling |
| 7 | **Content readiness** | Product content not yet prepared | Product photos, descriptions, and metadata need to be created; admin panel must support easy content entry; consider placeholder/seed data for demo |
| 8 | **Staffing for operations** | To be determined for demo | Admin panel should be intuitive for non-technical staff; design for single-operator workflow; demo will use simulated fulfillment |
| 9 | **Third-party service budget** | Sandbox/test mode for demo | Use Stripe test mode, free-tier email services, and local/dev hosting for demo; no production costs until launch decision |
| 10 | **Domain** | upstreamliteracy.org/shop | Shop is a section of the main site (not a subdomain); frontend routing handles /shop/* paths; shared navigation with main site |
