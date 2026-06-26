<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { SourceFile } from "@/types/contract";
import { apiBaseUrl } from "@/api/client";

const MIN_ZOOM = 1;
const MAX_ZOOM = 4;

interface SourcePreviewProps {
  files: SourceFile[];
}

const props = defineProps<SourcePreviewProps>();

const { t } = useI18n();

const activeIndex = ref(0);
const view = reactive({ zoom: 1, x: 0, y: 0 });
const pointers = new Map<number, { x: number; y: number }>();
const drag = reactive({ active: false, startX: 0, startY: 0, originX: 0, originY: 0 });
let pinchStartDistance = 0;
let pinchStartZoom = 1;

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

function resetView(): void {
  view.zoom = 1;
  view.x = 0;
  view.y = 0;
}

function setActive(index: number): void {
  activeIndex.value = index;
  resetView();
}

function clampZoom(value: number): number {
  return Math.min(Math.max(value, MIN_ZOOM), MAX_ZOOM);
}

function applyZoom(next: number): void {
  view.zoom = clampZoom(next);
  if (view.zoom === 1) {
    view.x = 0;
    view.y = 0;
  }
}

function zoomIn(): void {
  applyZoom(view.zoom + 0.25);
}

function zoomOut(): void {
  applyZoom(view.zoom - 0.25);
}

function onWheel(event: WheelEvent): void {
  event.preventDefault();
  applyZoom(view.zoom - event.deltaY * 0.002);
}

function distanceBetween(a: { x: number; y: number }, b: { x: number; y: number }): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function onPointerDown(event: PointerEvent): void {
  (event.target as HTMLElement).setPointerCapture?.(event.pointerId);
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (pointers.size === 2) {
    const points = Array.from(pointers.values());
    pinchStartDistance = distanceBetween(points[0]!, points[1]!);
    pinchStartZoom = view.zoom;
  } else if (pointers.size === 1 && view.zoom > 1) {
    drag.active = true;
    drag.startX = event.clientX;
    drag.startY = event.clientY;
    drag.originX = view.x;
    drag.originY = view.y;
  }
}

function onPointerMove(event: PointerEvent): void {
  if (!pointers.has(event.pointerId)) {
    return;
  }
  pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

  if (pointers.size === 2 && pinchStartDistance > 0) {
    const points = Array.from(pointers.values());
    const ratio = distanceBetween(points[0]!, points[1]!) / pinchStartDistance;
    applyZoom(pinchStartZoom * ratio);
    return;
  }
  if (drag.active) {
    view.x = drag.originX + (event.clientX - drag.startX);
    view.y = drag.originY + (event.clientY - drag.startY);
  }
}

function onPointerUp(event: PointerEvent): void {
  pointers.delete(event.pointerId);
  if (pointers.size < 2) {
    pinchStartDistance = 0;
  }
  if (pointers.size === 0) {
    drag.active = false;
  }
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

      <div class="relative flex-1 overflow-hidden rounded-2xl border border-summit-100 bg-slate-50">
        <iframe
          v-if="activeFile?.kind === 'pdf'"
          :src="resolveUrl(activeFile)"
          class="h-[70vh] w-full rounded-lg border-0 bg-white"
          title="document"
        ></iframe>
        <div
          v-else-if="activeFile != null"
          class="flex h-full min-h-[50vh] touch-none items-center justify-center"
          :class="view.zoom > 1 ? 'cursor-grab' : ''"
          @wheel="onWheel"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
        >
          <img
            :src="resolveUrl(activeFile)"
            :alt="activeFile.filename"
            class="max-h-full select-none rounded-lg"
            :class="drag.active ? '' : 'transition-transform duration-150'"
            :style="{ transform: `translate(${view.x}px, ${view.y}px) scale(${view.zoom})` }"
            draggable="false"
          />
        </div>
      </div>
    </template>
  </div>
</template>
