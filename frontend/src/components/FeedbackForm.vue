<script setup lang="ts">
import { ref } from "vue";
import { useI18n } from "vue-i18n";
import type { FeedbackPayload } from "@/types/contract";

interface FeedbackFormProps {
  onSubmit: (payload: FeedbackPayload) => Promise<void>;
}

const props = defineProps<FeedbackFormProps>();

const { t } = useI18n();

const csat = ref<number | null>(null);
const answer1 = ref("");
const answer2 = ref("");
const submitted = ref(false);
const submitting = ref(false);

function pick(value: number): void {
  csat.value = value;
}

async function submit(): Promise<void> {
  if (csat.value == null || submitting.value) {
    return;
  }
  submitting.value = true;
  await props.onSubmit({
    csat: csat.value,
    answers: { helped: answer1.value.trim(), improve: answer2.value.trim() },
  });
  submitting.value = false;
  submitted.value = true;
}
</script>

<template>
  <div class="card p-5 sm:p-6">
    <div v-if="submitted" class="flex items-center gap-3 text-emerald-700">
      <svg class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true"><path fill-rule="evenodd" d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z" clip-rule="evenodd" /></svg>
      <p class="font-semibold">{{ t("restaurant.feedbackThanks") }}</p>
    </div>

    <div v-else>
      <h3 class="text-lg font-bold text-summit-900">{{ t("restaurant.feedbackTitle") }}</h3>

      <div class="mt-4">
        <p class="mb-2 text-sm font-medium text-slate-600">{{ t("restaurant.feedbackCsat") }}</p>
        <div class="flex gap-2">
          <button
            v-for="score in [1, 2, 3, 4, 5]"
            :key="score"
            type="button"
            class="flex h-11 w-11 items-center justify-center rounded-xl border text-sm font-bold transition"
            :class="csat === score ? 'border-summit-500 bg-summit-500 text-white' : 'border-summit-200 bg-white text-slate-500 hover:border-summit-300'"
            @click="pick(score)"
          >
            {{ score }}
          </button>
        </div>
      </div>

      <div class="mt-4 space-y-3">
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-600">{{ t("restaurant.feedbackQ1") }}</label>
          <input v-model="answer1" type="text" class="input-field" />
        </div>
        <div>
          <label class="mb-1 block text-sm font-medium text-slate-600">{{ t("restaurant.feedbackQ2") }}</label>
          <input v-model="answer2" type="text" class="input-field" />
        </div>
      </div>

      <button type="button" class="btn-primary mt-4 px-6 py-2.5" :disabled="csat == null || submitting" @click="submit">
        {{ t("restaurant.feedbackSubmit") }}
      </button>
    </div>
  </div>
</template>
