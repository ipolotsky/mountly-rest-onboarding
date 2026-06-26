import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import type { Onboarding } from "@/types/contract";

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

import { useOnboardingStore } from "@/stores/onboarding";
import { emptyOnboarding, userField } from "@/domain/factory";

function resumedOnboarding(): Onboarding {
  const onboarding = emptyOnboarding("test_id", "fr", "desktop");
  onboarding.legal.status = "ready";
  onboarding.legal.fields.siren = {
    value: "913472056",
    status: "present",
    confidence: 0.97,
    provenance: "parser",
    valid: true,
  };
  onboarding.legal.fields.legal_name = userField("EDITED BY USER", "user_edited");
  return onboarding;
}

describe("parsed snapshot rehydration on resume", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    fetchOnboarding.mockReset();
    localStorage.setItem("onboarding_id", "test_id");
  });

  it("seeds the snapshot from parser-provenance values and blanks edited ones", async () => {
    fetchOnboarding.mockResolvedValue(resumedOnboarding());
    const store = useOnboardingStore();
    await store.load("test_id");

    expect(store.parsedSnapshots.legal?.fields.siren.value).toBe("913472056");
    expect(store.parsedSnapshots.legal?.fields.legal_name.value).toBe(null);
  });

  it("does not clobber an existing in-session snapshot", async () => {
    fetchOnboarding.mockResolvedValue(resumedOnboarding());
    const store = useOnboardingStore();
    store.parsedSnapshots.legal = emptyOnboarding("test_id", "fr", "desktop").legal;
    store.parsedSnapshots.legal.fields.siren = userField("000", "parser");

    await store.load("test_id");

    expect(store.parsedSnapshots.legal.fields.siren.value).toBe("000");
  });

  it("leaves snapshots null when the block was never parsed", async () => {
    fetchOnboarding.mockResolvedValue(emptyOnboarding("test_id", "fr", "desktop"));
    const store = useOnboardingStore();
    await store.load("test_id");

    expect(store.parsedSnapshots.legal).toBe(null);
    expect(store.parsedSnapshots.menu).toBe(null);
  });
});
