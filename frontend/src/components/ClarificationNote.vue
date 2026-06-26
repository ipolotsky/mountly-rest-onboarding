<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";

interface ClarificationNoteProps {
  onSubmit: (note: string) => void;
  disabled?: boolean;
}

const props = defineProps<ClarificationNoteProps>();

const { t } = useI18n();

const open = ref(false);
const note = ref("");

function toggle(): void {
  open.value = !open.value;
}

function submit(): void {
  const trimmed = note.value.trim();
  if (trimmed.length === 0 || props.disabled === true) {
    return;
  }
  props.onSubmit(trimmed);
  note.value = "";
  open.value = false;
}
</script>

<template>
  <div>
    <button type="button" class="btn-ghost px-3 py-2 text-sm" @click="toggle">
      <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14m-7-7h14" />
      </svg>
      {{ t("uploader.addNote") }}
    </button>
    <div v-if="open" class="mt-2 flex flex-col gap-2">
      <textarea
        v-model="note"
        rows="2"
        class="input-field resize-none"
        :placeholder="t('uploader.notePlaceholder')"
      ></textarea>
      <div class="flex justify-end">
        <button
          type="button"
          class="btn-primary px-4 py-2 text-sm"
          :disabled="note.trim().length === 0 || disabled === true"
          @click="submit"
        >
          {{ t("uploader.noteSubmit") }}
        </button>
      </div>
    </div>
  </div>
</template>
