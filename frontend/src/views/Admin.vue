<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { AdminFeedbackRow, AdminMetrics, AdminOnboardingRow } from "@/types/contract";
import { fetchAdminFeedback, fetchAdminMetrics, fetchAdminOnboardings } from "@/api/client";
import { formatDuration } from "@/domain/duration";
import FunnelChart from "@/components/charts/FunnelChart.vue";
import TtvHistogram from "@/components/charts/TtvHistogram.vue";
import StatusPill from "@/components/StatusPill.vue";

const { t, te } = useI18n();
const router = useRouter();

const metrics = ref<AdminMetrics | null>(null);
const rows = ref<AdminOnboardingRow[]>([]);
const feedback = ref<AdminFeedbackRow[]>([]);
const loading = ref(true);

const eurFormatter = new Intl.NumberFormat("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const dateFormatter = new Intl.DateTimeFormat("fr-FR", { dateStyle: "medium", timeStyle: "short" });

onMounted(async () => {
  // Load the three panels independently so one failing endpoint never blanks the dashboard.
  const [metricsResult, rowsResult, feedbackResult] = await Promise.allSettled([
    fetchAdminMetrics(),
    fetchAdminOnboardings(),
    fetchAdminFeedback(),
  ]);
  metrics.value = metricsResult.status === "fulfilled" ? metricsResult.value : null;
  rows.value = rowsResult.status === "fulfilled" ? rowsResult.value : [];
  feedback.value = feedbackResult.status === "fulfilled" ? feedbackResult.value : [];
  loading.value = false;
});

const hasData = computed(() => metrics.value != null || rows.value.length > 0 || feedback.value.length > 0);

const ttvValues = computed<number[]>(() => {
  return rows.value.filter((x) => x.ttv_ms != null).map((x) => x.ttv_ms ?? 0);
});

function formatEur(value: number): string {
  return `${eurFormatter.format(value)} €`;
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

function openResult(id: string): void {
  void router.push({ name: "restaurant", query: { id: id } });
}

function openOnboarding(row: AdminOnboardingRow): void {
  openResult(row.id);
}

function formatDate(iso: string): string {
  return dateFormatter.format(new Date(iso));
}

function csatClass(csat: number | null): string {
  if (csat == null) {
    return "bg-slate-100 text-slate-500";
  }
  if (csat <= 2) {
    return "bg-rose-100 text-rose-700";
  }
  if (csat === 3) {
    return "bg-amber-100 text-amber-700";
  }
  return "bg-emerald-100 text-emerald-700";
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
                  <td class="py-2">
                    <StatusPill v-if="entry.top_reason != null" :status="entry.top_reason" kind="reason" />
                    <span v-else class="text-slate-400">—</span>
                  </td>
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

        <section class="card overflow-hidden p-0">
          <div class="border-b border-summit-50 px-5 py-4">
            <h2 class="text-base font-bold text-summit-900">{{ t("admin.feedbackTitle") }}</h2>
            <p class="mt-0.5 text-xs text-slate-400">{{ t("admin.feedbackHint") }}</p>
          </div>
          <ul v-if="feedback.length > 0" class="divide-y divide-summit-50">
            <li
              v-for="entry in feedback"
              :key="entry.id + entry.submitted_at"
              class="cursor-pointer px-5 py-4 transition-colors hover:bg-summit-50/50"
              :title="t('admin.openOnboarding')"
              @click="openResult(entry.id)"
            >
              <div class="flex flex-wrap items-center gap-2.5">
                <span class="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-sm font-bold" :class="csatClass(entry.csat)">
                  {{ entry.csat ?? "—" }}
                </span>
                <span class="font-mono text-xs text-summit-700">{{ entry.id.slice(0, 8) }}</span>
                <StatusPill :status="entry.status" kind="onboarding" />
                <span class="ml-auto text-xs text-slate-400">{{ formatDate(entry.submitted_at) }}</span>
              </div>
              <dl v-if="entry.helped != null || entry.improve != null" class="mt-2.5 space-y-2 text-sm">
                <div v-if="entry.helped != null">
                  <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ t("restaurant.feedbackQ1") }}</dt>
                  <dd class="text-slate-700">{{ entry.helped }}</dd>
                </div>
                <div v-if="entry.improve != null">
                  <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ t("restaurant.feedbackQ2") }}</dt>
                  <dd class="text-slate-700">{{ entry.improve }}</dd>
                </div>
              </dl>
              <p v-else class="mt-2 text-xs italic text-slate-400">{{ t("admin.feedbackNoText") }}</p>
            </li>
          </ul>
          <p v-else class="px-5 py-8 text-center text-sm text-slate-400">{{ t("admin.feedbackEmpty") }}</p>
        </section>
      </div>
    </div>
  </div>
</template>
