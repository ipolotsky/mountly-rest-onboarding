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
import { fetchOnboarding } from "@/api/client";
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

  it("adds an item with its name in one atomic call (regression: name was lost)", () => {
    const store = seedStore();
    const group = store.addGroup("Pizzas");
    const item = store.addItem(group!.id, "Margherita");
    expect(item).not.toBeNull();
    const stored = store.menu?.groups[0]?.items[0];
    expect(stored?.name.value).toBe("Margherita");
    expect(stored?.provenance).toBe("user_added");
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

describe("menu source-file deletion (item 5)", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("removes the file and drops groups that came only from that file", () => {
    const store = seedStore();
    if (store.onboarding == null) {
      throw new Error("seed failed");
    }
    store.onboarding.menu.source_files = [
      { id: "f1", kind: "image", filename: "a.jpg", url: "/a" },
      { id: "f2", kind: "image", filename: "b.jpg", url: "/b" },
    ];
    store.onboarding.menu.groups = [
      { id: "g1", name: "From F1", items: [], provenance: "parser", source_file_ids: ["f1"] },
      { id: "g2", name: "Shared", items: [], provenance: "parser", source_file_ids: ["f1", "f2"] },
    ];

    store.deleteSourceFile("f1");

    expect(store.menu?.source_files.map((x) => x.id)).toEqual(["f2"]);
    expect(store.menu?.groups.find((x) => x.id === "g1")).toBeUndefined();
    const shared = store.menu?.groups.find((x) => x.id === "g2");
    expect(shared?.source_file_ids).toEqual(["f2"]);
  });

  it("drops the empty 'Sans catégorie' bucket once the last file is removed", () => {
    const store = seedStore();
    if (store.onboarding == null) {
      throw new Error("seed failed");
    }
    store.onboarding.menu.source_files = [{ id: "f1", kind: "image", filename: "a.jpg", url: "/a" }];
    store.onboarding.menu.groups = [
      { id: "g1", name: "Entrées", items: [], provenance: "parser", source_file_ids: ["f1"] },
      { id: "guncat", name: UNCATEGORIZED_GROUP_NAME, items: [], provenance: "parser", source_file_ids: [] },
    ];

    store.deleteSourceFile("f1");

    expect(store.menu?.source_files.length).toBe(0);
    expect(store.menu?.groups.length).toBe(0);
  });

  it("keeps the empty bucket while at least one file remains", () => {
    const store = seedStore();
    if (store.onboarding == null) {
      throw new Error("seed failed");
    }
    store.onboarding.menu.source_files = [
      { id: "f1", kind: "image", filename: "a.jpg", url: "/a" },
      { id: "f2", kind: "image", filename: "b.jpg", url: "/b" },
    ];
    store.onboarding.menu.groups = [
      { id: "g1", name: "Entrées", items: [], provenance: "parser", source_file_ids: ["f1"] },
      { id: "guncat", name: UNCATEGORIZED_GROUP_NAME, items: [], provenance: "parser", source_file_ids: [] },
    ];

    store.deleteSourceFile("f1");

    expect(store.menu?.source_files.length).toBe(1);
    expect(store.menu?.groups.find((x) => x.name === UNCATEGORIZED_GROUP_NAME)).not.toBeUndefined();
  });

  it("heals an already-stuck empty bucket on load when no files remain", async () => {
    const onboarding = emptyOnboarding("test_id", "fr", "desktop");
    onboarding.menu.status = "ready";
    onboarding.menu.groups = [
      { id: "guncat", name: UNCATEGORIZED_GROUP_NAME, items: [], provenance: "parser", source_file_ids: [] },
    ];
    vi.mocked(fetchOnboarding).mockResolvedValue(onboarding);

    const store = useOnboardingStore();
    await store.load("test_id");

    expect(store.menu?.groups.length).toBe(0);
  });
});
