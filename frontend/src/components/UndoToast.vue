<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

interface UndoToastProps {
  message: string | null;
  onUndo: () => void;
  onDismiss: () => void;
  timeoutMs?: number;
}

const props = defineProps<UndoToastProps>();

const { t } = useI18n();

const timer = ref<ReturnType<typeof setTimeout> | null>(null);

function clearTimer(): void {
  if (timer.value != null) {
    clearTimeout(timer.value);
    timer.value = null;
  }
}

function startTimer(): void {
  clearTimer();
  timer.value = setTimeout(() => {
    props.onDismiss();
  }, props.timeoutMs ?? 6000);
}

function undo(): void {
  clearTimer();
  props.onUndo();
}

watch(
  () => props.message,
  (value) => {
    if (value != null) {
      startTimer();
    } else {
      clearTimer();
    }
  },
);

onBeforeUnmount(() => {
  clearTimer();
});
</script>

<template>
  <transition name="toast">
    <div
      v-if="message != null"
      class="fixed inset-x-0 bottom-4 z-50 mx-auto flex w-fit max-w-[92vw] items-center gap-4 rounded-xl bg-slate-900 px-4 py-3 text-sm text-white shadow-lg safe-bottom"
      role="status"
    >
      <span>{{ message }}</span>
      <button type="button" class="font-semibold text-summit-200 hover:text-white" @click="undo">
        {{ t("common.undo") }}
      </button>
    </div>
  </transition>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
