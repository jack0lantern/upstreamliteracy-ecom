import { type ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useQuery } from '@tanstack/react-query';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';

interface Props {
  children: ReactNode;
}

export function RequireAuth({ children }: Props) {
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  if (!user) {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />;
  }

  return <>{children}</>;
}

export function RequireCart({ children }: Props) {
  const { data: cart, isLoading } = useQuery({
    queryKey: queryKeys.cart.current(),
    queryFn: cartApi.getCart,
    retry: false,
    staleTime: 1000 * 60,
  });

  if (isLoading) {
    return null;
  }

  if (!cart || cart.item_count === 0) {
    return <Navigate to="/shop/cart" replace />;
  }

  return <>{children}</>;
}
