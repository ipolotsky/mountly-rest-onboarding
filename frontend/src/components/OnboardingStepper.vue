<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { Step } from "@/types/contract";
import { STEP_ROUTE_NAMES } from "@/router";

interface StepDefinition {
  index: 1 | 2 | 3;
  label: string;
  done: boolean;
}

interface OnboardingStepperProps {
  current: Step;
  confirmed: { legal: boolean; banking: boolean; menu: boolean };
}

const props = defineProps<OnboardingStepperProps>();

const { t } = useI18n();
const router = useRouter();

const steps = computed<StepDefinition[]>(() => [
  { index: 1, label: t("stepper.legal"), done: props.confirmed.legal },
  { index: 2, label: t("stepper.banking"), done: props.confirmed.banking },
  { index: 3, label: t("stepper.menu"), done: props.confirmed.menu },
]);

function isActive(index: number): boolean {
  return props.current === index;
}

function canNavigate(index: number): boolean {
  return index < props.current || isStepDone(index);
}

function isStepDone(index: number): boolean {
  if (index === 1) {
    return props.confirmed.legal;
  }
  if (index === 2) {
    return props.confirmed.banking;
  }
  return props.confirmed.menu;
}

function navigate(index: 1 | 2 | 3): void {
  if (!canNavigate(index)) {
    return;
  }
  const name = STEP_ROUTE_NAMES[index];
  if (name != null) {
    void router.push({ name: name });
  }
}
</script>

<template>
  <nav class="mx-auto w-full max-w-3xl" aria-label="progression">
    <ol class="relative flex items-center justify-between">
      <span class="absolute left-0 right-0 top-4 -z-0 mx-6 h-0.5 bg-summit-100" aria-hidden="true"></span>
      <span
        class="absolute left-0 top-4 -z-0 mx-6 h-0.5 bg-summit-500 transition-all duration-500"
        :style="{ width: `calc(${((props.current - 1) / 2) * 100}% - 0px)` }"
        aria-hidden="true"
      ></span>

      <li v-for="step in steps" :key="step.index" class="relative z-10 flex flex-1 flex-col items-center gap-1.5">
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition"
          :class="[
            step.done
              ? 'border-summit-500 bg-summit-500 text-white'
              : isActive(step.index)
                ? 'border-summit-500 bg-white text-summit-700 ring-4 ring-summit-100'
                : 'border-summit-200 bg-white text-slate-400',
            canNavigate(step.index) ? 'cursor-pointer' : 'cursor-default',
          ]"
          :disabled="!canNavigate(step.index)"
          @click="navigate(step.index)"
        >
          <svg v-if="step.done" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path
              fill-rule="evenodd"
              d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z"
              clip-rule="evenodd"
            />
          </svg>
          <span v-else>{{ step.index }}</span>
        </button>
        <span
          class="text-center text-[11px] font-semibold sm:text-xs"
          :class="isActive(step.index) || step.done ? 'text-summit-800' : 'text-slate-400'"
        >
          {{ step.label }}
        </span>
      </li>
    </ol>
  </nav>
</template>
