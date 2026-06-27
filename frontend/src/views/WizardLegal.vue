<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { BlockStatus, Field, LegalFieldName } from "@/types/contract";
import { useOnboarding } from "@/composables/useOnboarding";
import { sirenReason, sirenValid, siretReason, siretValid } from "@/domain/validators";
import type { UploadRejection } from "@/domain/upload";
import WizardChrome from "@/components/WizardChrome.vue";
import DocumentUploader from "@/components/DocumentUploader.vue";
import ParseStatus from "@/components/ParseStatus.vue";
import ReviewField from "@/components/ReviewField.vue";
import RegistryBadge from "@/components/RegistryBadge.vue";
import type { ReviewState } from "@/components/ParseStatus.vue";

const FIELD_ORDER: LegalFieldName[] = [
  "legal_name",
  "siren",
  "siret",
  "legal_form",
  "registered_address",
  "legal_representative",
];

const { t } = useI18n();
const router = useRouter();
const onboarding = useOnboarding();

const manualMode = ref(false);
const uploader = ref<InstanceType<typeof DocumentUploader> | null>(null);

onMounted(async () => {
  await onboarding.ensureSession();
  onboarding.track("step_viewed", { step: 1 });
});

onUnmounted(() => {
  onboarding.store.stopParsingPoll();
});

const legal = computed(() => onboarding.legal.value);
const block = computed(() => onboarding.onboarding.value);
const hasDocument = computed(() => (legal.value?.status ?? "empty") !== "empty");
const isParsing = computed(() => legal.value?.status === "parsing");

const reviewState = computed<ReviewState>(() => {
  const fields = legal.value?.fields;
  if (fields == null) {
    return "clean";
  }
  const flagged = FIELD_ORDER.some((name) => fields[name].status === "low_confidence");
  return flagged ? "low_confidence" : "clean";
});

function effectiveField(name: LegalFieldName): Field {
  const field = legal.value?.fields[name];
  if (field == null) {
    return { value: null, status: "missing", confidence: null, provenance: "parser", valid: null };
  }
  if (name === "siren" && field.value != null) {
    return { ...field, valid: sirenValid(field.value) };
  }
  if (name === "siret" && field.value != null) {
    return { ...field, valid: siretValid(field.value) };
  }
  return field;
}

const showFields = computed(() => {
  const status = legal.value?.status ?? "empty";
  return manualMode.value || status === "ready" || status === "couldnt_parse";
});

const displayStatus = computed<BlockStatus>(() => {
  const status = legal.value?.status ?? "empty";
  if (manualMode.value && status === "couldnt_parse") {
    return "empty";
  }
  return status;
});

const canConfirm = computed(() => {
  const fields = legal.value?.fields;
  if (fields == null || legal.value?.status === "parsing") {
    return false;
  }
  const sirenOk = fields.siren.value == null || fields.siren.value.length === 0 || sirenValid(fields.siren.value);
  const siretOk = fields.siret.value == null || fields.siret.value.length === 0 || siretValid(fields.siret.value);
  return sirenOk && siretOk;
});

async function onFiles(files: File[]): Promise<void> {
  manualMode.value = false;
  onboarding.track("file_uploaded", { step: 1, file_type: files[0]?.type ?? "unknown", bytes: files[0]?.size ?? 0, upload_index: 0 });
  const ok = await onboarding.store.parseLegal(files, null);
  if (!ok) {
    onboarding.track("error_shown", { step: 1, error_type: "couldnt_parse" });
  }
}

function onReject(reason: UploadRejection): void {
  onboarding.track("error_shown", { step: 1, error_type: reason });
}

function replaceDocument(): void {
  uploader.value?.openFilePicker();
}

function editField(name: LegalFieldName, value: string | null): void {
  onboarding.store.editLegalField(name, value);
}

function enterManual(): void {
  manualMode.value = true;
}

function emitValidationResults(): void {
  const fields = legal.value?.fields;
  if (fields == null) {
    return;
  }
  if (fields.siren.value != null && fields.siren.value.length > 0) {
    onboarding.track("validation_result", { validator: "siren", passed: sirenValid(fields.siren.value), field_name: "siren" });
  }
  if (fields.siret.value != null && fields.siret.value.length > 0) {
    onboarding.track("validation_result", { validator: "siret", passed: siretValid(fields.siret.value), field_name: "siret" });
  }
}

async function confirm(): Promise<void> {
  if (!canConfirm.value) {
    return;
  }
  emitValidationResults();
  await onboarding.confirm(1);
  void router.push({ name: "banking" });
}

function fieldError(name: LegalFieldName): string | undefined {
  const value = legal.value?.fields[name]?.value ?? null;
  if (name === "siren") {
    const reason = sirenReason(value);
    return reason == null ? undefined : t(`legal.sirenError.${reason}`);
  }
  if (name === "siret") {
    const reason = siretReason(value);
    return reason == null ? undefined : t(`legal.siretError.${reason}`);
  }
  return undefined;
}

function verifiedMessage(name: LegalFieldName): string | undefined {
  if (name === "siren" && legal.value?.registry?.status === "match") {
    return t("registry.verified");
  }
  return undefined;
}
</script>

<template>
  <WizardChrome
    :current="1"
    :confirmed="block?.confirmed ?? { legal: false, banking: false, menu: false }"
    :save-state="onboarding.store.saveState"
  >
    <div class="card p-5 sm:p-6">
      <header class="mb-5">
        <h1 class="text-2xl font-bold text-summit-900">{{ t("legal.title") }}</h1>
        <p class="mt-1 text-sm text-slate-600">{{ t("legal.subtitle") }}</p>
      </header>

      <DocumentUploader
        ref="uploader"
        :on-files="onFiles"
        :prompt="t('legal.uploadPrompt')"
        :hint="t('legal.uploadHint')"
        :has-document="hasDocument"
        :disabled="isParsing"
        :on-reject="onReject"
        class="mb-5"
      />

      <ParseStatus
        :status="displayStatus"
        :review-state="reviewState"
        :on-replace="replaceDocument"
        :on-manual="enterManual"
        class="mb-5"
      />

      <div v-if="showFields" class="space-y-4">
        <div v-if="legal?.registry != null" class="flex">
          <RegistryBadge :registry="legal.registry" />
        </div>

        <ReviewField
          v-for="name in FIELD_ORDER"
          :key="name"
          :value="effectiveField(name)"
          :on-change="(value) => editField(name, value)"
          :label="t(`legal.fields.${name}`)"
          :error-message="fieldError(name)"
          :verified-message="verifiedMessage(name)"
        />
      </div>
    </div>

    <div
      v-if="showFields"
      class="fixed inset-x-0 bottom-0 z-20 border-t border-summit-100 bg-white/95 px-4 py-3 backdrop-blur safe-bottom sm:static sm:mt-6 sm:border-0 sm:bg-transparent sm:p-0"
    >
      <div class="mx-auto flex max-w-3xl justify-end">
        <button type="button" class="btn-primary w-full py-3.5 text-base sm:w-auto sm:px-10" :disabled="!canConfirm" @click="confirm">
          {{ t("common.looksGood") }}
        </button>
      </div>
    </div>
  </WizardChrome>
</template>
