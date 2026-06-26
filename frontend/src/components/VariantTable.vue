<script setup lang="ts">
import { useI18n } from "vue-i18n";
import type { PriceVariant } from "@/types/contract";
import { amountForEdit, normalizeAmount } from "@/domain/prices";

const QUICK_CHIPS = ["25 cl", "33 cl", "50 cl", "Verre", "Bouteille"];

interface VariantTableProps {
  value: PriceVariant[];
  onChange: (value: PriceVariant[]) => void;
  onCollapse?: (remaining: PriceVariant) => void;
}

const props = defineProps<VariantTableProps>();

const { t } = useI18n();

function updateLabel(index: number, label: string): void {
  const next = props.value.map((x, i) => (i === index ? { label: label.length > 0 ? label : null, amount: x.amount } : x));
  props.onChange(next);
}

function commitAmount(index: number, amount: string): void {
  const normalized = normalizeAmount(amount);
  const next = props.value.map((x, i) => (i === index ? { label: x.label, amount: normalized.length > 0 ? normalized : null } : x));
  props.onChange(next);
}

function addVariant(label: string | null): void {
  props.onChange([...props.value, { label: label, amount: null }]);
}

function removeVariant(index: number): void {
  const remaining = props.value.filter((_x, i) => i !== index);
  if (remaining.length === 0 && props.onCollapse != null) {
    const removed = props.value[index];
    props.onCollapse({ label: null, amount: removed?.amount ?? null });
    return;
  }
  if (remaining.length === 1 && props.onCollapse != null) {
    const last = remaining[0];
    props.onCollapse({ label: null, amount: last?.amount ?? null });
    return;
  }
  props.onChange(remaining);
}

function chipUsed(chip: string): boolean {
  return props.value.some((x) => x.label === chip);
}
</script>

<template>
  <div class="rounded-xl border border-summit-100 bg-summit-50/40 p-3">
    <div class="space-y-2">
      <div v-for="(variant, index) in value" :key="index" class="flex items-center gap-2">
        <input
          type="text"
          class="input-field flex-1 py-2 text-sm"
          :value="variant.label ?? ''"
          :placeholder="t('menu.variantLabel')"
          @input="updateLabel(index, ($event.target as HTMLInputElement).value)"
        />
        <div class="relative w-24 shrink-0">
          <input
            type="text"
            inputmode="decimal"
            class="input-field w-full py-2 pr-7 text-sm"
            :value="amountForEdit(variant.amount)"
            :placeholder="t('menu.variantAmount')"
            @blur="commitAmount(index, ($event.target as HTMLInputElement).value)"
            @keydown.enter.prevent="commitAmount(index, ($event.target as HTMLInputElement).value)"
          />
          <span class="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-sm text-slate-400">€</span>
        </div>
        <button
          type="button"
          class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:bg-rose-50 hover:text-rose-500"
          :aria-label="t('common.cancel')"
          @click="removeVariant(index)"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6 6 18" /></svg>
        </button>
      </div>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-1.5">
      <button
        v-for="chip in QUICK_CHIPS"
        :key="chip"
        type="button"
        class="rounded-full border px-2.5 py-1 text-xs font-medium transition"
        :class="chipUsed(chip) ? 'border-summit-300 bg-summit-100 text-summit-700' : 'border-summit-200 bg-white text-slate-600 hover:border-summit-300'"
        @click="addVariant(chip)"
      >
        {{ chip }}
      </button>
      <button type="button" class="rounded-full border border-dashed border-summit-300 px-2.5 py-1 text-xs font-semibold text-summit-700" @click="addVariant(null)">
        {{ t("menu.addVariant") }}
      </button>
    </div>
  </div>
</template>
