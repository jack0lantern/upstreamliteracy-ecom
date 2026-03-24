import { Link, NavLink } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { SearchBar } from '@/components/search/SearchBar';
import { CartIconBadge } from '@/components/layout/CartIconBadge';

const navLinks = [
  { label: 'Shop', to: '/shop' },
];

export function Header() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white shadow-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link
          to="/shop"
          className="flex flex-shrink-0 items-center gap-2 text-upstream-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-upstream-500 focus-visible:ring-offset-2"
          aria-label="Upstream Literacy home"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-8 w-8"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M11.47 3.84a.75.75 0 0 1 1.06 0l8.69 8.69a.75.75 0 1 0 1.06-1.06l-8.689-8.69a2.25 2.25 0 0 0-3.182 0l-8.69 8.69a.75.75 0 1 0 1.061 1.06l8.69-8.69Z" />
            <path d="m12 5.432 8.159 8.159c.03.03.06.058.091.086v6.198c0 1.035-.84 1.875-1.875 1.875H15a.75.75 0 0 1-.75-.75v-4.5a.75.75 0 0 0-.75-.75h-3a.75.75 0 0 0-.75.75V21a.75.75 0 0 1-.75.75H5.625a1.875 1.875 0 0 1-1.875-1.875v-6.198a2.29 2.29 0 0 0 .091-.086L12 5.432Z" />
          </svg>
          <span className="hidden text-lg font-bold tracking-tight sm:block">
            Upstream Literacy
          </span>
        </Link>

        {/* Navigation */}
        <nav aria-label="Main navigation" className="hidden md:flex md:items-center md:gap-6">
          {navLinks.map(({ label, to }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${
                  isActive
                    ? 'text-upstream-700'
                    : 'text-gray-600 hover:text-gray-900'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Search + Actions */}
        <div className="flex flex-1 items-center justify-end gap-3">
          <div className="hidden sm:block">
            <SearchBar />
          </div>

          <CartIconBadge />

          {user ? (
            <NavLink
              to="/shop/account"
              className={({ isActive }) =>
                `inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-upstream-50 text-upstream-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 24 24"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M7.5 6a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0ZM3.751 20.105a8.25 8.25 0 0 1 16.498 0 .75.75 0 0 1-.437.695A18.683 18.683 0 0 1 12 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 0 1-.437-.695Z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="hidden sm:inline">
                {user.first_name || 'Account'}
              </span>
            </NavLink>
          ) : (
            <NavLink
              to="/login"
              className="btn-primary py-1.5 text-sm"
            >
              Sign in
            </NavLink>
          )}
        </div>
      </div>

      {/* Mobile search row */}
      <div className="border-t border-gray-100 px-4 py-2 sm:hidden">
        <SearchBar />
      </div>
    </header>
  );
}

export default Header;
