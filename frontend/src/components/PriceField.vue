<script setup lang="ts">
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { PriceVariant } from "@/types/contract";
import VariantTable from "@/components/VariantTable.vue";

interface PriceFieldProps {
  value: PriceVariant[];
  onChange: (value: PriceVariant[]) => void;
}

const props = defineProps<PriceFieldProps>();

const { t } = useI18n();

const expanded = ref(props.value.length > 1 || props.value.some((x) => x.label != null));

const hasMultiple = computed(() => props.value.length > 1 || expanded.value);
const singleAmount = computed(() => props.value[0]?.amount ?? "");
const isPriceless = computed(() => props.value.length === 0 || props.value.every((x) => x.amount == null));

function updateSingle(amount: string): void {
  const trimmed = amount.trim();
  if (trimmed.length === 0) {
    props.onChange([]);
    return;
  }
  props.onChange([{ label: null, amount: trimmed }]);
}

function expandToVariants(): void {
  expanded.value = true;
  if (props.value.length === 0) {
    props.onChange([{ label: null, amount: null }]);
  }
}
</script>

<template>
  <div>
    <div v-if="!hasMultiple" class="flex items-center gap-2">
      <div class="relative flex-1">
        <input
          type="text"
          inputmode="decimal"
          class="input-field py-2 pr-9 text-sm"
          :value="singleAmount"
          :placeholder="t('menu.noPrice')"
          @input="updateSingle(($event.target as HTMLInputElement).value)"
        />
        <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">€</span>
      </div>
      <button type="button" class="shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-summit-700 hover:bg-summit-50" @click="expandToVariants">
        {{ t("menu.addVariant") }}
      </button>
    </div>

    <VariantTable v-else :value="value" :on-change="onChange" />

    <p v-if="isPriceless" class="mt-1 inline-flex items-center gap-1.5 text-xs text-slate-500">
      <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium">{{ t("menu.onSite") }}</span>
      {{ t("menu.noPrice") }}
    </p>
  </div>
</template>
