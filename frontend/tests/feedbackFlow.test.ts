import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createMemoryHistory } from "vue-router";

const submitFeedback = vi.fn(async (_id: string, _payload: unknown) => ({ ok: true }));

vi.mock("@/api/client", () => ({
  apiBaseUrl: "/api",
  createOnboarding: vi.fn(async () => ({ id: "test_id" })),
  fetchOnboarding: vi.fn(),
  fetchRestaurant: vi.fn(),
  parseLegal: vi.fn(),
  saveLegal: vi.fn(),
  parseBanking: vi.fn(),
  saveBanking: vi.fn(),
  parseMenu: vi.fn(),
  saveMenu: vi.fn(),
  confirmStep: vi.fn(),
  publishOnboarding: vi.fn(),
  submitFeedback: (id: string, payload: unknown) => submitFeedback(id, payload),
  sendEvents: vi.fn(async () => undefined),
  fetchAdminOnboardings: vi.fn(),
  fetchAdminMetrics: vi.fn(),
  fetchAdminFeedback: vi.fn(),
}));

import RestaurantPage from "@/views/RestaurantPage.vue";
import FeedbackForm from "@/components/FeedbackForm.vue";
import { fr } from "@/i18n/fr";
import { emptyOnboarding } from "@/domain/factory";
import { fetchOnboarding } from "@/api/client";

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

async function mountRestaurant() {
  const wrapper = mount(RestaurantPage, { global: { plugins: [buildI18n(), buildRouter()] } });
  await flushPromises();
  return wrapper;
}

describe("feedback submission shows a thank-you and hides the form", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.setItem("onboarding_id", "test_id");
    submitFeedback.mockClear();
    vi.mocked(fetchOnboarding).mockResolvedValue(emptyOnboarding("test_id", "fr", "desktop"));
  });

  it("shows the form first, then the thank-you message after submit", async () => {
    const wrapper = await mountRestaurant();

    const form = wrapper.findComponent(FeedbackForm);
    expect(form.exists()).toBe(true);
    expect(wrapper.text()).not.toContain(fr.restaurant.feedbackThanks);

    const buttons = form.findAll("button");
    const csatButton = buttons.find((x) => x.text() === "4");
    expect(csatButton).toBeTruthy();
    await csatButton!.trigger("click");

    const submitButton = form.findAll("button").find((x) => x.text() === fr.restaurant.feedbackSubmit);
    expect(submitButton).toBeTruthy();
    await submitButton!.trigger("click");
    await flushPromises();

    expect(submitFeedback).toHaveBeenCalledTimes(1);
    expect(submitFeedback.mock.calls[0]![1]).toMatchObject({ csat: 4 });
    expect(wrapper.findComponent(FeedbackForm).exists()).toBe(false);
    expect(wrapper.text()).toContain(fr.restaurant.feedbackThanks);
  });
});
