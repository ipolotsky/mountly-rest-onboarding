import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";
import type { BlockStatus, Onboarding } from "@/types/contract";

const fetchOnboarding = vi.fn();

vi.mock("@/api/client", () => ({
  apiBaseUrl: "/api",
  createOnboarding: vi.fn(),
  fetchOnboarding: (id: string) => fetchOnboarding(id),
  fetchRestaurant: vi.fn(),
  parseLegal: vi.fn(),
  saveLegal: vi.fn(),
  parseBanking: vi.fn(),
  saveBanking: vi.fn(),
  parseMenu: vi.fn(),
  saveMenu: vi.fn(),
  confirmStep: vi.fn(),
  submitFeedback: vi.fn(),
  sendEvents: vi.fn(async () => undefined),
  fetchAdminOnboardings: vi.fn(),
  fetchAdminMetrics: vi.fn(),
}));

import WizardLegal from "@/views/WizardLegal.vue";
import { fr } from "@/i18n/fr";
import { useOnboardingStore } from "@/stores/onboarding";
import { emptyOnboarding } from "@/domain/factory";

function onboardingWithLegalStatus(status: BlockStatus): Onboarding {
  const onboarding = emptyOnboarding("test_id", "fr", "desktop");
  onboarding.legal.status = status;
  return onboarding;
}

describe("parsing poll on (re)load", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    fetchOnboarding.mockReset();
    localStorage.setItem("onboarding_id", "test_id");
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts polling when a block loads as parsing and resolves it to ready", async () => {
    fetchOnboarding
      .mockResolvedValueOnce(onboardingWithLegalStatus("parsing"))
      .mockResolvedValueOnce(onboardingWithLegalStatus("parsing"))
      .mockResolvedValueOnce(onboardingWithLegalStatus("ready"));

    const store = useOnboardingStore();
    await store.load("test_id");

    expect(store.legal?.status).toBe("parsing");
    expect(store.parsing).toBe(true);

    await vi.advanceTimersByTimeAsync(1500);
    expect(store.legal?.status).toBe("parsing");

    await vi.advanceTimersByTimeAsync(1500);
    expect(store.legal?.status).toBe("ready");
    expect(store.parsing).toBe(false);
  });

  it("does not start a poll when no block is parsing", async () => {
    fetchOnboarding.mockResolvedValue(onboardingWithLegalStatus("ready"));

    const store = useOnboardingStore();
    await store.load("test_id");

    expect(store.parsing).toBe(false);
    await vi.advanceTimersByTimeAsync(5000);
    expect(fetchOnboarding).toHaveBeenCalledTimes(1);
  });

  it("does not start a second interval for the same parsing block", async () => {
    fetchOnboarding.mockResolvedValue(onboardingWithLegalStatus("parsing"));

    const store = useOnboardingStore();
    await store.load("test_id");
    store.startParsingPollIfNeeded();
    store.startParsingPollIfNeeded();

    await vi.advanceTimersByTimeAsync(1500);
    expect(fetchOnboarding).toHaveBeenCalledTimes(2);
    store.stopParsingPoll();
  });

  it("gives up after the timeout and marks the stale block as couldnt_parse", async () => {
    fetchOnboarding.mockResolvedValue(onboardingWithLegalStatus("parsing"));

    const store = useOnboardingStore();
    await store.load("test_id");

    await vi.advanceTimersByTimeAsync(121000);
    expect(store.legal?.status).toBe("couldnt_parse");
    expect(store.parsing).toBe(false);
  });

  it("shows the parsing loader on WizardLegal after a reload mid-parse", async () => {
    fetchOnboarding.mockResolvedValue(onboardingWithLegalStatus("parsing"));

    const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: "/", name: "start", component: { template: "<div />" } },
        { path: "/onboarding/legal", name: "legal", component: { template: "<div />" } },
        { path: "/onboarding/banking", name: "banking", component: { template: "<div />" } },
      ],
    });

    const wrapper = mount(WizardLegal, { global: { plugins: [i18n, router] } });
    await flushPromises();

    const singularReading = fr.parse.reading.split("|")[0]!.trim();
    expect(wrapper.text()).toContain(singularReading);
    const store = useOnboardingStore();
    store.stopParsingPoll();
  });
});
