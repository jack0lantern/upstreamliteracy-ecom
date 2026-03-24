import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';

export function CartIconBadge() {
  const { data: cart } = useQuery({
    queryKey: queryKeys.cart.current(),
    queryFn: cartApi.getCart,
    staleTime: 1000 * 60,
    retry: false,
  });

  const itemCount = cart?.item_count ?? 0;

  return (
    <Link
      to="/shop/cart"
      aria-label={`Shopping cart${itemCount > 0 ? `, ${itemCount} item${itemCount !== 1 ? 's' : ''}` : ', empty'}`}
      className="relative inline-flex items-center rounded-md p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-upstream-500"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 0 0-3 3h15.75m-12.75-3h11.218c1.121-2.3 2.1-4.684 2.924-7.138a60.114 60.114 0 0 0-16.536-1.84M7.5 14.25 5.106 5.272M6 20.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Zm12.75 0a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0Z"
        />
      </svg>

      {itemCount > 0 && (
        <span
          aria-hidden="true"
          className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-upstream-600 text-xs font-bold text-white"
        >
          {itemCount > 99 ? '99+' : itemCount}
        </span>
      )}
    </Link>
  );
}

export default CartIconBadge;
