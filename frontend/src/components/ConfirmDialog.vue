<script setup lang="ts">
import { useI18n } from "vue-i18n";

interface ConfirmDialogProps {
  open: boolean;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  confirmLabel?: string;
  danger?: boolean;
}

const props = defineProps<ConfirmDialogProps>();

const { t } = useI18n();

function confirm(): void {
  props.onConfirm();
}
</script>

<template>
  <transition name="fade">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-end justify-center bg-slate-900/40 p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      @click.self="onCancel"
    >
      <div class="w-full max-w-sm rounded-t-2xl bg-white p-5 shadow-xl sm:rounded-2xl">
        <p class="text-base font-semibold text-slate-900">{{ message }}</p>
        <div class="mt-5 flex justify-end gap-2">
          <button type="button" class="btn-ghost px-4 py-2.5 text-sm" @click="onCancel">
            {{ t("common.cancel") }}
          </button>
          <button
            type="button"
            class="btn px-5 py-2.5 text-sm text-white focus:ring-4"
            :class="danger === false ? 'bg-summit-600 hover:bg-summit-700 focus:ring-summit-200' : 'bg-rose-600 hover:bg-rose-700 focus:ring-rose-200'"
            @click="confirm"
          >
            {{ confirmLabel ?? t("common.remove") }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
