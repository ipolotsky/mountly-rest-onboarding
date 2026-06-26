<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { AdminMetrics, AdminOnboardingRow } from "@/types/contract";
import { fetchAdminMetrics, fetchAdminOnboardings } from "@/api/client";
import { formatDuration } from "@/domain/duration";
import FunnelChart from "@/components/charts/FunnelChart.vue";
import TtvHistogram from "@/components/charts/TtvHistogram.vue";
import StatusPill from "@/components/StatusPill.vue";

const { t, te } = useI18n();
const router = useRouter();

const metrics = ref<AdminMetrics | null>(null);
const rows = ref<AdminOnboardingRow[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const [loadedMetrics, loadedRows] = await Promise.all([fetchAdminMetrics(), fetchAdminOnboardings()]);
    metrics.value = loadedMetrics;
    rows.value = loadedRows;
  } catch {
    metrics.value = null;
    rows.value = [];
  } finally {
    loading.value = false;
  }
});

const hasData = computed(() => metrics.value != null || rows.value.length > 0);

const ttvValues = computed<number[]>(() => {
  return rows.value.filter((x) => x.ttv_ms != null).map((x) => x.ttv_ms ?? 0);
});

function formatEur(value: number): string {
  return `${value.toFixed(3)} €`;
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)} %`;
}

function modelEntries(record: Record<string, number>): { key: string; value: number }[] {
  return Object.keys(record).map((key) => ({ key: key, value: record[key] ?? 0 }));
}

function stepLabel(key: string): string {
  const stepKey = `admin.stepNames.${key}`;
  if (te(stepKey)) {
    return t(stepKey);
  }
  const stageKey = `admin.funnelStages.${key}`;
  if (te(stageKey)) {
    return t(stageKey);
  }
  return key;
}

function openOnboarding(row: AdminOnboardingRow): void {
  void router.push({ name: "restaurant", query: { id: row.id } });
}
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-4 py-8">
      <header class="mb-6">
        <h1 class="text-2xl font-extrabold tracking-tight text-summit-900">{{ t("admin.title") }}</h1>
        <p class="text-sm text-slate-500">{{ t("admin.subtitle") }}</p>
      </header>

      <p v-if="loading" class="text-sm text-slate-400">{{ t("common.loading") }}</p>
      <p v-else-if="!hasData" class="rounded-xl border border-dashed border-summit-200 px-4 py-8 text-center text-sm text-slate-400">
        {{ t("admin.none") }}
      </p>

      <div v-else class="space-y-5">
        <section class="card p-5">
          <h2 class="mb-1 text-base font-bold text-summit-900">{{ t("admin.funnelTitle") }}</h2>
          <p class="mb-4 text-xs text-slate-400">{{ t("admin.funnelHint") }}</p>
          <FunnelChart v-if="metrics != null" :data="metrics.funnel" />
        </section>

        <div class="grid gap-5 lg:grid-cols-2">
          <section v-if="metrics != null" class="card p-5">
            <h2 class="mb-4 text-base font-bold text-summit-900">{{ t("admin.aiEconomicsTitle") }}</h2>
            <p class="mb-3 flex items-baseline justify-between">
              <span class="text-sm text-slate-500">{{ t("admin.perPublishable") }}</span>
              <span class="text-2xl font-extrabold text-summit-700">{{ formatEur(metrics.ai_cost.per_publishable_eur) }}</span>
            </p>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t("admin.byModel") }}</p>
                <ul class="space-y-1">
                  <li v-for="entry in modelEntries(metrics.ai_cost.by_model)" :key="entry.key" class="flex justify-between">
                    <span class="truncate text-slate-600">{{ entry.key }}</span>
                    <span class="font-medium text-slate-800">{{ formatEur(entry.value) }}</span>
                  </li>
                </ul>
              </div>
              <div>
                <p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t("admin.byStep") }}</p>
                <ul class="space-y-1">
                  <li v-for="entry in modelEntries(metrics.ai_cost.by_step)" :key="entry.key" class="flex justify-between">
                    <span class="truncate text-slate-600">{{ stepLabel(entry.key) }}</span>
                    <span class="font-medium text-slate-800">{{ formatEur(entry.value) }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <section v-if="metrics != null" class="card p-5">
            <h2 class="mb-1 text-base font-bold text-summit-900">{{ t("admin.frictionTitle") }}</h2>
            <p class="mb-3 text-xs text-slate-400">{{ t("admin.frictionHint") }}</p>
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-summit-100 text-left text-xs uppercase tracking-wide text-slate-400">
                  <th class="pb-2 font-semibold">{{ t("admin.colStep") }}</th>
                  <th class="pb-2 font-semibold">{{ t("admin.colDropOff") }}</th>
                  <th class="pb-2 font-semibold">{{ t("admin.colReason") }}</th>
                  <th class="pb-2 text-right font-semibold">{{ t("admin.colMedian") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="entry in metrics.friction" :key="entry.step" class="border-b border-summit-50 last:border-0">
                  <td class="py-2 font-medium text-slate-700">{{ stepLabel(entry.step) }}</td>
                  <td class="py-2 text-slate-600">{{ formatPercent(entry.drop_off) }}</td>
                  <td class="py-2 text-slate-500">{{ entry.top_reason ?? "—" }}</td>
                  <td class="py-2 text-right text-slate-600">{{ formatDuration(entry.median_ms) }}</td>
                </tr>
              </tbody>
            </table>
          </section>
        </div>

        <section class="card p-5">
          <h2 class="mb-1 text-base font-bold text-summit-900">{{ t("admin.ttvTitle") }}</h2>
          <p class="mb-4 text-xs text-slate-400">{{ t("admin.ttvHint") }}</p>
          <TtvHistogram :values="ttvValues" />
        </section>

        <section class="card overflow-hidden p-0">
          <h2 class="border-b border-summit-50 px-5 py-4 text-base font-bold text-summit-900">{{ t("admin.onboardingsTitle") }}</h2>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-summit-100 bg-summit-50/40 text-left text-xs uppercase tracking-wide text-slate-400">
                  <th class="px-4 py-2 font-semibold">{{ t("admin.colId") }}</th>
                  <th class="px-4 py-2 font-semibold">{{ t("admin.colStatus") }}</th>
                  <th class="px-4 py-2 font-semibold">{{ t("admin.colDevice") }}</th>
                  <th class="px-4 py-2 text-right font-semibold">{{ t("admin.colTtv") }}</th>
                  <th class="px-4 py-2 text-right font-semibold">{{ t("admin.colCost") }}</th>
                  <th class="px-4 py-2 font-semibold">{{ t("admin.colRegistry") }}</th>
                  <th class="px-4 py-2 text-right font-semibold">{{ t("admin.colCsat") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in rows"
                  :key="row.id"
                  class="cursor-pointer border-b border-summit-50 transition-colors last:border-0 hover:bg-summit-50/50"
                  :title="t('admin.openOnboarding')"
                  @click="openOnboarding(row)"
                >
                  <td class="px-4 py-2 font-mono text-xs text-summit-700">{{ row.id.slice(0, 8) }}</td>
                  <td class="px-4 py-2"><StatusPill :status="row.status" kind="onboarding" /></td>
                  <td class="px-4 py-2">
                    <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="row.device === 'mobile' ? 'bg-summit-100 text-summit-700' : 'bg-slate-100 text-slate-600'">
                      {{ row.device === "mobile" ? t("admin.mobile") : t("admin.desktop") }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-right text-slate-600">{{ formatDuration(row.ttv_ms) }}</td>
                  <td class="px-4 py-2 text-right text-slate-600">{{ formatEur(row.ai_cost_eur) }}</td>
                  <td class="px-4 py-2">
                    <StatusPill v-if="row.registry_status != null" :status="row.registry_status" kind="registry" />
                    <span v-else class="text-slate-400">—</span>
                  </td>
                  <td class="px-4 py-2 text-right text-slate-600">{{ row.csat ?? "—" }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>
