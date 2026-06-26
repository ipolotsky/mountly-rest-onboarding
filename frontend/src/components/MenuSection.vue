<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { MenuGroup, MenuItem, PriceVariant } from "@/types/contract";
import { UNCATEGORIZED_GROUP_NAME } from "@/domain/factory";
import MenuItemRow from "@/components/MenuItemRow.vue";
import type { ItemHighlight } from "@/components/MenuItemRow.vue";
import AddItemGhostRow from "@/components/AddItemGhostRow.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";

interface MenuSectionProps {
  group: MenuGroup;
  onRename: (value: string) => void;
  onRemoveGroup: () => void;
  onAddItem: (name: string) => void;
  onRemoveItem: (itemId: string) => void;
  onItemName: (itemId: string, value: string | null) => void;
  onItemDescription: (itemId: string, value: string | null) => void;
  onItemPrices: (itemId: string, value: PriceVariant[]) => void;
  sortToReview?: boolean;
  highlights?: Map<string, ItemHighlight>;
}

const props = defineProps<MenuSectionProps>();

const { t } = useI18n();

const collapsed = ref(false);
const confirmOpen = ref(false);

function highlightFor(itemId: string): ItemHighlight {
  return props.highlights?.get(itemId) ?? null;
}

const isBucket = computed(() => props.group.name === UNCATEGORIZED_GROUP_NAME);
const itemCount = computed(() => props.group.items.length);
const flaggedCount = computed(
  () => props.group.items.filter((x) => x.name.status === "low_confidence" || x.description.status === "low_confidence").length,
);

const orderedItems = computed<MenuItem[]>(() => {
  if (props.sortToReview !== true) {
    return props.group.items;
  }
  return [...props.group.items].sort((a, b) => {
    const flagA = a.name.status === "low_confidence" || a.description.status === "low_confidence" ? 0 : 1;
    const flagB = b.name.status === "low_confidence" || b.description.status === "low_confidence" ? 0 : 1;
    return flagA - flagB;
  });
});

function onTitleInput(event: Event): void {
  props.onRename((event.target as HTMLInputElement).value);
}

function toggleCollapse(): void {
  collapsed.value = !collapsed.value;
}

function requestRemoveGroup(): void {
  confirmOpen.value = true;
}

function confirmRemoveGroup(): void {
  confirmOpen.value = false;
  props.onRemoveGroup();
}

function cancelRemoveGroup(): void {
  confirmOpen.value = false;
}
</script>

<template>
  <section class="card overflow-hidden">
    <header class="flex items-center gap-2 border-b border-summit-50 bg-summit-50/40 px-3 py-2.5">
      <button
        type="button"
        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-summit-100"
        :aria-expanded="!collapsed"
        @click="toggleCollapse"
      >
        <svg class="h-4 w-4 transition-transform" :class="{ '-rotate-90': collapsed }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="m6 9 6 6 6-6" />
        </svg>
      </button>

      <input
        type="text"
        class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base font-bold text-summit-900 placeholder:text-slate-400 focus:outline-none focus:ring-0 disabled:cursor-default"
        :value="group.name"
        :disabled="isBucket"
        :placeholder="t('menu.newSection')"
        @input="onTitleInput"
      />

      <span class="shrink-0 text-xs font-medium text-slate-400">
        {{ t("menu.itemCount", itemCount) }}
      </span>
      <span v-if="flaggedCount > 0" class="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
        {{ flaggedCount }}
      </span>

      <button
        v-if="!isBucket"
        type="button"
        class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-slate-300 hover:bg-rose-50 hover:text-rose-500"
        :aria-label="t('menu.removeGroup')"
        @click="requestRemoveGroup"
      >
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5h6v2m-7 0 1 12h6l1-12" />
        </svg>
      </button>
    </header>

    <div v-if="!collapsed" class="space-y-2 p-3">
      <MenuItemRow
        v-for="item in orderedItems"
        :key="item.id"
        :item="item"
        :highlight="highlightFor(item.id)"
        :on-name="(value) => onItemName(item.id, value)"
        :on-description="(value) => onItemDescription(item.id, value)"
        :on-prices="(value) => onItemPrices(item.id, value)"
        :on-remove="() => onRemoveItem(item.id)"
      />
      <AddItemGhostRow :on-add="onAddItem" />
    </div>

    <ConfirmDialog
      :open="confirmOpen"
      :message="t('menu.confirmRemoveSection')"
      :on-confirm="confirmRemoveGroup"
      :on-cancel="cancelRemoveGroup"
    />
  </section>
</template>
