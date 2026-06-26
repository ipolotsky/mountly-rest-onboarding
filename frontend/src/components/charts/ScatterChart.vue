<script setup lang="ts">
import { computed } from "vue";

export interface ScatterPoint {
  x: number;
  y: number;
  label: string;
  device: "mobile" | "desktop";
}

interface ScatterChartProps {
  points: ScatterPoint[];
  xLabel: string;
  yLabel: string;
}

const WIDTH = 320;
const HEIGHT = 220;
const PADDING = 36;

const props = defineProps<ScatterChartProps>();

const bounds = computed(() => {
  let maxX = 1;
  let maxY = 1;
  for (const point of props.points) {
    if (point.x > maxX) {
      maxX = point.x;
    }
    if (point.y > maxY) {
      maxY = point.y;
    }
  }
  return { maxX: maxX, maxY: maxY };
});

function plotX(value: number): number {
  return PADDING + (value / bounds.value.maxX) * (WIDTH - PADDING * 2);
}

function plotY(value: number): number {
  return HEIGHT - PADDING - (value / bounds.value.maxY) * (HEIGHT - PADDING * 2);
}
</script>

<template>
  <div class="overflow-x-auto">
    <svg :viewBox="`0 0 ${WIDTH} ${HEIGHT}`" class="w-full" role="img" :aria-label="`${xLabel} / ${yLabel}`">
      <line :x1="PADDING" :y1="HEIGHT - PADDING" :x2="WIDTH - PADDING" :y2="HEIGHT - PADDING" stroke="#c2d8eb" stroke-width="1" />
      <line :x1="PADDING" :y1="PADDING" :x2="PADDING" :y2="HEIGHT - PADDING" stroke="#c2d8eb" stroke-width="1" />

      <text :x="WIDTH / 2" :y="HEIGHT - 6" text-anchor="middle" class="fill-slate-400 text-[9px]">{{ xLabel }}</text>
      <text :x="12" :y="HEIGHT / 2" text-anchor="middle" :transform="`rotate(-90 12 ${HEIGHT / 2})`" class="fill-slate-400 text-[9px]">{{ yLabel }}</text>

      <circle
        v-for="(point, index) in points"
        :key="index"
        :cx="plotX(point.x)"
        :cy="plotY(point.y)"
        r="5"
        :fill="point.device === 'mobile' ? '#3274a8' : '#8fb8d9'"
        fill-opacity="0.75"
      >
        <title>{{ point.label }}</title>
      </circle>
    </svg>
  </div>
</template>
