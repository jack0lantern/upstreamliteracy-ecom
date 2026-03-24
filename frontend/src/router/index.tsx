import { type ReactNode, lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate, useParams } from 'react-router-dom';
import { RequireAuth, RequireCart } from './guards';
import Layout from '@/components/layout/Layout';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

const ShopPage = lazy(() => import('@/pages/ShopPage'));
const ProductDetailPage = lazy(() => import('@/pages/ProductDetailPage'));
const CartPage = lazy(() => import('@/pages/CartPage'));
const CheckoutLayout = lazy(() => import('@/pages/CheckoutLayout'));
const OrderConfirmationPage = lazy(() => import('@/pages/OrderConfirmationPage'));
const SearchResultsPage = lazy(() => import('@/pages/SearchResultsPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('@/pages/ForgotPasswordPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));
const AccountLayout = lazy(() => import('@/pages/account/AccountLayout'));
const ProfilePage = lazy(() => import('@/pages/account/ProfilePage'));
const OrderHistoryPage = lazy(() => import('@/pages/account/OrderHistoryPage'));

/**
 * Redirect old /shop/category/:slug URLs to /shop with the appropriate filter param.
 * Tries to guess the param key from well-known slugs; falls back to a generic redirect.
 */
const SLUG_TO_PARAM: Record<string, string> = {
  // Grade slugs
  'pre-k': 'grade',
  kindergarten: 'grade',
  'grade-1': 'grade',
  'grade-2': 'grade',
  'grade-3': 'grade',
  'grade-4': 'grade',
  'grade-5': 'grade',
  // Focus slugs
  phonics: 'focus',
  'phonemic-awareness': 'focus',
  fluency: 'focus',
  vocabulary: 'focus',
  comprehension: 'focus',
  // Format slugs
  'decodable-readers': 'format',
  'teacher-guides': 'format',
  'student-workbooks': 'format',
  'kits-bundles': 'format',
  'digital-downloads': 'format',
};

function CategoryRedirect() {
  const { slug } = useParams<{ slug: string }>();
  const paramKey = slug ? SLUG_TO_PARAM[slug] : undefined;
  const to = paramKey && slug ? `/shop?${paramKey}=${slug}` : '/shop';
  return <Navigate to={to} replace />;
}

function PageLoader() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12">
      <LoadingSkeleton lines={6} />
    </div>
  );
}

function withSuspense(element: ReactNode) {
  return <Suspense fallback={<PageLoader />}>{element}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/shop" replace /> },

      {
        path: 'shop',
        element: withSuspense(<ShopPage />),
      },
      {
        path: 'shop/category/:slug',
        element: <CategoryRedirect />,
      },
      {
        path: 'shop/product/:slug',
        element: withSuspense(<ProductDetailPage />),
      },
      {
        path: 'shop/cart',
        element: withSuspense(<CartPage />),
      },
      {
        path: 'shop/checkout',
        element: withSuspense(
          <RequireCart>
            <CheckoutLayout />
          </RequireCart>,
        ),
      },
      {
        path: 'shop/checkout/success',
        element: withSuspense(<OrderConfirmationPage />),
      },
      {
        path: 'shop/account',
        element: withSuspense(
          <RequireAuth>
            <AccountLayout />
          </RequireAuth>,
        ),
        children: [
          { index: true, element: <Navigate to="profile" replace /> },
          { path: 'profile', element: withSuspense(<ProfilePage />) },
          { path: 'orders', element: withSuspense(<OrderHistoryPage />) },
        ],
      },
      {
        path: 'shop/search',
        element: withSuspense(<SearchResultsPage />),
      },
    ],
  },
  {
    path: '/login',
    element: withSuspense(<LoginPage />),
  },
  {
    path: '/register',
    element: withSuspense(<RegisterPage />),
  },
  {
    path: '/forgot-password',
    element: withSuspense(<ForgotPasswordPage />),
  },
  {
    path: '*',
    element: (
      <Layout />
    ),
    children: [
      { path: '*', element: withSuspense(<NotFoundPage />) },
    ],
  },
]);
