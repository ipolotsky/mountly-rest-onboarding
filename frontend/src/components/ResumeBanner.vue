<script setup lang="ts">
import { useI18n } from "vue-i18n";

interface ResumeBannerProps {
  onResume: () => void;
  onFresh: () => void;
}

defineProps<ResumeBannerProps>();

const { t } = useI18n();
</script>

<template>
  <div class="card flex flex-col gap-3 border-summit-200 bg-summit-50/70 p-4 sm:flex-row sm:items-center sm:justify-between">
    <div class="flex items-start gap-3">
      <span class="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-summit-100 text-summit-700">
        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M10 3a7 7 0 1 0 6.9 8.3 1 1 0 0 0-2-.4A5 5 0 1 1 10 5v2l3.5-3L10 1Z" />
        </svg>
      </span>
      <div>
        <p class="font-semibold text-summit-900">{{ t("start.resumeTitle") }}</p>
        <p class="text-sm text-slate-600">{{ t("start.resumeBody") }}</p>
      </div>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <button type="button" class="btn-ghost px-3 py-2 text-xs" @click="onFresh">{{ t("start.resumeFresh") }}</button>
      <button type="button" class="btn-primary px-4 py-2 text-sm" @click="onResume">{{ t("start.resumeContinue") }}</button>
    </div>
  </div>
</template>
