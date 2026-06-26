<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import ConsentCheckbox from "@/components/ConsentCheckbox.vue";
import ResumeBanner from "@/components/ResumeBanner.vue";
import { useOnboarding } from "@/composables/useOnboarding";

const { t } = useI18n();
const router = useRouter();
const onboarding = useOnboarding();

const consent = ref(false);
const starting = ref(false);

const hasSavedSession = computed(() => onboarding.store.hasSavedSession);

const docs = computed(() => [
  { key: "legal", label: t("start.docLegal"), icon: "doc" },
  { key: "banking", label: t("start.docBanking"), icon: "bank" },
  { key: "menu", label: t("start.docMenu"), icon: "menu" },
]);

function setConsent(value: boolean): void {
  consent.value = value;
}

async function begin(): Promise<void> {
  if (!consent.value || starting.value) {
    return;
  }
  starting.value = true;
  await onboarding.startFresh();
  void router.push({ name: "legal" });
}

async function resume(): Promise<void> {
  starting.value = true;
  await onboarding.ensureSession();
  const step = onboarding.onboarding.value?.step ?? 1;
  const target = step >= 4 ? "restaurant" : step === 3 ? "menu" : step === 2 ? "banking" : "legal";
  void router.push({ name: target });
}

function startOver(): void {
  onboarding.store.clearSession();
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 py-8 sm:py-12">
    <ResumeBanner v-if="hasSavedSession" :on-resume="resume" :on-fresh="startOver" class="mb-8" />

    <section class="text-center">
      <span class="inline-flex items-center gap-2 rounded-full bg-summit-100 px-3 py-1 text-xs font-semibold text-summit-700">
        <svg class="h-3.5 w-3.5" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4 19 11 7l3 5 2-3 4 10Z" /></svg>
        {{ t("app.tagline") }}
      </span>
      <h1 class="mt-4 text-3xl font-extrabold tracking-tight text-summit-900 sm:text-4xl">
        {{ t("start.title") }}
      </h1>
      <p class="mx-auto mt-3 max-w-xl text-base text-slate-600">
        {{ t("start.subtitle") }}
      </p>
    </section>

    <section class="mt-8">
      <p class="mb-3 text-center text-sm font-semibold uppercase tracking-wide text-slate-400">
        {{ t("start.whatYouNeed") }}
      </p>
      <div class="grid grid-cols-3 gap-3">
        <div v-for="doc in docs" :key="doc.key" class="card flex flex-col items-center gap-2 p-4 text-center">
          <span class="flex h-11 w-11 items-center justify-center rounded-xl bg-summit-50 text-summit-600">
            <svg v-if="doc.icon === 'doc'" class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 3h7l4 4v14H7Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M14 3v4h4M9 12h6M9 16h4" />
            </svg>
            <svg v-else-if="doc.icon === 'bank'" class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 9 12 4l8 5M5 9v9m14-9v9M9 9v9m6-9v9M3 21h18" />
            </svg>
            <svg v-else class="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 4h14v16H5Z M8 8h8M8 12h8M8 16h5" />
            </svg>
          </span>
          <span class="text-xs font-medium text-slate-600">{{ doc.label }}</span>
        </div>
      </div>
    </section>

    <section class="mt-8 space-y-4">
      <div class="card border-summit-200 bg-summit-50/40 p-4">
        <p class="text-sm leading-relaxed text-slate-700">{{ t("start.consentBody") }}</p>
      </div>
      <ConsentCheckbox :value="consent" :on-change="setConsent" />
    </section>

    <section class="mt-6">
      <button type="button" class="btn-primary w-full py-3.5 text-base" :disabled="!consent || starting" @click="begin">
        {{ t("start.cta") }}
      </button>
    </section>

    <section class="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-slate-500">
      <span class="inline-flex items-center gap-1.5">
        <svg class="h-4 w-4 text-summit-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M7 11V8a5 5 0 0 1 10 0v3M5 11h14v9H5Z" />
        </svg>
        {{ t("start.trustLock") }}
      </span>
      <span class="inline-flex items-center gap-1.5">
        <svg class="h-4 w-4 text-summit-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12l-1 13H7L6 7Zm3 0V5a3 3 0 0 1 6 0v2" />
        </svg>
        {{ t("start.trustDelete") }}
      </span>
    </section>
  </div>
</template>
