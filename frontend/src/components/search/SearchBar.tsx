import { useState, useCallback, useRef, type ChangeEvent, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';

function debounce<T extends (...args: Parameters<T>) => void>(fn: T, delay: number) {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

export function SearchBar() {
  const [value, setValue] = useState('');
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const debouncedNavigate = useCallback(
    debounce((q: string) => {
      if (q.trim().length >= 2) {
        navigate(`/shop/search?q=${encodeURIComponent(q.trim())}`);
      }
    }, 300),
    [navigate],
  );

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    setValue(q);
    debouncedNavigate(q);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (q) {
      navigate(`/shop/search?q=${encodeURIComponent(q)}`);
      inputRef.current?.blur();
    }
  }

  return (
    <form
      role="search"
      onSubmit={handleSubmit}
      className="flex w-full max-w-xs items-center"
    >
      <label htmlFor="site-search" className="sr-only">
        Search products
      </label>
      <div className="relative w-full">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-4 w-4 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
            />
          </svg>
        </div>
        <input
          ref={inputRef}
          id="site-search"
          type="search"
          value={value}
          onChange={handleChange}
          placeholder="Search products…"
          autoComplete="off"
          className="block w-full rounded-md border border-gray-300 bg-white py-1.5 pl-9 pr-3 text-sm placeholder:text-gray-400 focus:border-upstream-500 focus:outline-none focus:ring-1 focus:ring-upstream-500"
        />
      </div>
    </form>
  );
}

export default SearchBar;
