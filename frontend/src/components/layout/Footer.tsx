import { Link } from 'react-router-dom';

const currentYear = new Date().getFullYear();

export function Footer() {
  return (
    <footer className="mt-auto border-t border-gray-200 bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {/* Brand */}
          <div>
            <Link to="/shop" className="text-base font-bold text-upstream-700">
              Upstream Literacy
            </Link>
            <p className="mt-2 text-sm text-gray-500">
              Educational materials for critical thinkers.
            </p>
          </div>

          {/* Shop links */}
          <nav aria-label="Shop links">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Shop
            </h3>
            <ul className="space-y-2 text-sm">
              {[
                { label: 'All Products', to: '/shop' },
                { label: 'Cart', to: '/shop/cart' },
              ].map(({ label, to }) => (
                <li key={to}>
                  <Link to={to} className="text-gray-500 transition-colors hover:text-gray-900">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Account links */}
          <nav aria-label="Account links">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-700">
              Account
            </h3>
            <ul className="space-y-2 text-sm">
              {[
                { label: 'Sign In', to: '/login' },
                { label: 'Create Account', to: '/register' },
                { label: 'My Orders', to: '/shop/account/orders' },
              ].map(({ label, to }) => (
                <li key={to}>
                  <Link to={to} className="text-gray-500 transition-colors hover:text-gray-900">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        <div className="mt-8 border-t border-gray-200 pt-6 text-center text-xs text-gray-400">
          &copy; {currentYear} Upstream Literacy. All rights reserved.
        </div>
      </div>
    </footer>
  );
}

export default Footer;
