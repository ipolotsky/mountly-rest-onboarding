<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { formatDuration } from "@/domain/duration";

interface Bucket {
  key: string;
  max: number;
  count: number;
}

interface TtvHistogramProps {
  values: number[];
}

const BUCKETS: { key: string; max: number }[] = [
  { key: "lt2m", max: 120_000 },
  { key: "2to5m", max: 300_000 },
  { key: "5to10m", max: 600_000 },
  { key: "gt10m", max: Number.POSITIVE_INFINITY },
];

const props = defineProps<TtvHistogramProps>();

const { t } = useI18n();

const buckets = computed<Bucket[]>(() => {
  const counts = BUCKETS.map((bucket) => ({ key: bucket.key, max: bucket.max, count: 0 }));
  for (const value of props.values) {
    const bucket = counts.find((x) => value < x.max);
    if (bucket != null) {
      bucket.count += 1;
    }
  }
  return counts;
});

const maxCount = computed(() => {
  let max = 1;
  for (const bucket of buckets.value) {
    if (bucket.count > max) {
      max = bucket.count;
    }
  }
  return max;
});

const median = computed(() => percentile(0.5));
const p90 = computed(() => percentile(0.9));

function percentile(fraction: number): number | null {
  if (props.values.length === 0) {
    return null;
  }
  const sorted = [...props.values].sort((a, b) => a - b);
  const index = Math.min(Math.ceil(fraction * sorted.length) - 1, sorted.length - 1);
  return sorted[Math.max(index, 0)] ?? null;
}

function barHeight(count: number): number {
  return Math.round((count / maxCount.value) * 100);
}
</script>

<template>
  <div>
    <p v-if="values.length === 0" class="py-10 text-center text-sm text-slate-400">{{ t("admin.ttvNone") }}</p>
    <div v-else>
      <div class="flex h-44 items-end gap-3">
        <div v-for="bucket in buckets" :key="bucket.key" class="flex flex-1 flex-col items-center justify-end">
          <span class="mb-1 text-sm font-semibold text-summit-700">{{ bucket.count }}</span>
          <div class="flex w-full items-end" style="height: 132px">
            <div class="w-full rounded-t-md bg-summit-400 transition-all" :style="{ height: `${barHeight(bucket.count)}%` }"></div>
          </div>
          <span class="mt-2 text-center text-xs text-slate-500">{{ t(`admin.ttvBuckets.${bucket.key}`) }}</span>
        </div>
      </div>
      <p class="mt-3 border-t border-summit-50 pt-2 text-xs text-slate-500">
        {{ t("admin.ttvMedian") }} <span class="font-semibold text-slate-700">{{ formatDuration(median) }}</span>
        <span class="mx-2 text-slate-300">·</span>
        {{ t("admin.ttvP90") }} <span class="font-semibold text-slate-700">{{ formatDuration(p90) }}</span>
        <span class="mx-2 text-slate-300">·</span>
        n = {{ values.length }}
      </p>
    </div>
  </div>
</template>
