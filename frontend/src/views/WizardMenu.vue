<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useOnboarding } from "@/composables/useOnboarding";
import { checkFiles } from "@/domain/upload";
import WizardChrome from "@/components/WizardChrome.vue";
import DocumentUploader from "@/components/DocumentUploader.vue";
import ParseStatus from "@/components/ParseStatus.vue";
import MenuBuilder from "@/components/MenuBuilder.vue";

const { t } = useI18n();
const router = useRouter();
const onboarding = useOnboarding();

onMounted(async () => {
  await onboarding.ensureSession();
  if (menu.value?.status === "parsing") {
    parsingCount.value = Math.max(menu.value.source_files.length, 1);
  }
  onboarding.track("step_viewed", { step: 3 });
});

onUnmounted(() => {
  onboarding.store.stopParsingPoll();
});

const menu = computed(() => onboarding.menu.value);
const block = computed(() => onboarding.onboarding.value);
const isParsing = computed(() => menu.value?.status === "parsing");
const hasItems = computed(() => (menu.value?.groups ?? []).some((x) => x.items.length > 0));
const canConfirm = computed(() => hasItems.value && !isParsing.value);
const showBuilder = computed(() => {
  const status = menu.value?.status ?? "empty";
  return status === "ready" || status === "couldnt_parse" || (menu.value?.groups.length ?? 0) > 0;
});
const showUploader = computed(() => !showBuilder.value);
const parsingCount = ref(1);

async function onFiles(files: File[]): Promise<void> {
  const check = checkFiles(files);
  if (check.rejection != null) {
    onboarding.track("error_shown", { step: 3, error_type: check.rejection });
    return;
  }
  parsingCount.value = files.length;
  for (let i = 0; i < files.length; i += 1) {
    const file = files[i];
    onboarding.track("file_uploaded", { step: 3, file_type: file.type, bytes: file.size, upload_index: i });
  }
  const ok = await onboarding.store.parseMenu(files, null);
  if (!ok) {
    onboarding.track("error_shown", { step: 3, error_type: "couldnt_parse" });
  }
}

async function confirm(): Promise<void> {
  await onboarding.confirm(3);
  void router.push({ name: "restaurant" });
}
</script>

<template>
  <WizardChrome
    :current="3"
    :confirmed="block?.confirmed ?? { legal: false, banking: false, menu: false }"
    :save-state="onboarding.store.saveState"
    wide
  >
    <header class="mb-5">
      <h1 class="text-2xl font-bold text-summit-900">{{ t("menu.title") }}</h1>
      <p class="mt-1 text-sm text-slate-600">{{ t("menu.subtitle") }}</p>
    </header>

    <DocumentUploader
      v-if="showUploader"
      :on-files="onFiles"
      :prompt="t('menu.uploadPrompt')"
      :hint="t('menu.uploadHint')"
      :has-document="false"
      :multiple="true"
      :disabled="isParsing"
      class="mb-5"
    />

    <ParseStatus
      :status="menu?.status ?? 'empty'"
      :parsing-count="parsingCount"
      class="mb-5"
    />

    <MenuBuilder v-if="showBuilder && menu != null" :menu="menu" />

    <div
      v-if="showBuilder"
      class="fixed inset-x-0 bottom-0 z-20 border-t border-summit-100 bg-white/95 px-4 py-3 backdrop-blur safe-bottom sm:static sm:mt-6 sm:border-0 sm:bg-transparent sm:p-0"
    >
      <div class="mx-auto flex max-w-6xl items-center justify-end gap-3">
        <button type="button" class="btn-primary py-3.5 text-base sm:px-10" :disabled="!canConfirm" @click="confirm">
          {{ t("common.looksGood") }}
        </button>
      </div>
    </div>
  </WizardChrome>
</template>
