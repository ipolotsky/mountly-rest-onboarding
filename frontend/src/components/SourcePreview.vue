<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { SourceFile } from "@/types/contract";
import { apiBaseUrl } from "@/api/client";

interface SourcePreviewProps {
  files: SourceFile[];
}

const props = defineProps<SourcePreviewProps>();

const { t } = useI18n();

const activeIndex = ref(0);
const zoom = ref(1);

const activeFile = computed<SourceFile | null>(() => props.files[activeIndex.value] ?? null);

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

function setActive(index: number): void {
  activeIndex.value = index;
  zoom.value = 1;
}

function zoomIn(): void {
  zoom.value = Math.min(zoom.value + 0.25, 3);
}

function zoomOut(): void {
  zoom.value = Math.max(zoom.value - 0.25, 1);
}
</script>

<template>
  <div class="flex h-full flex-col">
    <div v-if="files.length === 0" class="flex flex-1 items-center justify-center rounded-2xl border border-dashed border-summit-200 bg-summit-50/40 p-8 text-center text-sm text-slate-400">
      {{ t("menu.viewDocument") }}
    </div>

    <template v-else>
      <div class="flex items-center justify-between gap-2 pb-2">
        <div v-if="files.length > 1" class="flex flex-wrap gap-1">
          <button
            v-for="(file, i) in files"
            :key="file.id"
            type="button"
            class="rounded-lg px-2.5 py-1 text-xs font-semibold transition"
            :class="i === activeIndex ? 'bg-summit-600 text-white' : 'bg-summit-50 text-summit-700'"
            @click="setActive(i)"
          >
            {{ i + 1 }}
          </button>
        </div>
        <div class="ml-auto flex items-center gap-1">
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-lg bg-summit-50 text-summit-700" @click="zoomOut">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M5 12h14" /></svg>
          </button>
          <button type="button" class="flex h-7 w-7 items-center justify-center rounded-lg bg-summit-50 text-summit-700" @click="zoomIn">
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M12 5v14M5 12h14" /></svg>
          </button>
        </div>
      </div>

      <div class="flex-1 overflow-auto rounded-2xl border border-summit-100 bg-slate-50">
        <div class="flex min-h-full items-start justify-center p-2">
          <iframe
            v-if="activeFile?.kind === 'pdf'"
            :src="resolveUrl(activeFile)"
            class="h-[70vh] w-full rounded-lg border-0 bg-white"
            title="document"
          ></iframe>
          <img
            v-else-if="activeFile != null"
            :src="resolveUrl(activeFile)"
            :alt="activeFile.filename"
            class="origin-top rounded-lg transition-transform"
            :style="{ transform: `scale(${zoom})` }"
          />
        </div>
      </div>
    </template>
  </div>
</template>
