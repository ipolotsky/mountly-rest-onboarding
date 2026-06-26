<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { MenuBlock, PriceVariant } from "@/types/contract";
import { useOnboardingStore } from "@/stores/onboarding";
import { useAnalytics } from "@/composables/useAnalytics";
import { checkFiles } from "@/domain/upload";
import MenuSection from "@/components/MenuSection.vue";
import AddSectionCard from "@/components/AddSectionCard.vue";
import MenuReviewBanner from "@/components/MenuReviewBanner.vue";
import MenuFileStrip from "@/components/MenuFileStrip.vue";
import ReviewQueue from "@/components/ReviewQueue.vue";
import SourcePreview from "@/components/SourcePreview.vue";
import UndoToast from "@/components/UndoToast.vue";

const HIGHLIGHT_FADE_MS = 5000;
const TOAST_TIMEOUT_MS = 7000;

interface MenuBuilderProps {
  menu: MenuBlock;
}

const props = defineProps<MenuBuilderProps>();

const { t } = useI18n();
const store = useOnboardingStore();
const analytics = useAnalytics();

const sortToReview = ref(false);
const queueOpen = ref(false);
const sheetOpen = ref(false);
let highlightTimer: ReturnType<typeof setTimeout> | null = null;

const reviewCount = computed(() => store.menuReviewCount);
const removedToast = computed(() => (store.lastRemovedGroup != null ? t("menu.groupMoved") : null));
const duplicateToast = computed(() => (store.skippedDuplicates.length > 0 ? t("menu.duplicateSkipped") : null));
const highlights = computed(() => store.menuHighlights);
const hasSources = computed(() => props.menu.source_files.length > 0);
const isParsing = computed(() => props.menu.status === "parsing");
const isEmpty = computed(() => props.menu.groups.every((x) => x.items.length === 0) && props.menu.groups.length === 0);

watch(
  () => store.menuHighlights,
  (value) => {
    if (highlightTimer != null) {
      clearTimeout(highlightTimer);
      highlightTimer = null;
    }
    if (value.size > 0) {
      highlightTimer = setTimeout(() => {
        store.clearMenuHighlights();
      }, HIGHLIGHT_FADE_MS);
    }
  },
);

let duplicateTimer: ReturnType<typeof setTimeout> | null = null;

watch(duplicateToast, (value) => {
  if (duplicateTimer != null) {
    clearTimeout(duplicateTimer);
    duplicateTimer = null;
  }
  if (value != null) {
    duplicateTimer = setTimeout(() => {
      store.dismissSkippedDuplicates();
    }, TOAST_TIMEOUT_MS);
  }
});

async function addFiles(files: File[]): Promise<void> {
  const check = checkFiles(files);
  const onboardingId = store.onboardingId ?? "unknown";
  if (check.rejection != null) {
    analytics.track("error_shown", onboardingId, { step: 3, error_type: check.rejection });
    return;
  }
  analytics.track("reparse_requested", onboardingId, { step: 3 });
  for (let i = 0; i < files.length; i += 1) {
    const file = files[i];
    analytics.track("file_uploaded", onboardingId, { step: 3, file_type: file.type, bytes: file.size, upload_index: i });
  }
  const ok = await store.parseMenu(files, null);
  if (!ok) {
    analytics.track("error_shown", onboardingId, { step: 3, error_type: "couldnt_parse" });
  }
}

function removeFile(fileId: string): void {
  store.deleteSourceFile(fileId);
}

function dismissDuplicateToast(): void {
  store.dismissSkippedDuplicates();
}

function addGroup(name: string): void {
  store.addGroup(name);
}

function renameGroup(groupId: string, name: string): void {
  store.renameGroup(groupId, name);
}

function removeGroup(groupId: string): void {
  store.removeGroup(groupId);
}

function addItem(groupId: string, name: string): void {
  store.addItem(groupId, name);
}

function removeItem(groupId: string, itemId: string): void {
  store.removeItem(groupId, itemId);
}

function setItemName(groupId: string, itemId: string, value: string | null): void {
  store.editItemName(groupId, itemId, value);
}

function setItemDescription(groupId: string, itemId: string, value: string | null): void {
  store.editItemDescription(groupId, itemId, value);
}

function setItemPrices(groupId: string, itemId: string, value: PriceVariant[]): void {
  store.setItemPrices(groupId, itemId, value);
}

function acceptItem(groupId: string, itemId: string): void {
  store.acceptItem(groupId, itemId);
}

function undoRemove(): void {
  store.undoRemoveGroup();
}

function dismissToast(): void {
  store.lastRemovedGroup = null;
}
</script>

<template>
  <div>
    <div class="grid gap-5 lg:grid-cols-[minmax(0,40%)_minmax(0,1fr)]">
      <aside v-if="hasSources" class="hidden lg:block">
        <div class="sticky top-20">
          <SourcePreview :files="menu.source_files" />
        </div>
      </aside>

      <div class="min-w-0 space-y-4">
        <MenuFileStrip :files="menu.source_files" :on-add="addFiles" :on-remove="removeFile" :disabled="isParsing" />

        <MenuReviewBanner
          :count="reviewCount"
          :sort-to-review="sortToReview"
          :on-toggle-sort="(value) => (sortToReview = value)"
          :on-open-queue="() => (queueOpen = true)"
        />

        <p v-if="reviewCount === 0 && !isEmpty" class="rounded-xl bg-summit-50 px-4 py-2.5 text-sm text-summit-700">
          {{ t("menu.missingItems") }}
        </p>

        <p v-if="isEmpty" class="rounded-xl border border-dashed border-summit-200 px-4 py-6 text-center text-sm text-slate-400">
          {{ t("menu.emptyState") }}
        </p>

        <MenuSection
          v-for="group in menu.groups"
          :key="group.id"
          :group="group"
          :sort-to-review="sortToReview"
          :highlights="highlights"
          :on-rename="(value) => renameGroup(group.id, value)"
          :on-remove-group="() => removeGroup(group.id)"
          :on-add-item="(name) => addItem(group.id, name)"
          :on-remove-item="(itemId) => removeItem(group.id, itemId)"
          :on-item-name="(itemId, value) => setItemName(group.id, itemId, value)"
          :on-item-description="(itemId, value) => setItemDescription(group.id, itemId, value)"
          :on-item-prices="(itemId, value) => setItemPrices(group.id, itemId, value)"
        />

        <AddSectionCard :on-add="addGroup" />
      </div>
    </div>

    <button
      v-if="hasSources"
      type="button"
      class="btn-soft fixed bottom-20 right-4 z-30 shadow-md lg:hidden"
      @click="sheetOpen = true"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4 5h16v14H4Z M4 9h16" /></svg>
      {{ t("menu.viewDocument") }}
    </button>

    <transition name="sheet">
      <div v-if="sheetOpen" class="fixed inset-0 z-50 flex flex-col bg-slate-900/40 lg:hidden" @click.self="sheetOpen = false">
        <div class="mt-auto h-[85vh] rounded-t-2xl bg-white p-4">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="font-bold text-summit-900">{{ t("menu.viewDocument") }}</h3>
            <button type="button" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-summit-50" @click="sheetOpen = false">
              <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
            </button>
          </div>
          <SourcePreview :files="menu.source_files" class="h-[calc(85vh-3.5rem)]" />
        </div>
      </div>
    </transition>

    <ReviewQueue
      v-if="queueOpen"
      :groups="menu.groups"
      :on-keep="acceptItem"
      :on-remove="removeItem"
      :on-name="setItemName"
      :on-prices="setItemPrices"
      :on-close="() => (queueOpen = false)"
    />

    <UndoToast :message="removedToast" :on-undo="undoRemove" :on-dismiss="dismissToast" :timeout-ms="TOAST_TIMEOUT_MS" />

    <transition name="toast">
      <div
        v-if="duplicateToast != null"
        class="fixed inset-x-0 bottom-6 z-40 mx-auto flex w-fit max-w-[92vw] items-center gap-3 rounded-2xl border border-amber-200/80 bg-white px-4 py-3 text-sm text-slate-700 shadow-lg ring-1 ring-black/5 safe-bottom"
        role="status"
      >
        <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
          <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.5a1 1 0 0 1 1.8 0l7 12.5A1 1 0 0 1 17 16.5H3a1 1 0 0 1-.9-1.5l7-12.5ZM10 7a.9.9 0 0 0-.9.9v3a.9.9 0 0 0 1.8 0v-3A.9.9 0 0 0 10 7Zm0 6.4a.95.95 0 1 0 0 1.9.95.95 0 0 0 0-1.9Z" /></svg>
        </span>
        <span class="font-medium">{{ duplicateToast }}</span>
        <button
          type="button"
          class="ml-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
          :aria-label="t('common.cancel')"
          @click="dismissDuplicateToast"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
