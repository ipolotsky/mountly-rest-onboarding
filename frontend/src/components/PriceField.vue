<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import type { PriceVariant } from "@/types/contract";
import { amountForEdit, normalizeAmount } from "@/domain/prices";
import VariantTable from "@/components/VariantTable.vue";

interface PriceFieldProps {
  value: PriceVariant[];
  onChange: (value: PriceVariant[]) => void;
}

const props = defineProps<PriceFieldProps>();

const { t } = useI18n();

const hasVariants = computed(() => props.value.length > 1 || props.value.some((x) => x.label != null));

const expanded = ref(hasVariants.value);

watch(hasVariants, (value) => {
  if (value) {
    expanded.value = true;
  }
});

const showTable = computed(() => expanded.value);
const draft = ref(amountForEdit(props.value[0]?.amount ?? null));

watch(
  () => props.value,
  (value) => {
    if (!showTable.value) {
      draft.value = amountForEdit(value[0]?.amount ?? null);
    }
  },
  { deep: true },
);

const isPriceless = computed(() => props.value.length === 0 || props.value.every((x) => x.amount == null || x.amount.length === 0));

function commitSingle(): void {
  const normalized = normalizeAmount(draft.value);
  draft.value = normalized;
  if (normalized.length === 0) {
    props.onChange([]);
    return;
  }
  props.onChange([{ label: null, amount: normalized }]);
}

function expandToVariants(): void {
  expanded.value = true;
  const seed = props.value.length > 0 ? props.value : [{ label: null, amount: null }];
  props.onChange(seed);
}

function onCollapse(remaining: PriceVariant): void {
  expanded.value = false;
  draft.value = amountForEdit(remaining.amount);
  props.onChange([{ label: null, amount: remaining.amount }]);
}
</script>

<template>
  <div>
    <div v-if="!showTable" class="flex items-center gap-2">
      <div class="relative flex-1">
        <input
          v-model="draft"
          type="text"
          inputmode="decimal"
          class="input-field py-2 pr-9 text-sm"
          :placeholder="t('menu.noPrice')"
          @blur="commitSingle"
          @keydown.enter.prevent="commitSingle"
        />
        <span class="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">€</span>
      </div>
      <button type="button" class="shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-summit-700 hover:bg-summit-50" @click="expandToVariants">
        {{ t("menu.addVariant") }}
      </button>
    </div>

    <VariantTable v-else :value="value" :on-change="onChange" :on-collapse="onCollapse" />

    <p v-if="isPriceless" class="mt-1 inline-flex items-center gap-1.5 text-xs text-slate-500">
      <span class="rounded-full bg-slate-100 px-2 py-0.5 font-medium">{{ t("menu.onSite") }}</span>
      {{ t("menu.noPrice") }}
    </p>
  </div>
</template>
