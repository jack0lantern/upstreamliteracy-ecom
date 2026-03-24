import { type ReactNode, lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { RequireAuth, RequireCart } from './guards';
import Layout from '@/components/layout/Layout';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

const ShopPage = lazy(() => import('@/pages/ShopPage'));
const CategoryPage = lazy(() => import('@/pages/CategoryPage'));
const ProductDetailPage = lazy(() => import('@/pages/ProductDetailPage'));
const CartPage = lazy(() => import('@/pages/CartPage'));
const CheckoutLayout = lazy(() => import('@/pages/CheckoutLayout'));
const OrderConfirmationPage = lazy(() => import('@/pages/OrderConfirmationPage'));
const SearchResultsPage = lazy(() => import('@/pages/SearchResultsPage'));
const LoginPage = lazy(() => import('@/pages/LoginPage'));
const RegisterPage = lazy(() => import('@/pages/RegisterPage'));
const AccountLayout = lazy(() => import('@/pages/account/AccountLayout'));
const ProfilePage = lazy(() => import('@/pages/account/ProfilePage'));
const OrderHistoryPage = lazy(() => import('@/pages/account/OrderHistoryPage'));

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
        element: withSuspense(<CategoryPage />),
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
]);
