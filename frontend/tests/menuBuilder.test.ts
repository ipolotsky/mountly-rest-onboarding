import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";

vi.mock("@/api/client", () => ({
  apiBaseUrl: "/api",
  createOnboarding: vi.fn(),
  fetchOnboarding: vi.fn(),
  parseLegal: vi.fn(),
  saveLegal: vi.fn(),
  parseBanking: vi.fn(),
  saveBanking: vi.fn(),
  parseMenu: vi.fn(),
  saveMenu: vi.fn(async (_id: string, block: unknown) => block),
  confirmStep: vi.fn(),
}));

import { useOnboardingStore } from "@/stores/onboarding";
import { UNCATEGORIZED_GROUP_NAME, emptyOnboarding } from "@/domain/factory";

function seedStore() {
  const store = useOnboardingStore();
  store.onboarding = emptyOnboarding("test_id", "fr", "desktop");
  return store;
}

describe("menu builder mutations", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("adds a group and an item to it", () => {
    const store = seedStore();
    const group = store.addGroup("Entrées");
    expect(group).not.toBeNull();
    expect(store.menu?.groups.length).toBe(1);

    const item = store.addItem(group!.id);
    expect(item).not.toBeNull();
    expect(store.menu?.groups[0]?.items.length).toBe(1);
  });

  it("removes an item", () => {
    const store = seedStore();
    const group = store.addGroup("Plats");
    const item = store.addItem(group!.id);
    store.removeItem(group!.id, item!.id);
    expect(store.menu?.groups[0]?.items.length).toBe(0);
  });

  it("moves items to 'Sans catégorie' when a group is removed and never destroys them", () => {
    const store = seedStore();
    const group = store.addGroup("Desserts");
    store.addItem(group!.id);
    store.addItem(group!.id);

    store.removeGroup(group!.id);

    const bucket = store.menu?.groups.find((x) => x.name === UNCATEGORIZED_GROUP_NAME);
    expect(bucket).not.toBeUndefined();
    expect(bucket?.items.length).toBe(2);
    expect(store.menu?.groups.find((x) => x.id === group!.id)).toBeUndefined();
  });

  it("undoes a group removal, restoring the group with its items", () => {
    const store = seedStore();
    const group = store.addGroup("Boissons");
    store.addItem(group!.id);

    store.removeGroup(group!.id);
    store.undoRemoveGroup();

    const restored = store.menu?.groups.find((x) => x.name === "Boissons");
    expect(restored).not.toBeUndefined();
    expect(restored?.items.length).toBe(1);
  });

  it("never removes the 'Sans catégorie' bucket", () => {
    const store = seedStore();
    const bucket = store.addGroup(UNCATEGORIZED_GROUP_NAME);
    store.removeGroup(bucket!.id);
    expect(store.menu?.groups.find((x) => x.name === UNCATEGORIZED_GROUP_NAME)).not.toBeUndefined();
  });

  it("keeps a price-less item valid (empty prices array)", () => {
    const store = seedStore();
    const group = store.addGroup("Tapas");
    const item = store.addItem(group!.id);
    expect(item?.prices).toEqual([]);
    store.setItemPrices(group!.id, item!.id, []);
    expect(store.menu?.groups[0]?.items[0]?.prices).toEqual([]);
  });

  it("stores size variants as {label, amount} pairs preserving the original string", () => {
    const store = seedStore();
    const group = store.addGroup("Bières");
    const item = store.addItem(group!.id);
    store.setItemPrices(group!.id, item!.id, [
      { label: "25 cl", amount: "3,50" },
      { label: "50 cl", amount: "6 €" },
    ]);
    const prices = store.menu?.groups[0]?.items[0]?.prices ?? [];
    expect(prices.length).toBe(2);
    expect(prices[0]).toEqual({ label: "25 cl", amount: "3,50" });
    expect(prices[1]?.amount).toBe("6 €");
  });

  it("marks edited items as user_edited so re-parse cannot overwrite them", () => {
    const store = seedStore();
    const group = store.addGroup("Pizzas");
    const item = store.addItem(group!.id);
    store.editItemName(group!.id, item!.id, "Margherita");
    const stored = store.menu?.groups[0]?.items[0];
    expect(stored?.name.value).toBe("Margherita");
    expect(stored?.name.provenance).toBe("user_edited");
  });
});
