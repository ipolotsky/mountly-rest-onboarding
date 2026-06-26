<script setup lang="ts">
import { useI18n } from "vue-i18n";

interface ItemConflictChipProps {
  mineValue: string;
  reparseValue: string;
  onKeepMine: () => void;
  onUseReparse: () => void;
}

defineProps<ItemConflictChipProps>();

const { t } = useI18n();
</script>

<template>
  <div class="flex flex-col gap-2 rounded-lg border border-summit-200 bg-summit-50/50 p-2.5 text-xs">
    <div class="flex items-center justify-between gap-2">
      <span class="truncate text-slate-600">{{ mineValue }}</span>
      <button type="button" class="shrink-0 rounded-full bg-white px-2.5 py-1 font-semibold text-summit-700 shadow-sm" @click="onKeepMine">
        {{ t("menu.keepMine") }}
      </button>
    </div>
    <div class="flex items-center justify-between gap-2">
      <span class="truncate text-slate-600">{{ reparseValue }}</span>
      <button type="button" class="shrink-0 rounded-full bg-white px-2.5 py-1 font-semibold text-summit-700 shadow-sm" @click="onUseReparse">
        {{ t("menu.useReparse") }}
      </button>
    </div>
  </div>
</template>
