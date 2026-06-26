<script setup lang="ts">
import { nextTick, ref } from "vue";
import { useI18n } from "vue-i18n";

interface AddItemGhostRowProps {
  onAdd: (name: string) => void;
}

const props = defineProps<AddItemGhostRowProps>();

const { t } = useI18n();

const draft = ref("");
const inputElement = ref<HTMLInputElement | null>(null);

async function commit(keepFocus: boolean): Promise<void> {
  const trimmed = draft.value.trim();
  if (trimmed.length === 0) {
    return;
  }
  props.onAdd(trimmed);
  draft.value = "";
  if (keepFocus) {
    await nextTick();
    inputElement.value?.focus();
  }
}
</script>

<template>
  <div class="flex items-center gap-2 rounded-xl border border-dashed border-summit-200 px-3 py-2 transition focus-within:border-summit-400 focus-within:bg-summit-50/40">
    <svg class="h-4 w-4 shrink-0 text-summit-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
      <path stroke-linecap="round" d="M12 5v14M5 12h14" />
    </svg>
    <input
      ref="inputElement"
      v-model="draft"
      type="text"
      class="flex-1 border-0 bg-transparent p-0 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-0"
      :placeholder="t('menu.addItem')"
      @keydown.enter.prevent="commit(true)"
      @blur="commit(false)"
    />
  </div>
</template>
