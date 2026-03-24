import { Helmet } from 'react-helmet-async';
import { Link, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ordersApi } from '@/lib/api/orders';
import { queryKeys } from '@/lib/queryKeys';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';
import { OrderStatus } from '@/types';

const STATUS_LABEL: Record<OrderStatus, string> = {
  [OrderStatus.PENDING]: 'Pending',
  [OrderStatus.CONFIRMED]: 'Confirmed',
  [OrderStatus.PROCESSING]: 'Processing',
  [OrderStatus.SHIPPED]: 'Shipped',
  [OrderStatus.DELIVERED]: 'Delivered',
  [OrderStatus.CANCELLED]: 'Cancelled',
  [OrderStatus.REFUNDED]: 'Refunded',
};

export default function OrderConfirmationPage() {
  const [searchParams] = useSearchParams();
  const orderNumber = searchParams.get('order') ?? '';

  const { data: order, isLoading } = useQuery({
    queryKey: queryKeys.orders.detail(orderNumber),
    queryFn: () => ordersApi.getOrder(orderNumber),
    enabled: !!orderNumber,
    retry: false,
  });

  return (
    <>
      <Helmet>
        <title>Order Confirmed – Upstream Literacy</title>
      </Helmet>

      <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6 lg:px-8">
        {/* Success banner */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-8 w-8 text-green-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
            </svg>
          </div>
          <h1 className="mt-4 text-2xl font-bold text-gray-900">Thank you for your order!</h1>
          <p className="mt-2 text-gray-500">
            {orderNumber ? (
              <>
                Your order <span className="font-semibold text-gray-700">#{orderNumber}</span> has
                been placed and is being processed.
              </>
            ) : (
              'Your order has been placed and is being processed.'
            )}
          </p>
        </div>

        {/* Order details */}
        {isLoading ? (
          <div className="rounded-xl border border-gray-200 p-6">
            <LoadingSkeleton lines={6} />
          </div>
        ) : order ? (
          <div className="overflow-hidden rounded-xl border border-gray-200">
            <div className="flex items-center justify-between bg-gray-50 px-6 py-4">
              <div>
                <p className="text-xs text-gray-500">Order number</p>
                <p className="font-semibold text-gray-900">#{order.order_number}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-500">Status</p>
                <p className="font-semibold capitalize text-upstream-700">
                  {STATUS_LABEL[order.status] ?? order.status}
                </p>
              </div>
            </div>

            <ul className="divide-y divide-gray-100 px-6">
              {order.items.map((item) => (
                <li key={item.id} className="flex items-center gap-4 py-4">
                  {item.product_image && (
                    <img
                      src={item.product_image}
                      alt={item.product_title}
                      className="h-14 w-14 flex-shrink-0 rounded-lg object-cover"
                    />
                  )}
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{item.product_title}</p>
                    {Object.keys(item.sku_attributes).length > 0 && (
                      <p className="text-xs text-gray-500">
                        {Object.entries(item.sku_attributes)
                          .map(([k, v]) => `${k}: ${v}`)
                          .join(', ')}
                      </p>
                    )}
                    <p className="text-xs text-gray-400">Qty: {item.quantity}</p>
                  </div>
                  <span className="text-sm font-semibold text-gray-900">${item.line_total}</span>
                </li>
              ))}
            </ul>

            <div className="divide-y divide-gray-100 border-t border-gray-200 px-6">
              {[
                { label: 'Subtotal', value: `$${order.subtotal}` },
                { label: 'Shipping', value: `$${order.shipping_total}` },
                { label: 'Tax', value: `$${order.tax_total}` },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between py-2 text-sm">
                  <span className="text-gray-500">{label}</span>
                  <span className="text-gray-700">{value}</span>
                </div>
              ))}
              <div className="flex justify-between py-3 text-base font-semibold">
                <span>Total</span>
                <span>${order.grand_total}</span>
              </div>
            </div>

            {order.shipping_address && (
              <div className="border-t border-gray-200 px-6 py-4">
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                  Shipping to
                </p>
                <address className="not-italic text-sm text-gray-700">
                  {order.shipping_address.first_name} {order.shipping_address.last_name}
                  <br />
                  {order.shipping_address.address_line1}
                  {order.shipping_address.address_line2 && (
                    <>, {order.shipping_address.address_line2}</>
                  )}
                  <br />
                  {order.shipping_address.city}, {order.shipping_address.state}{' '}
                  {order.shipping_address.zip_code}
                </address>
              </div>
            )}
          </div>
        ) : null}

        {/* CTAs */}
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <Link to="/shop/account/orders" className="btn-primary">
            View My Orders
          </Link>
          <Link to="/shop" className="btn-secondary">
            Continue Shopping
          </Link>
        </div>
      </div>
    </>
  );
}
