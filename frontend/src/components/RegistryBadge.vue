<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { RegistryInfo } from "@/types/contract";

type RegistryVariant = "match" | "no_match" | "unavailable";

interface RegistryBadgeProps {
  registry: RegistryInfo | null;
}

const props = defineProps<RegistryBadgeProps>();

const { t } = useI18n();

const tooltipOpen = ref(false);

const variant = computed<RegistryVariant | null>(() => {
  if (props.registry == null) {
    return null;
  }
  if (props.registry.status === "match") {
    return "match";
  }
  if (props.registry.status === "no_match") {
    return "no_match";
  }
  if (props.registry.status === "unavailable") {
    return "unavailable";
  }
  return null;
});

const label = computed(() => {
  if (variant.value === "match") {
    return t("registry.verified");
  }
  if (variant.value === "no_match") {
    return t("registry.noMatch");
  }
  if (variant.value === "unavailable") {
    return t("registry.unavailable");
  }
  return "";
});

function toggleTooltip(): void {
  tooltipOpen.value = !tooltipOpen.value;
}

function closeTooltip(): void {
  tooltipOpen.value = false;
}
</script>

<template>
  <span
    v-if="variant != null"
    class="relative inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
    :class="{
      'bg-emerald-50 text-emerald-700': variant === 'match',
      'bg-amber-50 text-amber-700': variant === 'no_match',
      'bg-slate-100 text-slate-600': variant === 'unavailable',
    }"
  >
    <svg v-if="variant === 'match'" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path
        fill-rule="evenodd"
        d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm4.7 6.3-5.5 5.5a1 1 0 0 1-1.4 0l-2.5-2.5a1 1 0 1 1 1.4-1.4l1.8 1.8 4.8-4.8a1 1 0 1 1 1.4 1.4Z"
        clip-rule="evenodd"
      />
    </svg>
    <svg v-else class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M9.1 2.5a1 1 0 0 1 1.8 0l7 12.5A1 1 0 0 1 17 16.5H3a1 1 0 0 1-.9-1.5l7-12.5Z" />
    </svg>
    {{ label }}

    <button
      v-if="variant === 'match'"
      type="button"
      class="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-100 text-[10px] font-bold text-emerald-700 transition hover:bg-emerald-200"
      :aria-label="t('registry.explainLabel')"
      @click="toggleTooltip"
      @blur="closeTooltip"
      @mouseenter="tooltipOpen = true"
      @mouseleave="closeTooltip"
    >
      ?
    </button>

    <transition name="fade">
      <span
        v-if="variant === 'match' && tooltipOpen"
        role="tooltip"
        class="absolute left-0 top-full z-30 mt-2 w-64 rounded-lg bg-slate-900 px-3 py-2 text-xs font-normal leading-relaxed text-white shadow-lg"
      >
        {{ t("registry.tooltip") }}
      </span>
    </transition>
  </span>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
