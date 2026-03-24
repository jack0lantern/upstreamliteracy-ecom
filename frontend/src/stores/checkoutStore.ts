import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type CheckoutStep = 1 | 2 | 3 | 4;

interface CheckoutState {
  currentStep: CheckoutStep;
  sessionToken: string | null;

  setStep: (step: CheckoutStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  setSessionToken: (token: string) => void;
  reset: () => void;
}

const initialState = {
  currentStep: 1 as CheckoutStep,
  sessionToken: null,
};

export const useCheckoutStore = create<CheckoutState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setStep: (step) => set({ currentStep: step }),

      nextStep: () => {
        const current = get().currentStep;
        if (current < 4) {
          set({ currentStep: (current + 1) as CheckoutStep });
        }
      },

      prevStep: () => {
        const current = get().currentStep;
        if (current > 1) {
          set({ currentStep: (current - 1) as CheckoutStep });
        }
      },

      setSessionToken: (token) => set({ sessionToken: token }),

      reset: () => set(initialState),
    }),
    {
      name: 'upstream-checkout',
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);
