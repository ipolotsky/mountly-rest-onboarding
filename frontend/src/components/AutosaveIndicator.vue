<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { SaveState } from "@/stores/onboarding";

interface AutosaveIndicatorProps {
  state: SaveState;
}

const props = defineProps<AutosaveIndicatorProps>();

const { t } = useI18n();

const label = computed(() => {
  if (props.state === "saving") {
    return t("common.saving");
  }
  if (props.state === "error") {
    return t("errors.generic");
  }
  return t("common.saved");
});

const visible = computed(() => props.state !== "idle");
</script>

<template>
  <transition name="fade">
    <span
      v-if="visible"
      class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium"
      :class="
        props.state === 'error'
          ? 'bg-rose-50 text-rose-700'
          : 'bg-emerald-50 text-emerald-700'
      "
    >
      <svg
        v-if="props.state === 'saving'"
        class="h-3.5 w-3.5 animate-spin"
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8v3a5 5 0 0 0-5 5H4Z" />
      </svg>
      <svg v-else-if="props.state === 'saved'" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fill-rule="evenodd"
          d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z"
          clip-rule="evenodd"
        />
      </svg>
      {{ label }}
    </span>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
