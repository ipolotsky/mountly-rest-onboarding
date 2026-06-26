<script setup lang="ts">
import { nextTick, ref } from "vue";
import { useI18n } from "vue-i18n";

interface AddSectionCardProps {
  onAdd: (name: string) => void;
}

const props = defineProps<AddSectionCardProps>();

const { t } = useI18n();

const editing = ref(false);
const draft = ref("");
const inputElement = ref<HTMLInputElement | null>(null);

async function startEditing(): Promise<void> {
  editing.value = true;
  await nextTick();
  inputElement.value?.focus();
}

function commit(): void {
  const trimmed = draft.value.trim();
  editing.value = false;
  draft.value = "";
  props.onAdd(trimmed.length > 0 ? trimmed : t("menu.newSection"));
}

function cancel(): void {
  editing.value = false;
  draft.value = "";
}
</script>

<template>
  <div>
    <button
      v-if="!editing"
      type="button"
      class="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-summit-200 bg-white/50 px-4 py-4 text-sm font-semibold text-summit-700 transition hover:border-summit-300 hover:bg-summit-50"
      @click="startEditing"
    >
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg>
      {{ t("menu.addSection") }}
    </button>
    <div v-else class="flex items-center gap-2 rounded-2xl border-2 border-summit-300 bg-white p-3">
      <input
        ref="inputElement"
        v-model="draft"
        type="text"
        class="input-field py-2"
        :placeholder="t('menu.newSection')"
        @keydown.enter.prevent="commit"
        @keydown.esc.prevent="cancel"
      />
      <button type="button" class="btn-primary px-4 py-2 text-sm" @click="commit">{{ t("common.save") }}</button>
    </div>
  </div>
</template>
