<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";

type PillKind = "onboarding" | "registry";

interface StatusPillProps {
  status: string;
  kind: PillKind;
}

const COLORS: Record<PillKind, Record<string, string>> = {
  onboarding: {
    publishable: "bg-emerald-50 text-emerald-700",
    completed: "bg-sky-50 text-sky-700",
    in_progress: "bg-amber-50 text-amber-700",
  },
  registry: {
    match: "bg-emerald-50 text-emerald-700",
    no_match: "bg-rose-50 text-rose-700",
    unavailable: "bg-slate-100 text-slate-500",
    skipped: "bg-slate-100 text-slate-500",
  },
};

const FALLBACK = "bg-slate-100 text-slate-600";

const props = defineProps<StatusPillProps>();

const { t, te } = useI18n();

const colorClass = computed(() => COLORS[props.kind][props.status] ?? FALLBACK);

const label = computed(() => {
  const key = props.kind === "registry" ? `admin.registryStatuses.${props.status}` : `admin.statuses.${props.status}`;
  return te(key) ? t(key) : props.status;
});
</script>

<template>
  <span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium" :class="colorClass">
    {{ label }}
  </span>
</template>
