Bugs & Unexpected Behaviors Found
🔴 Critical
BUG-1: "Add to Cart" broken for ALL products — variant selector missing
Every product page shows a "Please select a variant." error when you click Add to Cart, but no variant selection UI exists anywhere on the page. There's no dropdown, radio button, or any other selector rendered. Users cannot add any product to the cart.

Affects: all 21 products, both Physical and Digital types
Route: /shop/product/*

BUG-2: Search result count always shows "0 results" even when results exist
Searching "phonics" returns a visible list of phonics products, but the count reads "0 results". The counter is decoupled from the rendered list — one of them is using wrong/stale data.

Route: /shop/search?q=phonics

BUG-3: Forgot Password route throws a raw 404 error
Clicking "Forgot password?" navigates to /forgot-password, which has no registered route and crashes to the bare React Router error page. The link exists on both the Login and Sign In pages.

Route: /forgot-password


🟠 Major
BUG-4: Parent category pages show "(0)" subcategory counts despite products existing
All three parent categories (By Grade, By Focus, By Format) display subcategory pills with "(0)" counts and show "No products in this category yet." The child categories have products — Grade 1 has 10, Phonics has 15, Grade 5 has 2, etc. The parent page is failing to aggregate or inherit counts from its children.

Routes: /shop/category/by-grade, /shop/category/by-focus, /shop/category/by-format

BUG-5: Unknown routes and some auth routes throw a raw React Router dev error page
Navigating to a completely unknown path (e.g. /totally-non-existent) shows the raw React Router "Unexpected Application Error! 404 Not Found" developer page. No errorElement or ErrorBoundary is configured. This exposes internal framework details to users.

Example routes: /totally-non-existent, /forgot-password

BUG-6: Long search query breaks page layout
A search query longer than ~100 characters causes the "Results for..." heading to overflow horizontally beyond the viewport, pushing the entire page layout sideways and creating a horizontal scrollbar. The header shifts out of frame.

Route: /shop/search?q=<very-long-string>


🟡 Minor / UX
BUG-7: Shop index page category sidebar counts show "0" for all parent categories
On the shop home page, "By Grade", "By Focus", and "By Format" all show "0" next to them in the sidebar. This is misleading — users think there are no products organized by grade/focus/format.
BUG-8: Non-existent category slug shows generic "Category" page instead of 404
Navigating to an invalid category slug (e.g. /shop/category/nonexistent-category) renders a page titled "Category" with breadcrumb "Category" and the message "No products in this category yet." It should either 404 or show a "Category not found" message.
BUG-9: Password validation only reports one error at a time
On the registration form, submitting a password that fails multiple rules (e.g. missing uppercase AND number AND special character) only shows the first failure. All unmet rules should be displayed simultaneously.
BUG-10: All product images are broken (placeholder only)
Every product on every page shows only the image placeholder icon. No product images are loading. This may be an environment/data issue, but it affects the entire shop.
BUG-11: Intermittent redirect to /login when clicking category links
Observed once during testing: clicking "By Grade" from the shop sidebar redirected to login. Subsequent attempts worked correctly. Likely a race condition or session/state issue during the brief period after a session expires mid-session.

End-to-End Test Suite
Here is the recommended suite organized by area:

Authentication
AUTH-01: Login - valid credentials
  Given a registered user
  When they enter correct email and password and submit
  Then they are redirected to /shop (or the ?next= path) and the nav shows their name

AUTH-02: Login - invalid credentials
  When incorrect email/password is submitted
  Then an "Invalid email or password" error appears and the user stays on the login page

AUTH-03: Login - invalid email format
  When a non-email string is entered in the email field and submitted
  Then "Enter a valid email address" appears inline and the form is not submitted

AUTH-04: Login - empty form submission
  When the form is submitted with blank fields
  Then field-level validation errors appear and no network request is sent

AUTH-05: Login - ?next= redirect preserved
  When an unauthenticated user tries to visit /shop/account and is redirected to login
  Then after successful login they are sent to /shop/account, not to /shop

AUTH-06: Register - successful account creation
  Given a unique email
  When all fields are filled validly and submitted
  Then the account is created and the user is redirected to the shop (or confirmation)

AUTH-07: Register - duplicate email
  When a registered email is used to sign up
  Then a "email already in use" error is shown

AUTH-08: Register - mismatched passwords
  When the password and confirm password fields differ
  Then "Passwords do not match" error appears on the confirm field

AUTH-09: Register - weak password shows ALL failing rules simultaneously
  When a password is submitted that fails multiple requirements
  Then ALL unmet requirements are displayed at once (not just the first one)

AUTH-10: Register - empty form
  When submitted empty
  Then all required fields show inline validation errors

AUTH-11: Forgot password route exists and is functional
  When the "Forgot password?" link is clicked
  Then a real forgot-password page loads (not a 404)

AUTH-12: Logout clears session and shows Sign In button
  Given a logged-in user
  When they log out
  Then the nav shows "Sign in" and protected routes redirect to login

Shop / Product Listing
SHOP-01: Shop home page loads with all 21 products
  When /shop is visited
  Then 21 product cards are visible with title and price

SHOP-02: All Products category is the default active filter
  When /shop is visited
  Then the "All Products" sidebar item is highlighted and all products are shown

SHOP-03: Category sidebar - parent categories show correct product counts
  When /shop is visited
  Then "By Grade", "By Focus", "By Format" each show a non-zero product count

SHOP-04: Category sidebar - clicking a parent category navigates to category page
  When "By Grade" is clicked in the sidebar
  Then /shop/category/by-grade loads with subcategory filter pills

SHOP-05: Parent category page - subcategory pills show correct counts
  When /shop/category/by-grade is visited
  Then each grade pill shows the actual number of products it contains

SHOP-06: Parent category page - clicking a subcategory pill filters correctly
  When "Grade 1 (10)" is clicked on /shop/category/by-grade
  Then only Grade 1 products are shown (10 products)

SHOP-07: Direct subcategory URL shows correct products
  When /shop/category/grade-1 is visited directly
  Then 10 Grade 1 products are displayed

SHOP-08: Non-existent category slug shows a "Category not found" page
  When /shop/category/this-does-not-exist is visited
  Then a user-friendly "Category not found" message appears (not a blank "No products" state)

Search
SEARCH-01: Search with matching term returns correct results and count
  When "phonics" is entered and submitted
  Then only phonics-related products appear AND the result count matches the number displayed

SEARCH-02: Search with no matches shows empty state
  When a nonsense query is submitted
  Then "No results found" empty state shows with "Browse All Products" CTA

SEARCH-03: Search with empty query shows prompt
  When /shop/search?q= is visited
  Then "Enter a search term to find products." is shown

SEARCH-04: Search result count is accurate
  Given any search term that returns N products
  Then the "X results" counter exactly matches the number of product cards rendered

SEARCH-05: XSS / special characters are escaped in search output
  When <script>alert('xss')</script> is searched
  Then the input is rendered as escaped text and no script executes

SEARCH-06: Long search query does not break page layout
  When a 300+ character string is searched
  Then the page layout stays intact (no horizontal overflow), the query is truncated in the heading

Product Detail Page
PRODUCT-01: Product page loads with title, price, and description
  When a valid product slug is visited
  Then the product name, price, description, quantity control, and Add to Cart button are all visible

PRODUCT-02: Variant selector is visible when a product has variants
  Given a product with variants (e.g. physical/digital)
  Then a variant selector (dropdown, radio, etc.) is rendered before the Add to Cart button

PRODUCT-03: Add to Cart works when no variant is required (single-variant products)
  Given a product with only one variant
  When Add to Cart is clicked at quantity 1
  Then the item is added to cart without a "select a variant" error

PRODUCT-04: Add to Cart works when a variant is selected
  Given a multi-variant product with variant selector visible
  When the user selects a variant and clicks Add to Cart
  Then the correct variant is added to cart

PRODUCT-05: Add to Cart without selecting variant shows error
  Given a multi-variant product
  When Add to Cart is clicked without selecting a variant
  Then a visible, clear error message appears near the selector (not just a toast)

PRODUCT-06: Quantity decrement is disabled at 1
  When the quantity is 1 and the "-" button is clicked
  Then the quantity stays at 1 (no going to 0 or negative)

PRODUCT-07: Quantity can be increased
  When "+" is clicked 3 times from quantity 1
  Then the quantity becomes 4

PRODUCT-08: Non-existent product slug shows "Product not found" page
  When /shop/product/this-does-not-exist is visited
  Then a "Product not found" page renders with a Back to Shop button

PRODUCT-09: Breadcrumbs are correct and navigable
  When a product page is visited
  Then breadcrumbs show Shop > [Category] > [Product Name] and each link navigates correctly

PRODUCT-10: "You might also like" section renders
  When a product page is scrolled to the bottom
  Then related product cards are visible with image, title, and price

Cart
CART-01: Empty cart shows empty state with Browse Products CTA
  When /shop/cart is visited with no items
  Then "Your cart is empty" and a "Browse Products" button is shown

CART-02: Adding a product increments cart count in header
  Given a product is successfully added to cart
  Then the cart icon in the nav shows the updated item count

CART-03: Cart shows added items with correct name, price, and quantity
  When /shop/cart is visited after adding items
  Then each item row shows product name, unit price, quantity, and subtotal

CART-04: Cart quantity can be adjusted inline
  When the quantity of a cart item is changed to 3
  Then the subtotal for that row updates correctly

CART-05: Removing an item removes it from the cart
  When the remove button is clicked for a cart item
  Then that item disappears from the cart

CART-06: Cart persists across page navigation
  When an item is added to cart and the user navigates to /shop and back to /shop/cart
  Then the item is still in the cart

CART-07: Checkout redirect from empty cart
  When /shop/checkout is visited with an empty cart
  Then the user is redirected to /shop/cart

CART-08: Cart total reflects sum of all items
  Given two items in cart with known prices
  Then the displayed total equals the sum of (unit price × quantity) for each item

Checkout
CHECKOUT-01: Checkout page loads for authenticated user with items in cart
  Given a logged-in user with items in cart
  When /shop/checkout is visited
  Then a checkout form with shipping and payment fields is shown

CHECKOUT-02: Checkout page requires authentication
  Given an unauthenticated user with items in cart
  When /shop/checkout is visited
  Then the user is redirected to login with ?next=/shop/checkout

CHECKOUT-03: Checkout form validation - required fields
  When the checkout form is submitted empty
  Then all required fields show inline validation errors

CHECKOUT-04: Order placed successfully
  Given valid form data and a test payment method
  When the order is submitted
  Then a success/confirmation page is shown with an order number

CHECKOUT-05: Order confirmation appears in My Orders
  After a successful checkout
  When /shop/account/orders is visited
  Then the new order is listed with correct items, total, and status

Routing & Error Handling
ROUTING-01: Unknown routes show a styled 404 page (not the raw React Router error)
  When any unregistered URL is visited
  Then a user-friendly 404 page renders within the app layout (with nav, footer, etc.)

ROUTING-02: All footer links navigate to valid routes
  For each link in the footer (All Products, Cart, Sign In, Create Account, My Orders)
  When clicked
  Then no 404 or application error occurs

ROUTING-03: Forgot password route exists
  When /forgot-password is visited
  Then a functional page renders (not a 404)

ROUTING-04: App handles malformed query parameters gracefully
  When URL params contain encoded special chars (e.g. %00, %3C%3E, etc.)
  Then the app renders without crashing

Responsive / Visual
UI-01: Shop page is usable on mobile (375px)
  When viewed at 375px wide
  Then products are readable, nav is accessible, and no content overflows

UI-02: Product page is usable on mobile
  When a product page is viewed at 375px
  Then the Add to Cart button, price, and description are all visible without scrolling past the fold on most devices

UI-03: All product images load (not broken placeholders)
  When any product card or product page is viewed
  Then real product images are displayed (not the gray placeholder icon)

UI-04: Search result heading truncates long queries
  When a 300+ character query is searched
  Then the "Results for…" heading is truncated with ellipsis and does not overflow the container