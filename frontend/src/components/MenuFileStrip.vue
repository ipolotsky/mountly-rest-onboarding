<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import type { SourceFile } from "@/types/contract";
import { apiBaseUrl } from "@/api/client";

interface MenuFileStripProps {
  files: SourceFile[];
  onAdd: (files: File[]) => void;
  onRemove: (fileId: string) => void;
}

const props = defineProps<MenuFileStripProps>();

const { t } = useI18n();

const fileInput = ref<HTMLInputElement | null>(null);

function resolveUrl(file: SourceFile): string {
  if (file.url.startsWith("http") || file.url.startsWith("blob:") || file.url.startsWith("data:")) {
    return file.url;
  }
  if (file.url.startsWith("/api")) {
    const origin = apiBaseUrl.replace(/\/api$/, "");
    return origin + file.url;
  }
  return file.url;
}

function openPicker(): void {
  fileInput.value?.click();
}

function onInputChange(event: Event): void {
  const target = event.target as HTMLInputElement;
  const list = target.files;
  if (list != null && list.length > 0) {
    const files: File[] = [];
    for (let i = 0; i < list.length; i += 1) {
      const file = list.item(i);
      if (file != null) {
        files.push(file);
      }
    }
    if (files.length > 0) {
      props.onAdd(files);
    }
  }
  target.value = "";
}
</script>

<template>
  <div>
    <input
      ref="fileInput"
      type="file"
      class="hidden"
      accept="image/*,application/pdf"
      multiple
      @change="onInputChange"
    />
    <div class="flex flex-wrap gap-2">
      <div
        v-for="file in files"
        :key="file.id"
        class="group relative flex w-20 flex-col items-center gap-1"
      >
        <div class="relative h-20 w-20 overflow-hidden rounded-xl border border-summit-100 bg-summit-50">
          <img v-if="file.kind === 'image'" :src="resolveUrl(file)" :alt="file.filename" class="h-full w-full object-cover" />
          <span v-else class="flex h-full w-full items-center justify-center text-summit-500">
            <svg class="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 3h7l4 4v14H7Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M14 3v4h4" />
              <text x="12" y="17" text-anchor="middle" font-size="5" fill="currentColor" stroke="none">PDF</text>
            </svg>
          </span>
          <button
            type="button"
            class="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-slate-900/70 text-white transition hover:bg-rose-600"
            :aria-label="t('menu.removeFile')"
            @click="onRemove(file.id)"
          >
            <svg class="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
          </button>
        </div>
        <span class="w-full truncate text-center text-[10px] text-slate-500" :title="file.filename">{{ file.filename }}</span>
      </div>

      <button
        type="button"
        class="flex h-20 w-20 flex-col items-center justify-center gap-1 rounded-xl border-2 border-dashed border-summit-200 text-summit-600 transition hover:border-summit-300 hover:bg-summit-50"
        @click="openPicker"
      >
        <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg>
        <span class="text-[10px] font-semibold">{{ t("menu.addFile") }}</span>
      </button>
    </div>
  </div>
</template>
