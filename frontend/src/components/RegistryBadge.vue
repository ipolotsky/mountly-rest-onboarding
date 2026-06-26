<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { RegistryInfo } from "@/types/contract";

interface RegistryBadgeProps {
  registry: RegistryInfo | null;
}

const props = defineProps<RegistryBadgeProps>();

const { t } = useI18n();

const variant = computed<"match" | "no_match" | "unavailable" | null>(() => {
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
</script>

<template>
  <span
    v-if="variant != null"
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
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
  </span>
</template>
