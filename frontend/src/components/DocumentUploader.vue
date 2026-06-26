<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";

interface DocumentUploaderProps {
  onFiles: (files: File[]) => void;
  prompt: string;
  hint?: string;
  multiple?: boolean;
  hasDocument?: boolean;
}

const props = defineProps<DocumentUploaderProps>();

const { t } = useI18n();

const dragging = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const cameraInput = ref<HTMLInputElement | null>(null);

function emitFiles(fileList: FileList | null): void {
  if (fileList == null || fileList.length === 0) {
    return;
  }
  const files: File[] = [];
  for (let i = 0; i < fileList.length; i += 1) {
    const file = fileList.item(i);
    if (file != null) {
      files.push(file);
    }
  }
  if (files.length > 0) {
    props.onFiles(files);
  }
}

function onInputChange(event: Event): void {
  const target = event.target as HTMLInputElement;
  emitFiles(target.files);
  target.value = "";
}

function onDrop(event: DragEvent): void {
  event.preventDefault();
  dragging.value = false;
  emitFiles(event.dataTransfer?.files ?? null);
}

function openFilePicker(): void {
  fileInput.value?.click();
}

function openCamera(): void {
  cameraInput.value?.click();
}

defineExpose({ openFilePicker });
</script>

<template>
  <div>
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      accept="image/*,application/pdf"
      :multiple="multiple ?? false"
      @change="onInputChange"
    />
    <input
      ref="cameraInput"
      type="file"
      class="hidden"
      accept="image/*"
      capture="environment"
      :multiple="multiple ?? false"
      @change="onInputChange"
    />

    <div
      v-if="!hasDocument"
      class="flex flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed px-6 py-10 text-center transition"
      :class="dragging ? 'border-summit-400 bg-summit-50' : 'border-summit-200 bg-white'"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop="onDrop"
    >
      <span class="flex h-14 w-14 items-center justify-center rounded-2xl bg-summit-100 text-summit-600">
        <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0L7 9m5-5 5 5" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 17v2a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-2" />
        </svg>
      </span>
      <div>
        <p class="text-base font-semibold text-slate-800">{{ prompt }}</p>
        <p v-if="hint" class="mt-1 text-sm text-slate-500">{{ hint }}</p>
      </div>
      <div class="flex flex-wrap items-center justify-center gap-2">
        <button type="button" class="btn-primary px-4 py-2.5 text-sm sm:hidden" @click="openCamera">
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" />
            <circle cx="12" cy="13" r="3" />
          </svg>
          {{ t("uploader.takePhoto") }}
        </button>
        <button type="button" class="btn-soft px-4 py-2.5 text-sm" @click="openFilePicker">
          {{ t("uploader.chooseFile") }}
        </button>
      </div>
    </div>

    <div v-else class="flex flex-wrap items-center gap-2">
      <button type="button" class="btn-soft px-4 py-2 text-sm" @click="openFilePicker">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v6h6M20 20v-6h-6" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M5.5 9a7 7 0 0 1 12-2.5M18.5 15a7 7 0 0 1-12 2.5" />
        </svg>
        {{ t("uploader.replace") }}
      </button>
      <button type="button" class="btn-ghost px-3 py-2 text-sm sm:hidden" @click="openCamera">
        {{ t("uploader.takePhoto") }}
      </button>
    </div>
  </div>
</template>
