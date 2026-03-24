import { Helmet } from 'react-helmet-async';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '@/lib/api/auth';
import { useUIStore } from '@/stores/uiStore';

const schema = z
  .object({
    first_name: z.string().min(1, 'First name is required'),
    last_name: z.string().min(1, 'Last name is required'),
    email: z.string().email('Enter a valid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
      .regex(/[0-9]/, 'Must contain at least one number')
      .regex(/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?`~]/, 'Must contain at least one special character'),
    confirm_password: z.string().min(1, 'Please confirm your password'),
  })
  .refine((data) => data.password === data.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords do not match',
  });

type FormValues = z.infer<typeof schema>;

export default function RegisterPage() {
  const navigate = useNavigate();
  const addToast = useUIStore((s) => s.addToast);

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: Omit<FormValues, 'confirm_password'>) => authApi.register(data),
    onSuccess: (data) => {
      addToast(
        data.message ??
          'Account created! Please check your email to verify your address.',
        'success',
      );
      navigate('/login');
    },
    onError: (err: unknown) => {
      const apiError = (err as { response?: { data?: { error?: { field_errors?: Record<string, string[]> } } } })
        ?.response?.data?.error;
      const fieldErrors = apiError?.field_errors;
      if (fieldErrors && Object.keys(fieldErrors).length) {
        Object.entries(fieldErrors).forEach(([field, messages]) => {
          if (field === 'non_field_errors') {
            addToast(messages[0], 'error');
          } else {
            setError(field as keyof FormValues, { message: messages[0] });
          }
        });
      } else {
        addToast('Registration failed. Please try again.', 'error');
      }
    },
  });

  function onSubmit({ confirm_password: _ignored, ...data }: FormValues) {
    mutation.mutate(data);
  }

  return (
    <>
      <Helmet>
        <title>Create Account – Upstream Literacy</title>
      </Helmet>

      <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 px-4 py-12">
        <div className="w-full max-w-md">
          {/* Logo + heading */}
          <div className="mb-8 text-center">
            <Link to="/shop" className="inline-block text-upstream-700">
              <span className="text-2xl font-bold tracking-tight">Upstream Literacy</span>
            </Link>
            <h1 className="mt-3 text-xl font-semibold text-gray-900">Create an account</h1>
          </div>

          <div className="rounded-2xl border border-gray-200 bg-white px-6 py-8 shadow-sm sm:px-8">
            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="first_name" className="label">First name</label>
                  <input
                    id="first_name"
                    type="text"
                    autoComplete="given-name"
                    {...register('first_name')}
                    className="input mt-1"
                    placeholder="Jane"
                  />
                  {errors.first_name && <p className="error-text">{errors.first_name.message}</p>}
                </div>

                <div>
                  <label htmlFor="last_name" className="label">Last name</label>
                  <input
                    id="last_name"
                    type="text"
                    autoComplete="family-name"
                    {...register('last_name')}
                    className="input mt-1"
                    placeholder="Smith"
                  />
                  {errors.last_name && <p className="error-text">{errors.last_name.message}</p>}
                </div>
              </div>

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
                <label htmlFor="password" className="label">Password</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  {...register('password')}
                  className="input mt-1"
                />
                {errors.password ? (
                  <p className="error-text">{errors.password.message}</p>
                ) : (
                  <p className="mt-1 text-xs text-gray-400">
                    At least 8 characters, one uppercase, one number, one special character.
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="confirm_password" className="label">Confirm password</label>
                <input
                  id="confirm_password"
                  type="password"
                  autoComplete="new-password"
                  {...register('confirm_password')}
                  className="input mt-1"
                />
                {errors.confirm_password && (
                  <p className="error-text">{errors.confirm_password.message}</p>
                )}
              </div>

              {mutation.isError && !Object.keys(errors).length && (
                <div role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
                  Registration failed. Please try again.
                </div>
              )}

              <button
                type="submit"
                disabled={mutation.isPending}
                className="btn-primary w-full justify-center"
              >
                {mutation.isPending ? 'Creating account…' : 'Create Account'}
              </button>
            </form>
          </div>

          <p className="mt-4 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-upstream-600 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </>
  );
}
