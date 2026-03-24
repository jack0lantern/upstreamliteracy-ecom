import { Helmet } from 'react-helmet-async';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
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

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: ({ user, tokens }) => {
      setAuth(user, tokens);
      identifyUser(user.id, { email: user.email });
      addToast(`Welcome back, ${user.first_name || user.email}!`, 'success');
      navigate(nextPath, { replace: true });
    },
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) {
        setError('password', { message: 'Invalid email or password.' });
      } else {
        addToast('Login failed. Please try again.', 'error');
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

              {mutation.isError && !errors.password && (
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
