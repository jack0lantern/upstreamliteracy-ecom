import { useEffect } from 'react';
import { Helmet } from 'react-helmet-async';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { accountApi } from '@/lib/api/account';
import { authApi } from '@/lib/api/auth';
import { queryKeys } from '@/lib/queryKeys';
import { useUIStore } from '@/stores/uiStore';
import { useAuthStore } from '@/stores/authStore';
import LoadingSkeleton from '@/components/ui/LoadingSkeleton';

// ─── Profile form ─────────────────────────────────────────────────────────────

const profileSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  phone: z.string().optional(),
});

type ProfileFormValues = z.infer<typeof profileSchema>;

// ─── Change password form ─────────────────────────────────────────────────────

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z
      .string()
      .min(8, 'Must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain an uppercase letter')
      .regex(/[0-9]/, 'Must contain a number'),
    confirm_password: z.string().min(1, 'Please confirm new password'),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    path: ['confirm_password'],
    message: 'Passwords do not match',
  });

type PasswordFormValues = z.infer<typeof passwordSchema>;

export default function ProfilePage() {
  const addToast = useUIStore((s) => s.addToast);
  const setUser = useAuthStore((s) => s.setUser);
  const queryClient = useQueryClient();

  const { data: profile, isLoading } = useQuery({
    queryKey: queryKeys.account.profile(),
    queryFn: accountApi.getProfile,
  });

  const {
    register: regProfile,
    handleSubmit: handleProfile,
    reset: resetProfile,
    formState: { errors: profileErrors },
  } = useForm<ProfileFormValues>({ resolver: zodResolver(profileSchema) });

  const {
    register: regPassword,
    handleSubmit: handlePassword,
    reset: resetPassword,
    formState: { errors: passwordErrors },
    setError: setPasswordError,
  } = useForm<PasswordFormValues>({ resolver: zodResolver(passwordSchema) });

  // Sync profile data into form
  useEffect(() => {
    if (profile) {
      resetProfile({
        first_name: profile.first_name,
        last_name: profile.last_name,
        phone: profile.phone ?? '',
      });
    }
  }, [profile, resetProfile]);

  const updateProfileMutation = useMutation({
    mutationFn: accountApi.updateProfile,
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.account.profile(), updated);
      setUser({
        id: updated.id,
        email: updated.email,
        first_name: updated.first_name,
        last_name: updated.last_name,
        is_email_verified: updated.is_email_verified,
        date_joined: updated.date_joined,
      });
      addToast('Profile updated successfully.', 'success');
    },
    onError: () => addToast('Failed to update profile.', 'error'),
  });

  const changePasswordMutation = useMutation({
    mutationFn: ({ current_password, new_password }: PasswordFormValues) =>
      authApi.changePassword(current_password, new_password),
    onSuccess: () => {
      addToast('Password changed successfully.', 'success');
      resetPassword();
    },
    onError: (err: unknown) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 400) {
        setPasswordError('current_password', { message: 'Incorrect current password.' });
      } else {
        addToast('Failed to change password.', 'error');
      }
    },
  });

  if (isLoading) {
    return <LoadingSkeleton lines={6} />;
  }

  return (
    <>
      <Helmet>
        <title>Profile – Upstream Literacy</title>
      </Helmet>

      <div className="space-y-8">
        {/* Profile section */}
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="mb-5 text-base font-semibold text-gray-900">Personal Information</h2>

          <form
            onSubmit={handleProfile((d) => updateProfileMutation.mutate(d))}
            className="space-y-4"
          >
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label htmlFor="first_name" className="label">First name</label>
                <input
                  id="first_name"
                  type="text"
                  {...regProfile('first_name')}
                  className="input mt-1"
                />
                {profileErrors.first_name && (
                  <p className="error-text">{profileErrors.first_name.message}</p>
                )}
              </div>
              <div>
                <label htmlFor="last_name" className="label">Last name</label>
                <input
                  id="last_name"
                  type="text"
                  {...regProfile('last_name')}
                  className="input mt-1"
                />
                {profileErrors.last_name && (
                  <p className="error-text">{profileErrors.last_name.message}</p>
                )}
              </div>
            </div>

            <div>
              <label className="label">Email address</label>
              <input
                type="email"
                value={profile?.email ?? ''}
                disabled
                className="input mt-1 cursor-not-allowed bg-gray-50 text-gray-500"
              />
              <p className="mt-1 text-xs text-gray-400">
                Email address cannot be changed here.
                {profile && !profile.is_email_verified && (
                  <span className="ml-1 font-medium text-yellow-600">
                    Not verified – check your inbox.
                  </span>
                )}
              </p>
            </div>

            <div>
              <label htmlFor="phone" className="label">Phone (optional)</label>
              <input id="phone" type="tel" {...regProfile('phone')} className="input mt-1" />
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={updateProfileMutation.isPending}
                className="btn-primary"
              >
                {updateProfileMutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          </form>
        </section>

        {/* Change password section */}
        <section className="rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="mb-5 text-base font-semibold text-gray-900">Change Password</h2>

          <form
            onSubmit={handlePassword((d) => changePasswordMutation.mutate(d))}
            className="space-y-4"
          >
            <div>
              <label htmlFor="current_password" className="label">Current password</label>
              <input
                id="current_password"
                type="password"
                autoComplete="current-password"
                {...regPassword('current_password')}
                className="input mt-1"
              />
              {passwordErrors.current_password && (
                <p className="error-text">{passwordErrors.current_password.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="new_password" className="label">New password</label>
              <input
                id="new_password"
                type="password"
                autoComplete="new-password"
                {...regPassword('new_password')}
                className="input mt-1"
              />
              {passwordErrors.new_password ? (
                <p className="error-text">{passwordErrors.new_password.message}</p>
              ) : (
                <p className="mt-1 text-xs text-gray-400">
                  At least 8 characters, one uppercase, one number.
                </p>
              )}
            </div>

            <div>
              <label htmlFor="confirm_password" className="label">Confirm new password</label>
              <input
                id="confirm_password"
                type="password"
                autoComplete="new-password"
                {...regPassword('confirm_password')}
                className="input mt-1"
              />
              {passwordErrors.confirm_password && (
                <p className="error-text">{passwordErrors.confirm_password.message}</p>
              )}
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={changePasswordMutation.isPending}
                className="btn-primary"
              >
                {changePasswordMutation.isPending ? 'Updating…' : 'Update Password'}
              </button>
            </div>
          </form>
        </section>
      </div>
    </>
  );
}
