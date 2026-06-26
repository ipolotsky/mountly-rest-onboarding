<script setup lang="ts">
import { computed } from "vue";
import { useI18n } from "vue-i18n";
import type { MenuBlock } from "@/types/contract";
import { formatPrices, isPriceless } from "@/domain/prices";

interface MenuDisplayProps {
  menu: MenuBlock;
}

const props = defineProps<MenuDisplayProps>();

const { t } = useI18n();

const visibleGroups = computed(() => props.menu.groups.filter((x) => x.items.length > 0));
const isEmpty = computed(() => visibleGroups.value.length === 0);
</script>

<template>
  <div>
    <p v-if="isEmpty" class="rounded-xl border border-dashed border-summit-200 px-4 py-6 text-center text-sm italic text-slate-400">
      {{ t("common.placeholder") }}
    </p>

    <div v-else class="space-y-7">
      <section v-for="group in visibleGroups" :key="group.id">
        <h3 class="mb-3 flex items-center gap-2 text-lg font-bold text-summit-900">
          <span class="h-px flex-1 bg-summit-100"></span>
          <span class="shrink-0">{{ group.name }}</span>
          <span class="h-px flex-1 bg-summit-100"></span>
        </h3>

        <ul class="space-y-3">
          <li v-for="item in group.items" :key="item.id" class="flex items-baseline justify-between gap-4">
            <div class="min-w-0">
              <p class="font-medium text-slate-900">
                {{ item.name.value ?? t("common.placeholder") }}
              </p>
              <p v-if="(item.description.value ?? '').length > 0" class="mt-0.5 text-sm text-slate-500">
                {{ item.description.value }}
              </p>
            </div>
            <div class="shrink-0 text-right">
              <template v-if="!isPriceless(item.prices)">
                <span v-for="(price, i) in formatPrices(item.prices)" :key="i" class="block text-sm font-semibold text-summit-700">
                  {{ price }}
                </span>
              </template>
              <span v-else class="text-xs italic text-slate-400">{{ t("restaurant.priceOnSite") }}</span>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
