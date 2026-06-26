<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { MenuGroup, MenuItem, PriceVariant } from "@/types/contract";
import PriceField from "@/components/PriceField.vue";

interface FlaggedEntry {
  groupId: string;
  groupName: string;
  item: MenuItem;
}

interface ReviewQueueProps {
  groups: MenuGroup[];
  onKeep: (groupId: string, itemId: string) => void;
  onRemove: (groupId: string, itemId: string) => void;
  onName: (groupId: string, itemId: string, value: string | null) => void;
  onPrices: (groupId: string, itemId: string, value: PriceVariant[]) => void;
  onClose: () => void;
}

const props = defineProps<ReviewQueueProps>();

const { t } = useI18n();

const cursor = ref(0);

const queue = computed<FlaggedEntry[]>(() => {
  const entries: FlaggedEntry[] = [];
  for (const group of props.groups) {
    for (const item of group.items) {
      if (item.name.status === "low_confidence" || item.description.status === "low_confidence") {
        entries.push({ groupId: group.id, groupName: group.name, item: item });
      }
    }
  }
  return entries;
});

const current = computed<FlaggedEntry | null>(() => queue.value[cursor.value] ?? null);
const total = computed(() => queue.value.length + cursor.value);
const done = computed(() => queue.value.length === 0);

watch(
  () => queue.value.length,
  (length) => {
    if (length === 0) {
      cursor.value = 0;
    }
  },
);

function keep(): void {
  if (current.value == null) {
    return;
  }
  props.onKeep(current.value.groupId, current.value.item.id);
}

function remove(): void {
  if (current.value == null) {
    return;
  }
  props.onRemove(current.value.groupId, current.value.item.id);
}

// Buffer the name locally and commit on blur, so editing never round-trips per keystroke
// (which would let the save echo jump the cursor and drop characters mid-typing).
const nameDraft = ref(current.value?.item.name.value ?? "");
const nameFocused = ref(false);

watch(
  () => current.value?.item.id,
  () => {
    nameDraft.value = current.value?.item.name.value ?? "";
  },
);

watch(
  () => current.value?.item.name.value,
  (value) => {
    if (!nameFocused.value) {
      nameDraft.value = value ?? "";
    }
  },
);

function commitName(): void {
  if (current.value == null) {
    return;
  }
  const value = nameDraft.value.length > 0 ? nameDraft.value : null;
  if (value !== (current.value.item.name.value ?? null)) {
    props.onName(current.value.groupId, current.value.item.id, value);
  }
}

function onNameBlur(): void {
  nameFocused.value = false;
  commitName();
}

function editPrices(value: PriceVariant[]): void {
  if (current.value == null) {
    return;
  }
  props.onPrices(current.value.groupId, current.value.item.id, value);
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-4" @click.self="onClose">
    <div class="w-full max-w-md rounded-t-2xl bg-white p-5 shadow-xl sm:rounded-2xl">
      <header class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-bold text-summit-900">{{ t("menu.queueTitle") }}</h2>
        <button type="button" class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 hover:bg-summit-50" :aria-label="t('common.cancel')" @click="onClose">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </header>

      <div v-if="done" class="flex flex-col items-center gap-3 py-8 text-center">
        <span class="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
          <svg class="h-7 w-7" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z" clip-rule="evenodd" /></svg>
        </span>
        <p class="font-semibold text-slate-800">{{ t("menu.queueDone") }}</p>
        <button type="button" class="btn-primary px-6 py-2.5" @click="onClose">{{ t("common.looksGood") }}</button>
      </div>

      <div v-else-if="current != null">
        <p class="mb-3 text-xs font-medium uppercase tracking-wide text-slate-400">
          {{ t("menu.queueProgress", { current: cursor + 1, total: total }) }} · {{ current.groupName }}
        </p>

        <div class="space-y-3 rounded-xl border border-amber-200 bg-amber-50/40 p-4">
          <input
            v-model="nameDraft"
            type="text"
            class="input-field"
            :placeholder="t('menu.itemName')"
            @focus="nameFocused = true"
            @blur="onNameBlur"
            @keydown.enter.prevent="commitName"
          />
          <p v-if="(current.item.description.value ?? '').length > 0" class="text-sm text-slate-500">
            {{ current.item.description.value }}
          </p>
          <PriceField :value="current.item.prices" :on-change="editPrices" />
        </div>

        <div class="mt-4 grid grid-cols-3 gap-2">
          <button type="button" class="btn-soft py-2.5 text-sm" @click="keep">{{ t("menu.queueKeep") }}</button>
          <button type="button" class="btn-soft py-2.5 text-sm" @click="keep">{{ t("menu.queueFix") }}</button>
          <button type="button" class="btn-ghost py-2.5 text-sm text-rose-600 hover:bg-rose-50" @click="remove">{{ t("menu.queueRemove") }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
