import { useEffect, useState, type FormEvent } from 'react';
import { Helmet } from 'react-helmet-async';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { loadStripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { checkoutApi } from '@/lib/api/checkout';
import { cartApi } from '@/lib/api/cart';
import { queryKeys } from '@/lib/queryKeys';
import { useCheckoutStore } from '@/stores/checkoutStore';
import { useUIStore } from '@/stores/uiStore';
import { trackEvent } from '@/lib/analytics';

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? '');

// ─── Step indicators ──────────────────────────────────────────────────────────

const STEPS = ['Contact', 'Shipping', 'Payment', 'Review'] as const;

function StepIndicator({ currentStep }: { currentStep: number }) {
  return (
    <nav aria-label="Checkout progress" className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((label, index) => {
          const stepNumber = index + 1;
          const isComplete = stepNumber < currentStep;
          const isActive = stepNumber === currentStep;

          return (
            <li key={label} className="flex flex-1 items-center">
              <div className="flex items-center gap-2">
                <span
                  className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                    isComplete
                      ? 'bg-upstream-600 text-white'
                      : isActive
                        ? 'border-2 border-upstream-600 text-upstream-600'
                        : 'border-2 border-gray-300 text-gray-400'
                  }`}
                  aria-current={isActive ? 'step' : undefined}
                >
                  {isComplete ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
                    </svg>
                  ) : (
                    stepNumber
                  )}
                </span>
                <span
                  className={`hidden text-sm sm:block ${
                    isActive ? 'font-semibold text-gray-900' : 'text-gray-500'
                  }`}
                >
                  {label}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`mx-2 flex-1 border-t-2 ${
                    isComplete ? 'border-upstream-600' : 'border-gray-300'
                  }`}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

// ─── Zod schemas ──────────────────────────────────────────────────────────────

const contactSchema = z.object({
  guest_email: z.string().email('Valid email required'),
  phone: z.string().optional(),
});

const addressSchema = z.object({
  first_name: z.string().min(1, 'First name required'),
  last_name: z.string().min(1, 'Last name required'),
  address_line1: z.string().min(1, 'Address required'),
  address_line2: z.string().optional(),
  city: z.string().min(1, 'City required'),
  state: z.string().min(2, 'State required').max(2, 'Use 2-letter state code'),
  zip_code: z.string().min(1, 'Zip code required'),
  country: z.string().min(2, 'Country required').default('US'),
});

type ContactFormValues = z.infer<typeof contactSchema>;
type AddressFormValues = z.infer<typeof addressSchema>;

// ─── Step 1 – Contact ─────────────────────────────────────────────────────────

function ContactStep({ sessionToken }: { sessionToken: string }) {
  const addToast = useUIStore((s) => s.addToast);
  const nextStep = useCheckoutStore((s) => s.nextStep);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ContactFormValues>({ resolver: zodResolver(contactSchema) });

  const mutation = useMutation({
    mutationFn: (data: ContactFormValues) =>
      checkoutApi.updateContact(sessionToken, data),
    onSuccess: () => nextStep(),
    onError: () => addToast('Failed to save contact info.', 'error'),
  });

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Contact Information</h2>

      <div>
        <label htmlFor="guest_email" className="label">Email address</label>
        <input id="guest_email" type="email" {...register('guest_email')} className="input mt-1" placeholder="you@example.com" />
        {errors.guest_email && <p className="error-text">{errors.guest_email.message}</p>}
      </div>

      <div>
        <label htmlFor="phone" className="label">Phone (optional)</label>
        <input id="phone" type="tel" {...register('phone')} className="input mt-1" placeholder="+1 (555) 000-0000" />
      </div>

      <div className="flex justify-end pt-2">
        <button type="submit" disabled={mutation.isPending} className="btn-primary">
          {mutation.isPending ? 'Saving…' : 'Continue to Shipping'}
        </button>
      </div>
    </form>
  );
}

// ─── Step 2 – Shipping address + method ──────────────────────────────────────

function ShippingStep({ sessionToken }: { sessionToken: string }) {
  const addToast = useUIStore((s) => s.addToast);
  const nextStep = useCheckoutStore((s) => s.nextStep);
  const prevStep = useCheckoutStore((s) => s.prevStep);

  const { data: rates } = useQuery({
    queryKey: queryKeys.checkout.shippingRates(),
    queryFn: () => checkoutApi.getShippingRates(),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AddressFormValues & { shipping_rate_id: string }>({
    resolver: zodResolver(
      addressSchema.extend({ shipping_rate_id: z.string().min(1, 'Select a shipping method') }),
    ),
  });

  const mutation = useMutation({
    mutationFn: async (data: AddressFormValues & { shipping_rate_id: string }) => {
      const { shipping_rate_id, ...addressData } = data;
      await checkoutApi.updateAddress(sessionToken, {
        shipping_address: addressData,
        billing_same_as_shipping: true,
      });
      await checkoutApi.updateShipping(sessionToken, { shipping_rate_id: Number(shipping_rate_id) });
    },
    onSuccess: () => nextStep(),
    onError: () => addToast('Failed to save shipping info.', 'error'),
  });

  return (
    <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-5">
      <h2 className="text-lg font-semibold text-gray-900">Shipping Address</h2>

      <div className="grid gap-4 sm:grid-cols-2">
        {[
          { id: 'first_name', label: 'First name', placeholder: 'Jane' },
          { id: 'last_name', label: 'Last name', placeholder: 'Smith' },
        ].map(({ id, label, placeholder }) => (
          <div key={id}>
            <label htmlFor={id} className="label">{label}</label>
            <input
              id={id}
              type="text"
              {...register(id as keyof AddressFormValues)}
              className="input mt-1"
              placeholder={placeholder}
            />
            {errors[id as keyof typeof errors] && (
              <p className="error-text">{errors[id as keyof typeof errors]?.message}</p>
            )}
          </div>
        ))}
      </div>

      <div>
        <label htmlFor="address_line1" className="label">Address</label>
        <input id="address_line1" type="text" {...register('address_line1')} className="input mt-1" placeholder="123 Main St" />
        {errors.address_line1 && <p className="error-text">{errors.address_line1.message}</p>}
      </div>

      <div>
        <label htmlFor="address_line2" className="label">Apartment, suite, etc. (optional)</label>
        <input id="address_line2" type="text" {...register('address_line2')} className="input mt-1" />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="city" className="label">City</label>
          <input id="city" type="text" {...register('city')} className="input mt-1" />
          {errors.city && <p className="error-text">{errors.city.message}</p>}
        </div>
        <div>
          <label htmlFor="state" className="label">State</label>
          <input id="state" type="text" {...register('state')} className="input mt-1" maxLength={2} placeholder="TX" />
          {errors.state && <p className="error-text">{errors.state.message}</p>}
        </div>
        <div>
          <label htmlFor="zip_code" className="label">Zip</label>
          <input id="zip_code" type="text" {...register('zip_code')} className="input mt-1" placeholder="78701" />
          {errors.zip_code && <p className="error-text">{errors.zip_code.message}</p>}
        </div>
      </div>

      {/* Shipping methods */}
      {rates && rates.length > 0 && (
        <div>
          <p className="label mb-2">Shipping method</p>
          <div className="space-y-2">
            {rates.map((rate) => (
              <label
                key={rate.id}
                className="flex cursor-pointer items-center gap-3 rounded-lg border border-gray-300 px-4 py-3 transition-colors has-[:checked]:border-upstream-500 has-[:checked]:bg-upstream-50"
              >
                <input
                  type="radio"
                  value={rate.id}
                  {...register('shipping_rate_id')}
                  className="h-4 w-4 text-upstream-600 focus:ring-upstream-500"
                />
                <div className="flex-1">
                  <span className="block text-sm font-medium text-gray-900">{rate.name}</span>
                  <span className="block text-xs text-gray-500">{rate.description}</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">${rate.flat_rate}</span>
              </label>
            ))}
          </div>
          {errors.shipping_rate_id && (
            <p className="error-text">{errors.shipping_rate_id.message as string}</p>
          )}
        </div>
      )}

      <div className="flex justify-between pt-2">
        <button type="button" onClick={prevStep} className="btn-secondary">
          Back
        </button>
        <button type="submit" disabled={mutation.isPending} className="btn-primary">
          {mutation.isPending ? 'Saving…' : 'Continue to Payment'}
        </button>
      </div>
    </form>
  );
}

// ─── Step 3 – Payment ─────────────────────────────────────────────────────────

const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#1f2937',
      '::placeholder': { color: '#9ca3af' },
    },
    invalid: { color: '#dc2626' },
  },
};

function PaymentStepInner({ sessionToken }: { sessionToken: string }) {
  const stripe = useStripe();
  const elements = useElements();
  const addToast = useUIStore((s) => s.addToast);
  const nextStep = useCheckoutStore((s) => s.nextStep);
  const prevStep = useCheckoutStore((s) => s.prevStep);
  const [isProcessing, setIsProcessing] = useState(false);
  const [cardError, setCardError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!stripe || !elements) return;

    setIsProcessing(true);
    setCardError(null);

    const cardElement = elements.getElement(CardElement);
    if (!cardElement) {
      setIsProcessing(false);
      return;
    }

    // Create a PaymentMethod from the card details
    const { error, paymentMethod } = await stripe.createPaymentMethod({
      type: 'card',
      card: cardElement,
    });

    if (error) {
      setCardError(error.message ?? 'Card validation failed.');
      setIsProcessing(false);
      return;
    }

    // Save the payment method ID to the checkout session
    try {
      await checkoutApi.updatePayment(sessionToken, {
        stripe_payment_method_id: paymentMethod.id,
      });
      nextStep();
    } catch {
      addToast('Failed to save payment info.', 'error');
    } finally {
      setIsProcessing(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <h2 className="text-lg font-semibold text-gray-900">Payment</h2>

      <div>
        <label className="label mb-2 block">Card details</label>
        <div className="rounded-lg border border-gray-300 bg-white px-4 py-3">
          <CardElement options={CARD_ELEMENT_OPTIONS} onChange={(e) => setCardError(e.error?.message ?? null)} />
        </div>
        {cardError && <p className="error-text mt-1">{cardError}</p>}
      </div>

      <p className="text-xs text-gray-400">
        Payments are processed securely via Stripe. Your card details never touch our servers.
      </p>

      <div className="flex justify-between pt-2">
        <button type="button" onClick={prevStep} className="btn-secondary">
          Back
        </button>
        <button type="submit" disabled={!stripe || isProcessing} className="btn-primary">
          {isProcessing ? 'Processing…' : 'Review Order'}
        </button>
      </div>
    </form>
  );
}

function PaymentStep({ sessionToken }: { sessionToken: string }) {
  return (
    <Elements stripe={stripePromise}>
      <PaymentStepInner sessionToken={sessionToken} />
    </Elements>
  );
}

// ─── Step 4 – Review + submit ─────────────────────────────────────────────────

function ReviewStep({ sessionToken }: { sessionToken: string }) {
  const addToast = useUIStore((s) => s.addToast);
  const prevStep = useCheckoutStore((s) => s.prevStep);
  const resetCheckout = useCheckoutStore((s) => s.reset);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: session, isLoading } = useQuery({
    queryKey: queryKeys.checkout.session(sessionToken),
    queryFn: () => checkoutApi.getSession(sessionToken),
  });

  const submitMutation = useMutation({
    mutationFn: () => checkoutApi.submitCheckout(sessionToken),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.cart.current() });
      trackEvent('purchase', { order_number: data.order_number });
      resetCheckout();
      navigate(`/shop/checkout/success?order=${data.order_number}`);
    },
    onError: () => addToast('Failed to place order. Please try again.', 'error'),
  });

  if (isLoading) {
    return <div className="animate-pulse space-y-3"><div className="h-6 w-48 rounded bg-gray-200" /><div className="h-40 rounded bg-gray-200" /></div>;
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-gray-900">Review Your Order</h2>

      {session && (
        <dl className="divide-y divide-gray-100 rounded-lg border border-gray-200 text-sm">
          <div className="flex gap-4 px-4 py-3">
            <dt className="w-36 text-gray-500">Contact</dt>
            <dd className="text-gray-900">{session.guest_email}</dd>
          </div>
          {session.shipping_address && (
            <div className="flex gap-4 px-4 py-3">
              <dt className="w-36 text-gray-500">Ship to</dt>
              <dd className="text-gray-900">
                {session.shipping_address.address_line1}, {session.shipping_address.city},{' '}
                {session.shipping_address.state} {session.shipping_address.zip_code}
              </dd>
            </div>
          )}
          {session.shipping_rate_detail && (
            <div className="flex gap-4 px-4 py-3">
              <dt className="w-36 text-gray-500">Shipping</dt>
              <dd className="text-gray-900">
                {session.shipping_rate_detail.name} – ${session.shipping_rate_detail.flat_rate}
              </dd>
            </div>
          )}
          <div className="flex gap-4 px-4 py-3">
            <dt className="w-36 text-gray-500">Subtotal</dt>
            <dd className="font-medium text-gray-900">${session.subtotal}</dd>
          </div>
          <div className="flex gap-4 px-4 py-3">
            <dt className="w-36 text-gray-500">Shipping</dt>
            <dd className="text-gray-900">${session.shipping_cost ?? '0.00'}</dd>
          </div>
          <div className="flex gap-4 px-4 py-3">
            <dt className="w-36 text-gray-500">Tax</dt>
            <dd className="text-gray-900">${session.tax_amount ?? '0.00'}</dd>
          </div>
          <div className="flex gap-4 px-4 py-3 font-semibold">
            <dt className="w-36 text-gray-700">Total</dt>
            <dd className="text-gray-900">${session.computed_total}</dd>
          </div>
        </dl>
      )}

      <div className="flex justify-between pt-2">
        <button type="button" onClick={prevStep} className="btn-secondary">
          Back
        </button>
        <button
          type="button"
          onClick={() => submitMutation.mutate()}
          disabled={submitMutation.isPending}
          className="btn-accent"
        >
          {submitMutation.isPending ? 'Placing order…' : 'Place Order'}
        </button>
      </div>
    </div>
  );
}

// ─── Main checkout layout ─────────────────────────────────────────────────────

export default function CheckoutLayout() {
  const currentStep = useCheckoutStore((s) => s.currentStep);
  const sessionToken = useCheckoutStore((s) => s.sessionToken);
  const setSessionToken = useCheckoutStore((s) => s.setSessionToken);
  const addToast = useUIStore((s) => s.addToast);

  const { data: cart } = useQuery({
    queryKey: queryKeys.cart.current(),
    queryFn: cartApi.getCart,
    staleTime: 1000 * 60,
  });

  const createSessionMutation = useMutation({
    mutationFn: () => checkoutApi.createSession(cart?.token),
    onSuccess: (session) => setSessionToken(session.session_token),
    onError: () => addToast('Could not start checkout session.', 'error'),
  });

  useEffect(() => {
    if (!sessionToken && cart) {
      createSessionMutation.mutate();
    }
    // Only run on mount / when cart becomes available
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cart?.token]);

  return (
    <>
      <Helmet>
        <title>Checkout – Upstream Literacy</title>
      </Helmet>

      <div className="mx-auto max-w-2xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-6 font-heading text-2xl font-bold tracking-tight text-gray-900">Checkout</h1>

        <StepIndicator currentStep={currentStep} />

        {!sessionToken ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-upstream-600" />
          </div>
        ) : (
          <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
            {currentStep === 1 && <ContactStep sessionToken={sessionToken} />}
            {currentStep === 2 && <ShippingStep sessionToken={sessionToken} />}
            {currentStep === 3 && <PaymentStep sessionToken={sessionToken} />}
            {currentStep === 4 && <ReviewStep sessionToken={sessionToken} />}
          </div>
        )}
      </div>
    </>
  );
}
