<script setup lang="ts">
import type { Step } from "@/types/contract";
import type { SaveState } from "@/stores/onboarding";
import OnboardingStepper from "@/components/OnboardingStepper.vue";
import AutosaveIndicator from "@/components/AutosaveIndicator.vue";

interface WizardChromeProps {
  current: Step;
  confirmed: { legal: boolean; banking: boolean; menu: boolean };
  saveState: SaveState;
  wide?: boolean;
}

defineProps<WizardChromeProps>();
</script>

<template>
  <div class="mx-auto w-full px-4 pb-28 pt-5 sm:pb-12" :class="wide ? 'max-w-6xl' : 'max-w-3xl'">
    <div class="mb-6 flex items-center justify-between gap-3">
      <div class="flex-1">
        <OnboardingStepper :current="current" :confirmed="confirmed" />
      </div>
    </div>
    <div class="mb-2 flex justify-end">
      <AutosaveIndicator :state="saveState" />
    </div>
    <slot />
  </div>
</template>
