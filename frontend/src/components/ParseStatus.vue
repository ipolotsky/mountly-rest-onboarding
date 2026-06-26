<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { BlockStatus } from "@/types/contract";

export type ReviewState = "clean" | "low_confidence";

interface ParseStatusProps {
  status: BlockStatus;
  reviewState?: ReviewState;
  parsingCount?: number;
  onReplace?: () => void;
  onManual?: () => void;
}

const props = defineProps<ParseStatusProps>();

const { t } = useI18n();

const isParsing = computed(() => props.status === "parsing");
const isError = computed(() => props.status === "couldnt_parse");
const isReady = computed(() => props.status === "ready");
const isLowConfidence = computed(() => isReady.value && props.reviewState === "low_confidence");
</script>

<template>
  <div v-if="isParsing" class="card flex items-center gap-3 border-summit-200 bg-summit-50/60 p-4">
    <svg class="h-5 w-5 animate-spin text-summit-600" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v3a5 5 0 0 0-5 5H4Z" />
    </svg>
    <p class="text-sm font-medium text-summit-800">{{ t("parse.reading", parsingCount ?? 1) }}</p>
  </div>

  <div v-else-if="isError" class="card flex flex-col gap-3 border-rose-200 bg-rose-50/70 p-4">
    <div class="flex items-start gap-3">
      <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-rose-100 text-rose-600">
        <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm.9 11.5a.9.9 0 1 1-1.8 0 .9.9 0 0 1 1.8 0ZM9.1 6a.9.9 0 0 1 1.8 0v3.8a.9.9 0 0 1-1.8 0V6Z" />
        </svg>
      </span>
      <p class="text-sm font-medium text-rose-800">{{ t("parse.errorTitle") }}</p>
    </div>
    <div class="flex flex-wrap gap-2 pl-11">
      <button v-if="onReplace" type="button" class="btn-soft px-4 py-2 text-sm" @click="onReplace">{{ t("uploader.replace") }}</button>
      <button v-if="onManual" type="button" class="btn-ghost px-4 py-2 text-sm" @click="onManual">{{ t("parse.manualEntry") }}</button>
    </div>
  </div>

  <div v-else-if="isLowConfidence" class="card flex items-start gap-3 border-amber-200 bg-amber-50/70 p-4">
    <span class="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-600">
      <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path d="M9.1 2.5a1 1 0 0 1 1.8 0l7 12.5A1 1 0 0 1 17 16.5H3a1 1 0 0 1-.9-1.5l7-12.5ZM10 7a.9.9 0 0 0-.9.9v3a.9.9 0 0 0 1.8 0v-3A.9.9 0 0 0 10 7Zm0 6.4a.95.95 0 1 0 0 1.9.95.95 0 0 0 0-1.9Z" />
      </svg>
    </span>
    <div>
      <p class="text-sm font-semibold text-amber-900">{{ t("parse.lowConfTitle") }}</p>
      <p class="text-sm text-amber-800/80">{{ t("parse.lowConfBody") }}</p>
    </div>
  </div>

  <div v-else-if="isReady" class="card flex items-center gap-3 border-emerald-200 bg-emerald-50/70 p-4">
    <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
      <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fill-rule="evenodd"
          d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z"
          clip-rule="evenodd"
        />
      </svg>
    </span>
    <p class="text-sm font-semibold text-emerald-900">{{ t("parse.cleanTitle") }}</p>
  </div>
</template>
