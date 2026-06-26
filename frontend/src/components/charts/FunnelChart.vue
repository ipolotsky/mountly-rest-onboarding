<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { FunnelEntry } from "@/types/contract";

interface FunnelRow {
  step: string;
  mobile: number;
  desktop: number;
  total: number;
  conversion: number;
  mobileWidth: number;
  desktopWidth: number;
  dropCount: number;
  dropPercent: number;
}

interface FunnelChartProps {
  data: FunnelEntry[];
}

const props = defineProps<FunnelChartProps>();

const { t, te } = useI18n();

function stageLabel(step: string): string {
  const key = `admin.funnelStages.${step}`;
  return te(key) ? t(key) : step;
}

const startedTotal = computed(() => {
  const first = props.data[0];
  const total = first != null ? first.mobile + first.desktop : 0;
  return total > 0 ? total : 1;
});

const frows = computed<FunnelRow[]>(() => {
  return props.data.map((entry, index) => {
    const total = entry.mobile + entry.desktop;
    const previous = index > 0 ? props.data[index - 1] : null;
    const previousTotal = previous != null ? previous.mobile + previous.desktop : total;
    const dropCount = Math.max(previousTotal - total, 0);
    return {
      step: entry.step,
      mobile: entry.mobile,
      desktop: entry.desktop,
      total: total,
      conversion: Math.round((total / startedTotal.value) * 100),
      mobileWidth: (entry.mobile / startedTotal.value) * 100,
      desktopWidth: (entry.desktop / startedTotal.value) * 100,
      dropCount: dropCount,
      dropPercent: previousTotal > 0 ? Math.round((dropCount / previousTotal) * 100) : 0,
    };
  });
});
</script>

<template>
  <div>
    <div class="mb-4 flex items-center gap-4 text-xs font-medium text-slate-500">
      <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm bg-summit-500"></span>{{ t("admin.mobile") }}</span>
      <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-sm bg-summit-300"></span>{{ t("admin.desktop") }}</span>
    </div>
    <ul>
      <li v-for="(row, index) in frows" :key="row.step">
        <p v-if="index > 0" class="py-1 text-center text-[11px] font-medium text-slate-400">
          {{ t("admin.funnelDropped", { count: row.dropCount, percent: row.dropPercent }) }}
        </p>
        <div class="mb-1 flex items-baseline justify-between text-sm">
          <span class="font-medium text-slate-700">{{ stageLabel(row.step) }}</span>
          <span class="text-slate-500">
            <span class="font-semibold text-summit-700">{{ row.total }}</span>
            <span class="ml-1.5 text-xs text-slate-400">{{ row.conversion }}% {{ t("admin.funnelOfStart") }}</span>
          </span>
        </div>
        <div class="flex h-7 w-full overflow-hidden rounded-lg bg-summit-50">
          <div class="h-full bg-summit-500 transition-all" :style="{ width: `${row.mobileWidth}%` }" :title="`${t('admin.mobile')}: ${row.mobile}`"></div>
          <div class="h-full bg-summit-300 transition-all" :style="{ width: `${row.desktopWidth}%` }" :title="`${t('admin.desktop')}: ${row.desktop}`"></div>
        </div>
      </li>
    </ul>
  </div>
</template>
