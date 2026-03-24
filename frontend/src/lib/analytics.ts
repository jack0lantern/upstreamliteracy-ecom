type Properties = Record<string, string | number | boolean | null | undefined>;

const isDev = import.meta.env.DEV;

/**
 * Track an analytics event. In development this logs to the console.
 * Replace the body with a PostHog (or similar) call when you go to production.
 */
export function trackEvent(name: string, properties?: Properties): void {
  if (isDev) {
    console.info('[analytics]', name, properties ?? {});
    return;
  }

  // Production: forward to PostHog, Segment, etc.
  // Example:
  // if (typeof window !== 'undefined' && (window as any).posthog) {
  //   (window as any).posthog.capture(name, properties);
  // }
}

/**
 * Identify the current user. Call after successful login.
 */
export function identifyUser(userId: string | number, traits?: Properties): void {
  if (isDev) {
    console.info('[analytics] identify', userId, traits ?? {});
    return;
  }
  // posthog.identify(String(userId), traits);
}

/**
 * Reset identity. Call on logout.
 */
export function resetIdentity(): void {
  if (isDev) {
    console.info('[analytics] reset');
    return;
  }
  // posthog.reset();
}
