<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { BlockStatus } from "@/types/contract";

type BadgeVariant = "ready" | "verified" | "couldnt_parse";

interface StatusBadgesProps {
  status: BlockStatus;
  verified?: boolean;
}

const props = defineProps<StatusBadgesProps>();

const { t } = useI18n();

const variant = computed<BadgeVariant>(() => {
  if (props.status === "couldnt_parse" || props.status === "empty") {
    return "couldnt_parse";
  }
  if (props.verified === true) {
    return "verified";
  }
  return "ready";
});

const label = computed(() => {
  if (variant.value === "verified") {
    return t("restaurant.statusVerified");
  }
  if (variant.value === "couldnt_parse") {
    return t("restaurant.statusCouldntParse");
  }
  return t("restaurant.statusReady");
});
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
    :class="{
      'bg-emerald-50 text-emerald-700': variant === 'ready' || variant === 'verified',
      'bg-slate-100 text-slate-500': variant === 'couldnt_parse',
    }"
  >
    <svg v-if="variant !== 'couldnt_parse'" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path fill-rule="evenodd" d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm4.7 6.3-5.5 5.5a1 1 0 0 1-1.4 0l-2.5-2.5a1 1 0 1 1 1.4-1.4l1.8 1.8 4.8-4.8a1 1 0 1 1 1.4 1.4Z" clip-rule="evenodd" />
    </svg>
    <svg v-else class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
      <path d="M10 2a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm.9 11.5a.9.9 0 1 1-1.8 0 .9.9 0 0 1 1.8 0ZM9.1 6a.9.9 0 0 1 1.8 0v3.8a.9.9 0 0 1-1.8 0V6Z" />
    </svg>
    {{ label }}
  </span>
</template>
