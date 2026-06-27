<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "@/components/AppHeader.vue";
import CookieBanner from "@/components/CookieBanner.vue";

const route = useRoute();
const isAdmin = computed(() => route.name === "admin");
</script>

<template>
  <div class="ridge flex min-h-screen flex-col">
    <AppHeader v-if="!isAdmin" />
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <CookieBanner />
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
