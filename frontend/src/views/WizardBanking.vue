<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { BankingFieldName, BlockStatus, Field } from "@/types/contract";
import { useOnboarding } from "@/composables/useOnboarding";
import { bicValid, ibanValidation } from "@/domain/validators";
import type { UploadRejection } from "@/domain/upload";
import WizardChrome from "@/components/WizardChrome.vue";
import DocumentUploader from "@/components/DocumentUploader.vue";
import ParseStatus from "@/components/ParseStatus.vue";
import ReviewField from "@/components/ReviewField.vue";
import type { ReviewState } from "@/components/ParseStatus.vue";

const FIELD_ORDER: BankingFieldName[] = ["account_holder", "bank_name", "iban", "bic"];

const { t } = useI18n();
const router = useRouter();
const onboarding = useOnboarding();

const manualMode = ref(false);
const uploader = ref<InstanceType<typeof DocumentUploader> | null>(null);

onMounted(async () => {
  await onboarding.ensureSession();
  onboarding.track("step_viewed", { step: 2 });
});

onUnmounted(() => {
  onboarding.store.stopParsingPoll();
});

const banking = computed(() => onboarding.banking.value);
const block = computed(() => onboarding.onboarding.value);
const hasDocument = computed(() => (banking.value?.status ?? "empty") !== "empty");
const isParsing = computed(() => banking.value?.status === "parsing");

const ibanResult = computed(() => ibanValidation(banking.value?.fields.iban.value ?? null));

const reviewState = computed<ReviewState>(() => {
  const fields = banking.value?.fields;
  if (fields == null) {
    return "clean";
  }
  const flagged = FIELD_ORDER.some((name) => fields[name].status === "low_confidence");
  return flagged ? "low_confidence" : "clean";
});

function effectiveField(name: BankingFieldName): Field {
  const field = banking.value?.fields[name];
  if (field == null) {
    return { value: null, status: "missing", confidence: null, provenance: "parser", valid: null };
  }
  if (name === "iban" && field.value != null) {
    return { ...field, valid: ibanResult.value.valid };
  }
  if (name === "bic" && field.value != null) {
    return { ...field, valid: bicValid(field.value) };
  }
  return field;
}

const showFields = computed(() => {
  const status = banking.value?.status ?? "empty";
  return manualMode.value || status === "ready" || status === "couldnt_parse";
});

const displayStatus = computed<BlockStatus>(() => {
  const status = banking.value?.status ?? "empty";
  if (manualMode.value && status === "couldnt_parse") {
    return "empty";
  }
  return status;
});

const holderMismatch = computed(() => banking.value?.cross_doc_holder_match === false);

const canConfirm = computed(() => {
  const fields = banking.value?.fields;
  if (fields == null || banking.value?.status === "parsing") {
    return false;
  }
  const ibanOk = fields.iban.value == null || fields.iban.value.length === 0 || ibanResult.value.valid;
  const bicOk = fields.bic.value == null || fields.bic.value.length === 0 || bicValid(fields.bic.value);
  return ibanOk && bicOk;
});

async function onFiles(files: File[]): Promise<void> {
  manualMode.value = false;
  onboarding.track("file_uploaded", { step: 2, file_type: files[0]?.type ?? "unknown", bytes: files[0]?.size ?? 0, upload_index: 0 });
  const ok = await onboarding.store.parseBanking(files, null);
  if (!ok) {
    onboarding.track("error_shown", { step: 2, error_type: "couldnt_parse" });
  }
}

function onReject(reason: UploadRejection): void {
  onboarding.track("error_shown", { step: 2, error_type: reason });
}

function replaceDocument(): void {
  uploader.value?.openFilePicker();
}

function editField(name: BankingFieldName, value: string | null): void {
  onboarding.store.editBankingField(name, value);
}

function enterManual(): void {
  manualMode.value = true;
}

function emitValidationResults(): void {
  const fields = banking.value?.fields;
  if (fields == null) {
    return;
  }
  if (fields.iban.value != null && fields.iban.value.length > 0) {
    onboarding.track("validation_result", { validator: "iban", passed: ibanResult.value.valid, field_name: "iban" });
  }
  if (fields.bic.value != null && fields.bic.value.length > 0) {
    onboarding.track("validation_result", { validator: "bic", passed: bicValid(fields.bic.value), field_name: "bic" });
  }
}

async function confirm(): Promise<void> {
  if (!canConfirm.value) {
    return;
  }
  emitValidationResults();
  await onboarding.confirm(2);
  void router.push({ name: "menu" });
}

function fieldError(name: BankingFieldName): string | undefined {
  if (name === "iban") {
    return t("banking.ibanError");
  }
  if (name === "bic") {
    return t("banking.bicError");
  }
  return undefined;
}
</script>

<template>
  <WizardChrome
    :current="2"
    :confirmed="block?.confirmed ?? { legal: false, banking: false, menu: false }"
    :save-state="onboarding.store.saveState"
  >
    <div class="card p-5 sm:p-6">
      <header class="mb-5">
        <h1 class="text-2xl font-bold text-summit-900">{{ t("banking.title") }}</h1>
        <p class="mt-1 text-sm text-slate-600">{{ t("banking.subtitle") }}</p>
      </header>

      <DocumentUploader
        ref="uploader"
        :on-files="onFiles"
        :prompt="t('banking.uploadPrompt')"
        :hint="t('banking.uploadHint')"
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
        <div
          v-if="holderMismatch"
          class="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-sm text-amber-800"
        >
          <svg class="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path d="M9.1 2.5a1 1 0 0 1 1.8 0l7 12.5A1 1 0 0 1 17 16.5H3a1 1 0 0 1-.9-1.5l7-12.5Z" /></svg>
          {{ t("banking.holderMismatch") }}
        </div>

        <ReviewField
          v-for="name in FIELD_ORDER"
          :key="name"
          :value="effectiveField(name)"
          :on-change="(value) => editField(name, value)"
          :label="t(`banking.fields.${name}`)"
          :error-message="fieldError(name)"
          :suspect-indexes="name === 'iban' ? ibanResult.suspectIndexes : []"
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
