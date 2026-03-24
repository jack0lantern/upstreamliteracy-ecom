import { useState } from 'react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { useQuery, keepPreviousData } from '@tanstack/react-query';
import { ordersApi } from '@/lib/api/orders';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import { OrderStatus, type OrderSummary } from '@/types';

const STATUS_COLORS: Record<OrderStatus, string> = {
  [OrderStatus.PENDING]: 'bg-yellow-100 text-yellow-700',
  [OrderStatus.CONFIRMED]: 'bg-blue-100 text-blue-700',
  [OrderStatus.PROCESSING]: 'bg-blue-100 text-blue-700',
  [OrderStatus.SHIPPED]: 'bg-purple-100 text-purple-700',
  [OrderStatus.DELIVERED]: 'bg-green-100 text-green-700',
  [OrderStatus.CANCELLED]: 'bg-red-100 text-red-600',
  [OrderStatus.REFUNDED]: 'bg-gray-100 text-gray-600',
};

const STATUS_LABEL: Record<OrderStatus, string> = {
  [OrderStatus.PENDING]: 'Pending',
  [OrderStatus.CONFIRMED]: 'Confirmed',
  [OrderStatus.PROCESSING]: 'Processing',
  [OrderStatus.SHIPPED]: 'Shipped',
  [OrderStatus.DELIVERED]: 'Delivered',
  [OrderStatus.CANCELLED]: 'Cancelled',
  [OrderStatus.REFUNDED]: 'Refunded',
};

function OrderRow({ order }: { order: OrderSummary }) {
  const statusClass = STATUS_COLORS[order.status] ?? 'bg-gray-100 text-gray-600';
  const statusLabel = STATUS_LABEL[order.status] ?? order.status;
  const date = new Date(order.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  return (
    <li className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs text-gray-500">Order</p>
          <p className="font-semibold text-gray-900">#{order.order_number}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Date</p>
          <p className="text-sm text-gray-700">{date}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Items</p>
          <p className="text-sm text-gray-700">
            {order.item_count} item{order.item_count !== 1 ? 's' : ''}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Total</p>
          <p className="text-sm font-semibold text-gray-900">${order.grand_total}</p>
        </div>
        <div>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusClass}`}
          >
            {statusLabel}
          </span>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-end gap-3">
        <Link
          to={`/shop/checkout/success?order=${order.order_number}`}
          className="text-sm font-medium text-upstream-600 hover:underline"
        >
          View details
        </Link>
      </div>
    </li>
  );
}

export default function OrderHistoryPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.orders.list({ page }),
    queryFn: () => ordersApi.getOrders({ page }),
    placeholderData: keepPreviousData,
  });

  const orders = data?.results ?? [];
  const hasNextPage = !!data?.next;
  const hasPrevPage = !!data?.previous;

  return (
    <>
      <Helmet>
        <title>Order History – Upstream Literacy</title>
      </Helmet>

      <div>
        <h2 className="mb-5 text-base font-semibold text-gray-900">Order History</h2>

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-xl border border-gray-200 p-5">
                <LoadingSkeleton lines={2} />
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-sm text-red-700">Failed to load orders. Please try again.</p>
          </div>
        ) : orders.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-gray-50 py-16 text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="mx-auto mb-4 h-12 w-12 text-gray-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"
              />
            </svg>
            <p className="text-base font-medium text-gray-600">No orders yet</p>
            <p className="mt-1 text-sm text-gray-400">
              Your order history will appear here after your first purchase.
            </p>
            <Link to="/shop" className="btn-primary mt-6 inline-flex">
              Start Shopping
            </Link>
          </div>
        ) : (
          <>
            <ul className="space-y-4">
              {orders.map((order) => (
                <OrderRow key={order.id} order={order} />
              ))}
            </ul>

            {(hasPrevPage || hasNextPage) && (
              <div className="mt-6 flex items-center justify-center gap-4">
                <button
                  type="button"
                  onClick={() => setPage((p) => p - 1)}
                  disabled={!hasPrevPage}
                  className="btn-secondary disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-500">Page {page}</span>
                <button
                  type="button"
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!hasNextPage}
                  className="btn-secondary disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
