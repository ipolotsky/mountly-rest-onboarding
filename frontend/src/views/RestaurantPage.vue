<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRoute, useRouter } from "vue-router";
import type { Field, FeedbackPayload, LegalFieldName } from "@/types/contract";
import { useOnboarding } from "@/composables/useOnboarding";
import { publishOnboarding, submitFeedback } from "@/api/client";
import StatusBadges from "@/components/StatusBadges.vue";
import MenuDisplay from "@/components/MenuDisplay.vue";
import FeedbackForm from "@/components/FeedbackForm.vue";

const LEGAL_ORDER: LegalFieldName[] = [
  "legal_name",
  "siren",
  "siret",
  "legal_form",
  "registered_address",
  "legal_representative",
];

const BANKING_ORDER = ["account_holder", "bank_name", "iban", "bic"] as const;

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const onboarding = useOnboarding();

const copied = ref(false);
const publishing = ref(false);
const feedbackJustSubmitted = ref(false);
const notFound = ref(false);

const sharedId = computed(() => {
  const value = route.query.id;
  return typeof value === "string" && value.length > 0 ? value : null;
});
const readOnly = computed(() => sharedId.value != null);

onMounted(async () => {
  // A shared link or an admin deep-link ( /restaurant?id=… ) opens a specific onboarding
  // read-only: load it by id without touching the visitor's own session or analytics.
  if (sharedId.value != null) {
    await onboarding.load(sharedId.value);
    notFound.value = onboarding.onboarding.value == null;
    return;
  }
  await onboarding.ensureSession();
  onboarding.track("step_viewed", { step: 4 });
});

const data = computed(() => onboarding.onboarding.value);
const legal = computed(() => data.value?.legal ?? null);
const banking = computed(() => data.value?.banking ?? null);
const menu = computed(() => data.value?.menu ?? null);

const published = computed(() => data.value?.published === true);
const feedbackSubmitted = computed(() => data.value?.feedback_submitted === true || feedbackJustSubmitted.value);

const restaurantName = computed(() => legal.value?.fields.legal_name.value ?? t("common.placeholder"));
const address = computed(() => legal.value?.fields.registered_address.value ?? t("common.placeholder"));
const registryVerified = computed(() => legal.value?.registry?.status === "match");

function fieldValue(field: Field | undefined): string {
  if (field == null || field.value == null || field.value.length === 0) {
    return t("common.placeholder");
  }
  return field.value;
}

function isMissing(field: Field | undefined): boolean {
  return field == null || field.value == null || field.value.length === 0;
}

function editListing(): void {
  void router.push({ name: "legal" });
}

async function publish(): Promise<void> {
  const id = data.value?.id;
  if (id == null || publishing.value || published.value) {
    return;
  }
  publishing.value = true;
  try {
    const updated = await publishOnboarding(id);
    onboarding.store.onboarding = updated;
  } catch {
    // Publishing gates link sharing and reads back from the server by id; if the call
    // fails, stay unpublished so we never offer a shareable link the server didn't publish.
  } finally {
    publishing.value = false;
  }
}

async function copyLink(): Promise<void> {
  if (!published.value) {
    return;
  }
  const id = data.value?.id ?? "";
  const url = `${window.location.origin}/restaurant?id=${id}`;
  try {
    await navigator.clipboard?.writeText(url);
    copied.value = true;
    setTimeout(() => {
      copied.value = false;
    }, 2000);
  } catch {
    copied.value = false;
  }
}

async function onFeedback(payload: FeedbackPayload): Promise<void> {
  const id = data.value?.id;
  if (id == null) {
    return;
  }
  try {
    await submitFeedback(id, payload);
  } catch {
    // Feedback failures must not block the page.
  }
  feedbackJustSubmitted.value = true;
  if (onboarding.store.onboarding != null) {
    onboarding.store.onboarding.feedback_submitted = true;
    onboarding.store.onboarding.csat = payload.csat;
  }
}
</script>

<template>
  <div v-if="notFound" class="mx-auto max-w-3xl px-4 py-20 text-center">
    <p class="text-sm text-slate-500">{{ t("errors.loadFailed") }}</p>
  </div>
  <div v-else class="pb-12">
    <header class="ridge bg-gradient-to-b from-summit-100/80 to-transparent">
      <div class="mx-auto max-w-3xl px-4 pb-8 pt-8 sm:pt-10">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-sm font-semibold text-summit-600">{{ t("restaurant.readyTitle") }}</p>
            <h1 class="mt-1 text-3xl font-extrabold tracking-tight text-summit-900 sm:text-4xl" :class="{ 'italic text-slate-400': isMissing(legal?.fields.legal_name) }">
              {{ restaurantName }}
            </h1>
            <p class="mt-1 flex items-center gap-1.5 text-sm" :class="isMissing(legal?.fields.registered_address) ? 'italic text-slate-400' : 'text-slate-600'">
              <svg class="h-4 w-4 shrink-0 text-summit-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 21s-6-5.3-6-10a6 6 0 0 1 12 0c0 4.7-6 10-6 10Z" /><circle cx="12" cy="11" r="2" /></svg>
              {{ address }}
            </p>
          </div>
        </div>
        <p class="mt-3 text-sm text-slate-500">{{ t("restaurant.readySubtitle") }}</p>
      </div>
    </header>

    <div class="mx-auto max-w-3xl space-y-5 px-4">
      <section class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-bold text-summit-900">{{ t("restaurant.sections.legal") }}</h2>
          <StatusBadges :status="legal?.status ?? 'empty'" :verified="registryVerified" />
        </div>
        <dl class="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          <div v-for="name in LEGAL_ORDER" :key="name">
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ t(`legal.fields.${name}`) }}</dt>
            <dd class="text-sm" :class="isMissing(legal?.fields[name]) ? 'italic text-slate-400' : 'font-medium text-slate-800'">
              {{ fieldValue(legal?.fields[name]) }}
            </dd>
          </div>
        </dl>
      </section>

      <section class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-bold text-summit-900">{{ t("restaurant.sections.banking") }}</h2>
          <StatusBadges :status="banking?.status ?? 'empty'" />
        </div>
        <dl class="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          <div v-for="name in BANKING_ORDER" :key="name">
            <dt class="text-xs font-medium uppercase tracking-wide text-slate-400">{{ t(`banking.fields.${name}`) }}</dt>
            <dd class="text-sm" :class="isMissing(banking?.fields[name]) ? 'italic text-slate-400' : 'font-medium text-slate-800'">
              {{ fieldValue(banking?.fields[name]) }}
            </dd>
          </div>
        </dl>
      </section>

      <section class="card p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-base font-bold text-summit-900">{{ t("restaurant.sections.menu") }}</h2>
          <StatusBadges :status="menu?.status ?? 'empty'" />
        </div>
        <MenuDisplay v-if="menu != null" :menu="menu" />
      </section>

      <section v-if="!readOnly" class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <button type="button" class="btn-soft py-3 sm:flex-1" @click="editListing">{{ t("restaurant.editListing") }}</button>
        <button type="button" class="btn-ghost py-3 sm:flex-1" :disabled="!published" @click="copyLink">
          {{ copied ? t("restaurant.copied") : t("restaurant.copyLink") }}
        </button>
        <button type="button" class="btn-primary py-3 sm:flex-1" :disabled="published || publishing" @click="publish">
          {{ published ? t("restaurant.published") : t("restaurant.publish") }}
        </button>
      </section>

      <FeedbackForm v-if="!readOnly && !feedbackSubmitted" :on-submit="onFeedback" />
      <div
        v-else-if="!readOnly && feedbackJustSubmitted"
        class="card flex items-center gap-3 p-5 text-emerald-700 sm:p-6"
      >
        <svg class="h-6 w-6 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z" clip-rule="evenodd" /></svg>
        <p class="font-semibold">{{ t("restaurant.feedbackThanks") }}</p>
      </div>
    </div>
  </div>
</template>
