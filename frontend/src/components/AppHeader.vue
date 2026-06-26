<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { Locale } from "@/types/contract";
import { setLocale } from "@/i18n";

const { t, locale } = useI18n();
const router = useRouter();

const activeLocale = computed<Locale>(() => locale.value as Locale);

function switchLocale(next: Locale): void {
  setLocale(next);
}

function goHome(): void {
  void router.push({ name: "start" });
}
</script>

<template>
  <header class="sticky top-0 z-30 border-b border-summit-100 bg-white/85 backdrop-blur">
    <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
      <button type="button" class="flex items-center gap-2" @click="goHome">
        <span class="flex h-8 w-8 items-center justify-center rounded-lg bg-summit-600">
          <svg viewBox="0 0 32 32" class="h-5 w-5" aria-hidden="true">
            <path d="M5 24 L13 10 L17 18 L20 13 L27 24 Z" fill="#fff" />
            <path d="M11 14 L13 10 L15.5 14 Z" fill="#c2d8eb" />
          </svg>
        </span>
        <span class="text-base font-bold tracking-tight text-summit-800">{{ t("app.name") }}</span>
      </button>

      <div class="flex items-center gap-1 rounded-full border border-summit-100 bg-summit-50 p-0.5 text-xs font-semibold">
        <button
          type="button"
          class="rounded-full px-3 py-1 transition"
          :class="activeLocale === 'fr' ? 'bg-white text-summit-700 shadow-sm' : 'text-slate-500'"
          @click="switchLocale('fr')"
        >
          FR
        </button>
        <button
          type="button"
          class="rounded-full px-3 py-1 transition"
          :class="activeLocale === 'en' ? 'bg-white text-summit-700 shadow-sm' : 'text-slate-500'"
          @click="switchLocale('en')"
        >
          EN
        </button>
      </div>
    </div>
  </header>
</template>
