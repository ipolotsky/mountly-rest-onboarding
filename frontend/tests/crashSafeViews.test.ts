import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";
import type { Onboarding } from "@/types/contract";

vi.mock("@/api/client", () => ({
  apiBaseUrl: "/api",
  createOnboarding: vi.fn(async () => ({ id: "fresh_id" })),
  fetchOnboarding: vi.fn(),
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
import WizardBanking from "@/views/WizardBanking.vue";
import RestaurantPage from "@/views/RestaurantPage.vue";
import { fr } from "@/i18n/fr";
import { useOnboardingStore } from "@/stores/onboarding";
import { emptyOnboarding } from "@/domain/factory";

function buildI18n() {
  return createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });
}

function buildRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "start", component: { template: "<div />" } },
      { path: "/onboarding/legal", name: "legal", component: { template: "<div />" } },
      { path: "/onboarding/banking", name: "banking", component: { template: "<div />" } },
      { path: "/onboarding/menu", name: "menu", component: { template: "<div />" } },
      { path: "/restaurant", name: "restaurant", component: { template: "<div />" } },
    ],
  });
}

function seedEmpty(): Onboarding {
  const store = useOnboardingStore();
  const onboarding = emptyOnboarding("test_id", "fr", "desktop");
  store.onboarding = onboarding;
  return onboarding;
}

async function mountView(component: unknown) {
  const i18n = buildI18n();
  const router = buildRouter();
  const wrapper = mount(component as never, { global: { plugins: [i18n, router] } });
  await flushPromises();
  return wrapper;
}

describe("crash-safe rendering of wizard + restaurant views from an all-missing onboarding", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.setItem("onboarding_id", "test_id");
    seedEmpty();
  });

  it("renders WizardLegal without throwing", async () => {
    const wrapper = await mountView(WizardLegal);
    expect(wrapper.text()).toContain(fr.legal.title);
  });

  it("renders WizardBanking without throwing", async () => {
    const wrapper = await mountView(WizardBanking);
    expect(wrapper.text()).toContain(fr.banking.title);
  });

  it("renders RestaurantPage with placeholders, never blank, from empty state", async () => {
    const wrapper = await mountView(RestaurantPage);
    expect(wrapper.text()).toContain(fr.restaurant.sections.legal);
    expect(wrapper.text()).toContain(fr.common.placeholder);
  });
});
