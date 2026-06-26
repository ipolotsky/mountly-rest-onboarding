<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { MenuGroup } from "@/types/contract";

interface MoveItemPickerProps {
  groups: MenuGroup[];
  currentGroupId: string;
  onMove: (targetGroupId: string) => void;
  onClose: () => void;
}

defineProps<MoveItemPickerProps>();

const { t } = useI18n();
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-4" @click.self="onClose">
    <div class="w-full max-w-xs rounded-t-2xl bg-white p-4 shadow-xl sm:rounded-2xl">
      <header class="mb-3 flex items-center justify-between">
        <h3 class="font-bold text-summit-900">{{ t("menu.addSection") }}</h3>
        <button type="button" class="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 hover:bg-summit-50" @click="onClose">
          <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </header>
      <ul class="space-y-1">
        <li v-for="group in groups" :key="group.id">
          <button
            type="button"
            class="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition hover:bg-summit-50 disabled:cursor-default disabled:opacity-40"
            :disabled="group.id === currentGroupId"
            @click="onMove(group.id)"
          >
            <span class="font-medium text-slate-700">{{ group.name }}</span>
            <span class="text-xs text-slate-400">{{ t("menu.itemCount", group.items.length) }}</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
