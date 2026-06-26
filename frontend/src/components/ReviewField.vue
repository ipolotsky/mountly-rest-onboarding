<script setup lang="ts">
import { computed, nextTick, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { Field } from "@/types/contract";

interface ReviewFieldProps {
  value: Field;
  onChange: (value: string | null) => void;
  label: string;
  errorMessage?: string;
  verifiedMessage?: string;
  placeholder?: string;
  suspectIndexes?: number[];
}

const props = defineProps<ReviewFieldProps>();

const { t } = useI18n();

const editing = ref(false);
const inputElement = ref<HTMLInputElement | null>(null);
const draft = ref("");

const isFlagged = computed(() => props.value.status === "low_confidence");
const isMissing = computed(() => props.value.status === "missing" || props.value.value == null);
const isInvalid = computed(() => props.value.valid === false);
const isVerified = computed(() => props.value.valid === true && props.verifiedMessage != null);
const displayValue = computed(() => props.value.value ?? "");

async function startEditing(): Promise<void> {
  draft.value = props.value.value ?? "";
  editing.value = true;
  await nextTick();
  inputElement.value?.focus();
  inputElement.value?.select();
}

function commit(): void {
  if (!editing.value) {
    return;
  }
  editing.value = false;
  const trimmed = draft.value.trim();
  const next = trimmed.length === 0 ? null : trimmed;
  if (next !== (props.value.value ?? null)) {
    props.onChange(next);
  }
}

function cancel(): void {
  editing.value = false;
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div class="flex items-center justify-between">
      <label class="text-sm font-medium text-slate-600">{{ label }}</label>
      <span
        v-if="isFlagged && !editing"
        class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-700"
      >
        {{ t("menu.toReview") }}
      </span>
    </div>

    <div v-if="!editing" class="group relative">
      <button
        type="button"
        class="flex w-full items-center justify-between gap-2 rounded-xl border px-4 py-2.5 text-left transition"
        :class="[
          isInvalid
            ? 'border-rose-300 bg-rose-50/50'
            : isFlagged
              ? 'border-amber-300 bg-amber-50/50'
              : 'border-summit-100 bg-white hover:border-summit-200',
        ]"
        @click="startEditing"
      >
        <span :class="isMissing ? 'text-sm italic text-slate-400' : 'text-sm font-medium text-slate-900'">
          {{ isMissing ? (placeholder ?? t("common.placeholder")) : displayValue }}
        </span>
        <svg
          class="h-4 w-4 shrink-0 text-slate-300 transition group-hover:text-summit-500"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.8"
          aria-hidden="true"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="m16.5 4.5 3 3L9 18l-4 1 1-4 10.5-10.5Z" />
        </svg>
      </button>
    </div>

    <input
      v-else
      ref="inputElement"
      v-model="draft"
      type="text"
      class="input-field"
      :class="{ 'field-invalid': isInvalid }"
      :placeholder="placeholder ?? t('common.placeholder')"
      @blur="commit"
      @keydown.enter.prevent="commit"
      @keydown.esc.prevent="cancel"
    />

    <p v-if="isInvalid && errorMessage != null" class="text-xs font-medium text-rose-600">
      {{ errorMessage }}
    </p>
    <p v-else-if="isVerified" class="inline-flex items-center gap-1 text-xs font-medium text-emerald-600">
      <svg class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
        <path
          fill-rule="evenodd"
          d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-3.5-3.5a1 1 0 1 1 1.4-1.4L8.5 12l6.8-6.7a1 1 0 0 1 1.4 0Z"
          clip-rule="evenodd"
        />
      </svg>
      {{ verifiedMessage }}
    </p>
  </div>
</template>
