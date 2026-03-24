import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { Footer } from './Footer';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { CartSidebar } from '@/components/cart/CartSidebar';

export function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main id="main-content" className="flex-1">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
      <Footer />
      <CartSidebar />
    </div>
  );
}

export default Layout;
