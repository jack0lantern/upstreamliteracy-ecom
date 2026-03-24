import { create } from 'zustand';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface UIState {
  isCartSidebarOpen: boolean;
  toasts: Toast[];

  openCartSidebar: () => void;
  closeCartSidebar: () => void;
  toggleCartSidebar: () => void;

  addToast: (message: string, type?: ToastType) => void;
  removeToast: (id: string) => void;
}

let toastCounter = 0;

export const useUIStore = create<UIState>((set) => ({
  isCartSidebarOpen: false,
  toasts: [],

  openCartSidebar: () => set({ isCartSidebarOpen: true }),
  closeCartSidebar: () => set({ isCartSidebarOpen: false }),
  toggleCartSidebar: () =>
    set((state) => ({ isCartSidebarOpen: !state.isCartSidebarOpen })),

  addToast: (message, type = 'info') => {
    const id = `toast-${++toastCounter}-${Date.now()}`;
    set((state) => ({ toasts: [...state.toasts, { id, message, type }] }));

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) }));
    }, 5000);
  },

  removeToast: (id) =>
    set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
}));
