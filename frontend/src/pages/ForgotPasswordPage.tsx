import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useUIStore } from '@/stores/uiStore';

const schema = z.object({
  email: z.string().email('Enter a valid email address'),
});

type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const addToast = useUIStore((s) => s.addToast);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: FormValues) => authApi.requestPasswordReset(data.email),
    onSuccess: () => {
      addToast(
        'If an account exists with that email, you will receive a password reset link.',
        'success',
      );
    },
    onError: () => {
      addToast(
        'If an account exists with that email, you will receive a password reset link.',
        'success',
      );
    },
  });

  return (
    <>
      <Helmet>
        <title>Forgot Password – Upstream Literacy</title>
      </Helmet>

      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-12">
        <div className="w-full max-w-md">
          <div className="mb-8 text-center">
            <Link to="/shop" className="inline-block text-upstream-700">
              <span className="text-2xl font-bold tracking-tight">Upstream Literacy</span>
            </Link>
            <h1 className="mt-3 text-xl font-semibold text-gray-900">Reset your password</h1>
            <p className="mt-1 text-sm text-gray-500">
              Enter your email and we&rsquo;ll send you a link to reset your password.
            </p>
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

              {mutation.isSuccess && (
                <div role="alert" className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
                  Check your email for a password reset link.
                </div>
              )}

              <button
                type="submit"
                disabled={mutation.isPending}
                className="btn-primary w-full justify-center"
              >
                {mutation.isPending ? 'Sending…' : 'Send Reset Link'}
              </button>
            </form>
          </div>

          <p className="mt-4 text-center text-sm text-gray-500">
            Remember your password?{' '}
            <Link to="/login" className="font-medium text-upstream-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
