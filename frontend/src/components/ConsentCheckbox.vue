<script setup lang="ts">
import { useI18n } from "vue-i18n";

interface ConsentCheckboxProps {
  value: boolean;
  onChange: (value: boolean) => void;
}

const props = defineProps<ConsentCheckboxProps>();

const { t } = useI18n();

function toggle(event: Event): void {
  const target = event.target as HTMLInputElement;
  props.onChange(target.checked);
}
</script>

<template>
  <label class="flex cursor-pointer items-start gap-3 rounded-xl border border-summit-100 bg-white p-4 transition hover:border-summit-200">
    <input
      type="checkbox"
      class="mt-0.5 h-5 w-5 shrink-0 rounded border-summit-300 text-summit-600 focus:ring-2 focus:ring-summit-300"
      :checked="value"
      @change="toggle"
    />
    <span class="text-sm leading-relaxed text-slate-700">{{ t("start.consentCheckbox") }}</span>
  </label>
</template>
