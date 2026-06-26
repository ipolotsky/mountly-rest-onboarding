import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import type { Field } from "@/types/contract";

const trackSpy = vi.fn();

vi.mock("@/composables/useAnalytics", () => ({
  useAnalytics: () => ({
    track: trackSpy,
    flush: vi.fn(async () => undefined),
    device: () => "desktop" as const,
  }),
}));

vi.mock("@/api/client", () => ({
  apiBaseUrl: "/api",
  createOnboarding: vi.fn(),
  fetchOnboarding: vi.fn(),
  parseLegal: vi.fn(),
  saveLegal: vi.fn(),
  parseBanking: vi.fn(),
  saveBanking: vi.fn(),
  parseMenu: vi.fn(),
  saveMenu: vi.fn(),
  confirmStep: vi.fn(async () => {
    throw new Error("offline");
  }),
}));

import { useOnboarding } from "@/composables/useOnboarding";
import { useOnboardingStore } from "@/stores/onboarding";
import { emptyOnboarding } from "@/domain/factory";

function parserField(value: string | null): Field {
  return {
    value: value,
    status: value == null ? "missing" : "present",
    confidence: 0.7,
    provenance: "parser",
    valid: null,
  };
}

describe("confirm-time analytics emission wiring", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    trackSpy.mockClear();
  });

  it("emits one field_resolved per legal field with doc_type at step-1 confirm", async () => {
    const store = useOnboardingStore();
    store.onboarding = emptyOnboarding("test_id", "fr", "desktop");
    store.onboarding.legal.status = "ready";
    store.onboarding.legal.fields.legal_name = parserField("Chez Pierre");
    store.parsedSnapshots.legal = JSON.parse(JSON.stringify(store.onboarding.legal));

    const onboarding = useOnboarding();
    await onboarding.confirm(1);

    const fieldEvents = trackSpy.mock.calls.filter((call) => call[0] === "field_resolved");
    expect(fieldEvents.length).toBe(6);
    expect(fieldEvents.every((call) => call[2]?.doc_type === "legal")).toBe(true);
    const nameEvent = fieldEvents.find((call) => call[2]?.field_name === "legal_name");
    expect(nameEvent?.[2]?.resolution).toBe("accepted_as_is");
  });

  it("does NOT emit parse_completed from the client", async () => {
    const store = useOnboardingStore();
    store.onboarding = emptyOnboarding("test_id", "fr", "desktop");

    const onboarding = useOnboarding();
    await onboarding.confirm(1);

    const parseCompleted = trackSpy.mock.calls.filter((call) => call[0] === "parse_completed");
    expect(parseCompleted.length).toBe(0);
  });

  it("emits menu_group_resolved per group and menu_usable_reached at step-3 confirm", async () => {
    const store = useOnboardingStore();
    store.onboarding = emptyOnboarding("test_id", "fr", "desktop");
    store.onboarding.menu.status = "ready";
    const group = {
      id: "g1",
      name: "Plats",
      provenance: "parser" as const,
      source_file_ids: [],
      items: [
        { id: "i1", name: parserField("Steak"), description: parserField(null), prices: [], confidence: 0.9, provenance: "parser" as const },
      ],
    };
    store.onboarding.menu.groups = [group];
    store.parsedSnapshots.menu = JSON.parse(JSON.stringify(store.onboarding.menu));

    const onboarding = useOnboarding();
    await onboarding.confirm(3);

    const groupEvents = trackSpy.mock.calls.filter((call) => call[0] === "menu_group_resolved");
    expect(groupEvents.length).toBe(1);
    expect(groupEvents[0]?.[2]?.items_final).toBe(1);
    const usable = trackSpy.mock.calls.filter((call) => call[0] === "menu_usable_reached");
    expect(usable.length).toBe(1);
    expect(usable[0]?.[2]?.items_count).toBe(1);
  });
});
