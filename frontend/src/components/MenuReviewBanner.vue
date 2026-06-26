<script setup lang="ts">
import { useI18n } from "vue-i18n";

interface MenuReviewBannerProps {
  count: number;
  sortToReview: boolean;
  onToggleSort: (value: boolean) => void;
  onOpenQueue: () => void;
}

const props = defineProps<MenuReviewBannerProps>();

const { t } = useI18n();

function toggleSort(): void {
  props.onToggleSort(!props.sortToReview);
}
</script>

<template>
  <div v-if="count > 0" class="card flex flex-col gap-3 border-amber-200 bg-amber-50/70 p-4 sm:flex-row sm:items-center sm:justify-between">
    <div class="flex items-center gap-3">
      <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.5a1 1 0 0 1 1.8 0l7 12.5A1 1 0 0 1 17 16.5H3a1 1 0 0 1-.9-1.5l7-12.5ZM10 7a.9.9 0 0 0-.9.9v3a.9.9 0 0 0 1.8 0v-3A.9.9 0 0 0 10 7Z" /></svg>
      </span>
      <p class="font-semibold text-amber-900">
        {{ count }} {{ t("menu.reviewBanner", count) }}
      </p>
    </div>
    <div class="flex items-center gap-2">
      <label class="flex cursor-pointer items-center gap-2 text-xs font-medium text-amber-800">
        <input type="checkbox" class="h-4 w-4 rounded border-amber-300 text-amber-600 focus:ring-amber-300" :checked="sortToReview" @change="toggleSort" />
        {{ t("menu.sortToReview") }}
      </label>
      <button type="button" class="btn-primary bg-amber-500 px-4 py-2 text-sm hover:bg-amber-600 focus:ring-amber-200" @click="onOpenQueue">
        {{ t("menu.reviewOpen") }}
      </button>
    </div>
  </div>
</template>
