import { Helmet } from 'react-helmet-async';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { authApi } from '@/lib/api/auth';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { identifyUser } from '@/lib/analytics';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const nextPath = searchParams.get('next') ?? '/shop';

  const setAuth = useAuthStore((s) => s.setAuth);
  const addToast = useUIStore((s) => s.addToast);
  const [emailUnverified, setEmailUnverified] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const resendMutation = useMutation({
    mutationFn: (email: string) => authApi.resendVerification(email),
    onSuccess: () => addToast('Verification email sent! Check your inbox.', 'success'),
    onError: () => addToast('Failed to resend. Please try again.', 'error'),
  });

  const mutation = useMutation({
    mutationFn: authApi.login,
    onMutate: () => setEmailUnverified(false),
    onSuccess: ({ user, tokens }) => {
      setAuth(user, tokens);
      identifyUser(user.id, { email: user.email });
      addToast(`Welcome back, ${user.first_name || user.email}!`, 'success');
      navigate(nextPath, { replace: true });
    },
    onError: (err: unknown) => {
      const response = (err as { response?: { status?: number; data?: { error?: { code?: string; field_errors?: Record<string, string[]> } } } })?.response;
      const status = response?.status;
      const errorCode = response?.data?.error?.code;
      const fieldErrors = response?.data?.error?.field_errors;

      if (errorCode === 'email_not_verified' || fieldErrors?.non_field_errors?.[0]?.includes('verify')) {
        setEmailUnverified(true);
      } else if (status === 400 && fieldErrors?.non_field_errors?.[0]) {
        setError('password', { message: fieldErrors.non_field_errors[0] });
      } else if (status === 401) {
        setError('password', { message: 'Invalid email or password.' });
      }
    },
  });

  return (
    <>
      <Helmet>
        <title>Sign In – Upstream Literacy</title>
      </Helmet>

      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-12">
        <div className="w-full max-w-md">
          {/* Logo + heading */}
          <div className="mb-8 text-center">
            <Link to="/shop" className="inline-block text-upstream-700">
              <span className="text-2xl font-bold tracking-tight">Upstream Literacy</span>
            </Link>
            <h1 className="mt-3 text-xl font-semibold text-gray-900">Sign in to your account</h1>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white px-6 py-8 shadow-sm sm:px-8">
            <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate className="space-y-4">
              <div>
                <label htmlFor="email" className="label">Email address</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  {...register('email')}
                  className="input mt-1"
                  placeholder="you@example.com"
                />
                {errors.email && <p className="error-text">{errors.email.message}</p>}
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="label">Password</label>
                  <Link
                    to="/forgot-password"
                    className="text-xs text-upstream-600 hover:underline"
                    tabIndex={-1}
                  >
                    Forgot password?
                  </Link>
                </div>
                <input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  {...register('password')}
                  className="input mt-1"
                />
                {errors.password && <p className="error-text">{errors.password.message}</p>}
              </div>

              {emailUnverified && (
                <div role="alert" className="rounded-md bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
                  <p className="font-medium">Email not verified</p>
                  <p className="mt-1">Please check your inbox for a verification link.{' '}
                    <button
                      type="button"
                      onClick={() => resendMutation.mutate(mutation.variables?.email ?? '')}
                      disabled={resendMutation.isPending}
                      className="underline font-medium hover:text-amber-900 disabled:opacity-50"
                    >
                      {resendMutation.isPending ? 'Sending…' : 'Resend email'}
                    </button>
                  </p>
                </div>
              )}

              {mutation.isError && !errors.password && !emailUnverified && (
                <div
                  role="alert"
                  className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                  Sign in failed. Please check your credentials.
                </div>
              )}

              <button
                type="submit"
                disabled={mutation.isPending}
                className="btn-primary w-full justify-center"
              >
                {mutation.isPending ? 'Signing in…' : 'Sign In'}
              </button>
            </form>
          </div>

          <p className="mt-4 text-center text-sm text-gray-500">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="font-medium text-upstream-600 hover:underline">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
