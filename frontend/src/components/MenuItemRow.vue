<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { MenuItem, PriceVariant } from "@/types/contract";
import PriceField from "@/components/PriceField.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

export type ItemHighlight = "new" | "changed" | null;

interface MenuItemRowProps {
  item: MenuItem;
  onName: (value: string | null) => void;
  onDescription: (value: string | null) => void;
  onPrices: (value: PriceVariant[]) => void;
  onRemove: () => void;
  highlight?: ItemHighlight;
}

const props = defineProps<MenuItemRowProps>();

const { t } = useI18n();

const confirmOpen = ref(false);

const isFlagged = computed(
  () => props.item.name.status === "low_confidence" || props.item.description.status === "low_confidence",
);
const isNew = computed(() => props.item.provenance === "user_added" && props.item.confidence == null && props.item.name.value == null);
const isReparseNew = computed(() => props.item.provenance === "parser" && props.item.confidence == null && props.item.name.status === "low_confidence");

const descriptionOpen = ref((props.item.description.value ?? "").length > 0);

// Edits are buffered locally and committed on blur, so typing never round-trips to the server
// per keystroke (which would jump the cursor and drop characters when the save echo lands).
const nameDraft = ref(props.item.name.value ?? "");
const nameFocused = ref(false);
const descriptionDraft = ref(props.item.description.value ?? "");
const descriptionFocused = ref(false);

watch(
  () => props.item.name.value,
  (value) => {
    if (!nameFocused.value) {
      nameDraft.value = value ?? "";
    }
  },
);

watch(
  () => props.item.description.value,
  (value) => {
    if (!descriptionFocused.value) {
      descriptionDraft.value = value ?? "";
    }
  },
);

function commitName(): void {
  const value = nameDraft.value.length > 0 ? nameDraft.value : null;
  if (value !== (props.item.name.value ?? null)) {
    props.onName(value);
  }
}

function onNameBlur(): void {
  nameFocused.value = false;
  commitName();
}

function commitDescription(): void {
  const value = descriptionDraft.value.length > 0 ? descriptionDraft.value : null;
  if (value !== (props.item.description.value ?? null)) {
    props.onDescription(value);
  }
}

function onDescriptionBlur(): void {
  descriptionFocused.value = false;
  commitDescription();
}

function toggleDescription(): void {
  descriptionOpen.value = !descriptionOpen.value;
}

function requestRemove(): void {
  confirmOpen.value = true;
}

function confirmRemove(): void {
  confirmOpen.value = false;
  props.onRemove();
}

function cancelRemove(): void {
  confirmOpen.value = false;
}
</script>

<template>
  <div
    class="rounded-xl border p-3 transition-colors duration-[1500ms]"
    :class="[
      isFlagged ? 'border-l-4 border-l-amber-400 border-summit-100' : 'border-summit-100',
      highlight === 'new' ? 'bg-emerald-50' : highlight === 'changed' ? 'bg-sky-50' : 'bg-white',
    ]"
  >
    <div class="flex items-start gap-2">
      <div class="min-w-0 flex-1 space-y-1.5">
        <div class="flex items-center gap-2">
          <input
            v-model="nameDraft"
            type="text"
            class="w-full border-0 bg-transparent p-0 text-sm font-semibold text-slate-900 placeholder:font-normal placeholder:text-slate-400 focus:outline-none focus:ring-0"
            :placeholder="t('menu.itemName')"
            @focus="nameFocused = true"
            @blur="onNameBlur"
            @keydown.enter.prevent="commitName"
          />
          <span v-if="isReparseNew" class="shrink-0 rounded-full bg-summit-100 px-2 py-0.5 text-[10px] font-semibold text-summit-700">
            {{ t("menu.newOnReparse") }}
          </span>
        </div>

        <textarea
          v-if="descriptionOpen"
          v-model="descriptionDraft"
          rows="2"
          class="w-full resize-none border-0 bg-transparent p-0 text-xs text-slate-500 placeholder:text-slate-300 focus:outline-none focus:ring-0"
          :placeholder="t('menu.itemDescription')"
          @focus="descriptionFocused = true"
          @blur="onDescriptionBlur"
        ></textarea>
        <button v-else type="button" class="text-[11px] font-medium text-summit-500 hover:text-summit-700" @click="toggleDescription">
          + {{ t("menu.itemDescription") }}
        </button>

        <PriceField :value="item.prices" :on-change="onPrices" />
      </div>

      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-300 transition hover:bg-rose-50 hover:text-rose-500"
        :aria-label="t('menu.queueRemove')"
        @click="requestRemove"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5h6v2m-7 0 1 12h6l1-12" />
        </svg>
      </button>
    </div>
    <span v-if="isNew" class="sr-only">new</span>

    <ConfirmDialog
      :open="confirmOpen"
      :message="t('menu.confirmRemoveItem')"
      :on-confirm="confirmRemove"
      :on-cancel="cancelRemove"
    />
  </div>
</template>
