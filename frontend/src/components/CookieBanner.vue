<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";

const STORAGE_KEY = "cookie_consent";

const { t } = useI18n();

const visible = ref(localStorage.getItem(STORAGE_KEY) == null);

function accept(): void {
  localStorage.setItem(STORAGE_KEY, "1");
  visible.value = false;
}
</script>

<template>
  <transition name="cookie">
    <div
      v-if="visible"
      class="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-2.5 rounded-xl border border-summit-100 bg-white/95 px-3 py-2 text-xs text-slate-600 shadow-lg ring-1 ring-black/5 backdrop-blur sm:left-4 sm:right-auto sm:mx-0"
      role="region"
      :aria-label="t('cookies.label')"
    >
      <svg class="h-4 w-4 shrink-0 text-summit-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 3a9 9 0 1 0 9 9 3 3 0 0 1-3-3 3 3 0 0 1-3-3 3 3 0 0 1-3-3Z" />
        <circle cx="9" cy="12" r="0.7" fill="currentColor" stroke="none" />
        <circle cx="13.5" cy="15" r="0.7" fill="currentColor" stroke="none" />
        <circle cx="14" cy="10" r="0.7" fill="currentColor" stroke="none" />
      </svg>
      <span class="flex-1">{{ t("cookies.message") }}</span>
      <button type="button" class="btn-primary shrink-0 px-3 py-1 text-xs" @click="accept">
        {{ t("cookies.accept") }}
      </button>
    </div>
  </transition>
</template>

<style scoped>
.cookie-enter-active,
.cookie-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.cookie-enter-from,
.cookie-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
