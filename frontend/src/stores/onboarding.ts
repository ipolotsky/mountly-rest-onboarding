import { defineStore } from "pinia";
import type {
  BankingBlock,
  BankingFieldName,
  Device,
  LegalBlock,
  LegalFieldName,
  Locale,
  MenuBlock,
  MenuGroup,
  MenuItem,
  Onboarding,
  PriceVariant,
  Step,
} from "@/types/contract";
import {
  createOnboarding,
  fetchOnboarding,
  parseBanking as apiParseBanking,
  parseLegal as apiParseLegal,
  parseMenu as apiParseMenu,
  saveBanking as apiSaveBanking,
  saveLegal as apiSaveLegal,
  saveMenu as apiSaveMenu,
  confirmStep as apiConfirmStep,
} from "@/api/client";
import {
  UNCATEGORIZED_GROUP_NAME,
  emptyMenuGroup,
  emptyMenuItem,
  emptyOnboarding,
  userField,
} from "@/domain/factory";

const ONBOARDING_ID_KEY = "onboarding_id";

export type SaveState = "idle" | "saving" | "saved" | "error";

interface RemovedGroupSnapshot {
  group: MenuGroup;
  movedItemIds: string[];
}

interface ParsedSnapshots {
  legal: LegalBlock | null;
  banking: BankingBlock | null;
  menu: MenuBlock | null;
}

interface OnboardingStoreState {
  onboarding: Onboarding | null;
  loading: boolean;
  parsing: boolean;
  saveState: SaveState;
  error: string | null;
  lastRemovedGroup: RemovedGroupSnapshot | null;
  parsedSnapshots: ParsedSnapshots;
}

function deepClone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function storedOnboardingId(): string | null {
  return localStorage.getItem(ONBOARDING_ID_KEY);
}

function persistOnboardingId(id: string): void {
  localStorage.setItem(ONBOARDING_ID_KEY, id);
}

function findGroup(menu: MenuBlock, groupId: string): MenuGroup | null {
  return menu.groups.find((x) => x.id === groupId) ?? null;
}

function findItem(group: MenuGroup, itemId: string): MenuItem | null {
  return group.items.find((x) => x.id === itemId) ?? null;
}

function ensureUncategorized(menu: MenuBlock): MenuGroup {
  const existing = menu.groups.find((x) => x.name === UNCATEGORIZED_GROUP_NAME);
  if (existing != null) {
    return existing;
  }
  const bucket = emptyMenuGroup(UNCATEGORIZED_GROUP_NAME);
  menu.groups.push(bucket);
  return bucket;
}

export const useOnboardingStore = defineStore("onboarding", {
  state: (): OnboardingStoreState => ({
    onboarding: null,
    loading: false,
    parsing: false,
    saveState: "idle",
    error: null,
    lastRemovedGroup: null,
    parsedSnapshots: { legal: null, banking: null, menu: null },
  }),

  getters: {
    hasSavedSession(): boolean {
      return storedOnboardingId() != null;
    },
    onboardingId(state): string | null {
      return state.onboarding?.id ?? null;
    },
    locale(state): Locale {
      return state.onboarding?.locale ?? "fr";
    },
    legal(state): LegalBlock | null {
      return state.onboarding?.legal ?? null;
    },
    banking(state): BankingBlock | null {
      return state.onboarding?.banking ?? null;
    },
    menu(state): MenuBlock | null {
      return state.onboarding?.menu ?? null;
    },
    menuReviewCount(state): number {
      const menu = state.onboarding?.menu;
      if (menu == null) {
        return 0;
      }
      let count = 0;
      for (const group of menu.groups) {
        for (const item of group.items) {
          if (item.name.status === "low_confidence" || item.description.status === "low_confidence") {
            count += 1;
          }
        }
      }
      return count;
    },
  },

  actions: {
    async ensureSession(locale: Locale, device: Device): Promise<string> {
      const existing = storedOnboardingId();
      if (existing != null) {
        await this.load(existing);
        if (this.onboarding != null) {
          return existing;
        }
      }
      return this.startFresh(locale, device);
    },

    async startFresh(locale: Locale, device: Device): Promise<string> {
      this.error = null;
      try {
        const created = await createOnboarding(locale, device);
        persistOnboardingId(created.id);
        this.onboarding = emptyOnboarding(created.id, locale, device);
        return created.id;
      } catch {
        const fallbackId = `local_${Date.now().toString(36)}`;
        persistOnboardingId(fallbackId);
        this.onboarding = emptyOnboarding(fallbackId, locale, device);
        this.error = null;
        return fallbackId;
      }
    },

    async load(id: string): Promise<void> {
      this.loading = true;
      this.error = null;
      try {
        const onboarding = await fetchOnboarding(id);
        this.onboarding = onboarding;
      } catch {
        this.onboarding = null;
        this.error = "loadFailed";
      } finally {
        this.loading = false;
      }
    },

    clearSession(): void {
      localStorage.removeItem(ONBOARDING_ID_KEY);
      this.onboarding = null;
    },

    async parseLegal(files: File[], note: string | null): Promise<boolean> {
      if (this.onboarding == null) {
        return false;
      }
      this.parsing = true;
      this.onboarding.legal.status = "parsing";
      try {
        const block = await apiParseLegal(this.onboarding.id, files, note);
        this.onboarding.legal = block;
        this.parsedSnapshots.legal = deepClone(block);
        return block.status !== "couldnt_parse";
      } catch {
        this.onboarding.legal.status = "couldnt_parse";
        return false;
      } finally {
        this.parsing = false;
      }
    },

    editLegalField(name: LegalFieldName, value: string | null): void {
      if (this.onboarding == null) {
        return;
      }
      this.onboarding.legal.fields[name] = userField(value);
      void this.persistLegal();
    },

    async persistLegal(): Promise<void> {
      if (this.onboarding == null) {
        return;
      }
      await this.runSave(async () => {
        const block = await apiSaveLegal(this.onboarding!.id, this.onboarding!.legal);
        this.onboarding!.legal = block;
      });
    },

    async parseBanking(files: File[], note: string | null): Promise<boolean> {
      if (this.onboarding == null) {
        return false;
      }
      this.parsing = true;
      this.onboarding.banking.status = "parsing";
      try {
        const block = await apiParseBanking(this.onboarding.id, files, note);
        this.onboarding.banking = block;
        this.parsedSnapshots.banking = deepClone(block);
        return block.status !== "couldnt_parse";
      } catch {
        this.onboarding.banking.status = "couldnt_parse";
        return false;
      } finally {
        this.parsing = false;
      }
    },

    editBankingField(name: BankingFieldName, value: string | null): void {
      if (this.onboarding == null) {
        return;
      }
      this.onboarding.banking.fields[name] = userField(value);
      void this.persistBanking();
    },

    async persistBanking(): Promise<void> {
      if (this.onboarding == null) {
        return;
      }
      await this.runSave(async () => {
        const block = await apiSaveBanking(this.onboarding!.id, this.onboarding!.banking);
        this.onboarding!.banking = block;
      });
    },

    async parseMenu(files: File[], note: string | null): Promise<boolean> {
      if (this.onboarding == null) {
        return false;
      }
      this.parsing = true;
      this.onboarding.menu.status = "parsing";
      try {
        const block = await apiParseMenu(this.onboarding.id, files, note);
        this.onboarding.menu = block;
        this.parsedSnapshots.menu = deepClone(block);
        return block.status !== "couldnt_parse";
      } catch {
        this.onboarding.menu.status = "couldnt_parse";
        return false;
      } finally {
        this.parsing = false;
      }
    },

    async persistMenu(): Promise<void> {
      if (this.onboarding == null) {
        return;
      }
      await this.runSave(async () => {
        const block = await apiSaveMenu(this.onboarding!.id, this.onboarding!.menu);
        this.onboarding!.menu = block;
      });
    },

    addGroup(name: string): MenuGroup | null {
      if (this.onboarding == null) {
        return null;
      }
      const group = emptyMenuGroup(name.length > 0 ? name : UNCATEGORIZED_GROUP_NAME);
      this.onboarding.menu.groups.push(group);
      void this.persistMenu();
      return group;
    },

    renameGroup(groupId: string, name: string): void {
      if (this.onboarding == null) {
        return;
      }
      const group = findGroup(this.onboarding.menu, groupId);
      if (group == null || group.name === UNCATEGORIZED_GROUP_NAME) {
        return;
      }
      group.name = name;
      void this.persistMenu();
    },

    removeGroup(groupId: string): void {
      if (this.onboarding == null) {
        return;
      }
      const menu = this.onboarding.menu;
      const group = findGroup(menu, groupId);
      if (group == null || group.name === UNCATEGORIZED_GROUP_NAME) {
        return;
      }
      const bucket = ensureUncategorized(menu);
      const movedItemIds = group.items.map((x) => x.id);
      bucket.items.push(...group.items);
      this.lastRemovedGroup = { group: { ...group, items: [] }, movedItemIds: movedItemIds };
      menu.groups = menu.groups.filter((x) => x.id !== groupId);
      void this.persistMenu();
    },

    undoRemoveGroup(): void {
      if (this.onboarding == null || this.lastRemovedGroup == null) {
        return;
      }
      const menu = this.onboarding.menu;
      const snapshot = this.lastRemovedGroup;
      const bucket = menu.groups.find((x) => x.name === UNCATEGORIZED_GROUP_NAME);
      const restoredItems: MenuItem[] = [];
      if (bucket != null) {
        for (const id of snapshot.movedItemIds) {
          const item = findItem(bucket, id);
          if (item != null) {
            restoredItems.push(item);
          }
        }
        bucket.items = bucket.items.filter((x) => !snapshot.movedItemIds.includes(x.id));
      }
      const restoredGroup: MenuGroup = { ...snapshot.group, items: restoredItems };
      menu.groups.push(restoredGroup);
      this.lastRemovedGroup = null;
      void this.persistMenu();
    },

    addItem(groupId: string): MenuItem | null {
      if (this.onboarding == null) {
        return null;
      }
      const group = findGroup(this.onboarding.menu, groupId);
      if (group == null) {
        return null;
      }
      const item = emptyMenuItem();
      group.items.push(item);
      void this.persistMenu();
      return item;
    },

    removeItem(groupId: string, itemId: string): void {
      if (this.onboarding == null) {
        return;
      }
      const group = findGroup(this.onboarding.menu, groupId);
      if (group == null) {
        return;
      }
      group.items = group.items.filter((x) => x.id !== itemId);
      void this.persistMenu();
    },

    editItemName(groupId: string, itemId: string, value: string | null): void {
      this.mutateItem(groupId, itemId, (item) => {
        item.name = userField(value);
      });
    },

    editItemDescription(groupId: string, itemId: string, value: string | null): void {
      this.mutateItem(groupId, itemId, (item) => {
        item.description = userField(value);
      });
    },

    setItemPrices(groupId: string, itemId: string, prices: PriceVariant[]): void {
      this.mutateItem(groupId, itemId, (item) => {
        item.prices = prices;
        item.provenance = "user_edited";
      });
    },

    acceptItem(groupId: string, itemId: string): void {
      this.mutateItem(groupId, itemId, (item) => {
        if (item.name.status === "low_confidence") {
          item.name.status = "present";
        }
        if (item.description.status === "low_confidence") {
          item.description.status = "present";
        }
        item.provenance = "user_confirmed";
      });
    },

    mutateItem(groupId: string, itemId: string, mutator: (item: MenuItem) => void): void {
      if (this.onboarding == null) {
        return;
      }
      const group = findGroup(this.onboarding.menu, groupId);
      if (group == null) {
        return;
      }
      const item = findItem(group, itemId);
      if (item == null) {
        return;
      }
      mutator(item);
      void this.persistMenu();
    },

    async confirm(step: Step): Promise<void> {
      if (this.onboarding == null) {
        return;
      }
      try {
        const updated = await apiConfirmStep(this.onboarding.id, step);
        this.onboarding = updated;
      } catch {
        if (step === 1) {
          this.onboarding.confirmed.legal = true;
        } else if (step === 2) {
          this.onboarding.confirmed.banking = true;
        } else if (step === 3) {
          this.onboarding.confirmed.menu = true;
        }
        const nextStep = Math.min(step + 1, 4) as Step;
        this.onboarding.step = nextStep;
      }
    },

    async runSave(operation: () => Promise<void>): Promise<void> {
      this.saveState = "saving";
      try {
        await operation();
        this.saveState = "saved";
      } catch {
        this.saveState = "error";
      }
    },
  },
});
