<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { FunnelEntry } from "@/types/contract";

interface FunnelChartProps {
  data: FunnelEntry[];
}

const props = defineProps<FunnelChartProps>();

const { t, te } = useI18n();

function stageLabel(step: string): string {
  const key = `admin.funnelStages.${step}`;
  return te(key) ? t(key) : step;
}

const maxTotal = computed(() => {
  let max = 1;
  for (const entry of props.data) {
    const total = entry.mobile + entry.desktop;
    if (total > max) {
      max = total;
    }
  }
  return max;
});

function widthPercent(value: number): number {
  return Math.round((value / maxTotal.value) * 100);
}
</script>

<template>
  <div>
    <div class="mb-3 flex items-center gap-4 text-xs font-medium text-slate-500">
      <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm bg-summit-500"></span>{{ t("admin.mobile") }}</span>
      <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm bg-summit-300"></span>{{ t("admin.desktop") }}</span>
    </div>
    <ul class="space-y-2.5">
      <li v-for="entry in data" :key="entry.step">
        <div class="mb-1 flex items-center justify-between text-sm">
          <span class="font-medium text-slate-700">{{ stageLabel(entry.step) }}</span>
          <span class="text-xs text-slate-400">{{ entry.mobile + entry.desktop }}</span>
        </div>
        <div class="flex h-6 w-full overflow-hidden rounded-lg bg-summit-50">
          <div
            class="h-full bg-summit-500 transition-all"
            :style="{ width: `${widthPercent(entry.mobile)}%` }"
            :title="`${t('admin.mobile')}: ${entry.mobile}`"
          ></div>
          <div
            class="h-full bg-summit-300 transition-all"
            :style="{ width: `${widthPercent(entry.desktop)}%` }"
            :title="`${t('admin.desktop')}: ${entry.desktop}`"
          ></div>
        </div>
      </li>
    </ul>
  </div>
</template>
