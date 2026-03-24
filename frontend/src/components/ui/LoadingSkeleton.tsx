interface Props {
  /** Number of skeleton lines to render */
  lines?: number;
  /** Extra CSS classes for the container */
  className?: string;
}

/**
 * Reusable skeleton loading component.
 * Renders animated pulse bars to indicate loading state.
 */
export function LoadingSkeleton({ lines = 3, className = '' }: Props) {
  return (
    <div
      role="status"
      aria-label="Loading…"
      className={`animate-pulse space-y-3 ${className}`}
    >
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={`h-4 rounded bg-gray-200 ${
            index === 0
              ? 'w-3/4'
              : index === lines - 1 && lines > 2
                ? 'w-1/2'
                : 'w-full'
          }`}
        />
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  );
}

// Named variants for common use-cases

export function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div role="status" aria-label="Loading…" className={`animate-pulse ${className}`}>
      <div className="aspect-square rounded-lg bg-gray-200" />
      <div className="mt-3 space-y-2">
        <div className="h-4 w-3/4 rounded bg-gray-200" />
        <div className="h-4 w-1/2 rounded bg-gray-200" />
      </div>
      <span className="sr-only">Loading…</span>
    </div>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export default LoadingSkeleton;
