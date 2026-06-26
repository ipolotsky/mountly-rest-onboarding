import { computed } from "vue";
import type { ComputedRef } from "vue";
import type {
  BankingBlock,
  LegalBlock,
  MenuBlock,
  Onboarding,
  Step,
} from "@/types/contract";
import { useOnboardingStore } from "@/stores/onboarding";
import { useAnalytics } from "@/composables/useAnalytics";
import { currentLocale } from "@/i18n";
import {
  buildBankingFieldEvents,
  buildLegalFieldEvents,
  buildMenuGroupEvents,
} from "@/domain/analyticsEvents";

export interface UseOnboarding {
  onboarding: ComputedRef<Onboarding | null>;
  legal: ComputedRef<LegalBlock | null>;
  banking: ComputedRef<BankingBlock | null>;
  menu: ComputedRef<MenuBlock | null>;
  reviewCount: ComputedRef<number>;
  parsing: ComputedRef<boolean>;
  loading: ComputedRef<boolean>;
  ensureSession: () => Promise<string>;
  startFresh: () => Promise<string>;
  load: (id: string) => Promise<void>;
  confirm: (step: Step) => Promise<void>;
  track: (name: string, props?: Record<string, unknown>) => void;
  store: ReturnType<typeof useOnboardingStore>;
}

export function useOnboarding(): UseOnboarding {
  const store = useOnboardingStore();
  const analytics = useAnalytics();

  function track(name: string, props?: Record<string, unknown>): void {
    const id = store.onboardingId ?? "unknown";
    analytics.track(name, id, props);
  }

  async function ensureSession(): Promise<string> {
    const id = await store.ensureSession(currentLocale(), analytics.device());
    track("onboarding_started");
    return id;
  }

  async function startFresh(): Promise<string> {
    const id = await store.startFresh(currentLocale(), analytics.device());
    track("onboarding_started");
    return id;
  }

  async function load(id: string): Promise<void> {
    await store.load(id);
  }

  function emitResolutionEvents(step: Step): void {
    if (step === 1 && store.onboarding != null) {
      const events = buildLegalFieldEvents(store.parsedSnapshots.legal, store.onboarding.legal);
      for (const event of events) {
        track("field_resolved", { ...event });
      }
    } else if (step === 2 && store.onboarding != null) {
      const events = buildBankingFieldEvents(store.parsedSnapshots.banking, store.onboarding.banking);
      for (const event of events) {
        track("field_resolved", { ...event });
      }
    } else if (step === 3 && store.onboarding != null) {
      const groupEvents = buildMenuGroupEvents(store.parsedSnapshots.menu, store.onboarding.menu);
      let itemsCount = 0;
      for (const event of groupEvents) {
        track("menu_group_resolved", { ...event });
        itemsCount += event.items_final;
      }
      track("menu_usable_reached", { items_count: itemsCount });
    }
  }

  async function confirm(step: Step): Promise<void> {
    const startedAt = performance.now();
    emitResolutionEvents(step);
    await store.confirm(step);
    track("step_confirmed", { step: step, duration_ms: Math.round(performance.now() - startedAt) });
    if (step === 3) {
      track("onboarding_completed", { duration_ms: Math.round(performance.now() - startedAt) });
    }
  }

  return {
    onboarding: computed(() => store.onboarding),
    legal: computed(() => store.legal),
    banking: computed(() => store.banking),
    menu: computed(() => store.menu),
    reviewCount: computed(() => store.menuReviewCount),
    parsing: computed(() => store.parsing),
    loading: computed(() => store.loading),
    ensureSession: ensureSession,
    startFresh: startFresh,
    load: load,
    confirm: confirm,
    track: track,
    store: store,
  };
}
