import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "start",
    component: () => import("@/views/Start.vue"),
  },
  {
    path: "/onboarding/legal",
    name: "legal",
    component: () => import("@/views/WizardLegal.vue"),
  },
  {
    path: "/onboarding/banking",
    name: "banking",
    component: () => import("@/views/WizardBanking.vue"),
  },
  {
    path: "/onboarding/menu",
    name: "menu",
    component: () => import("@/views/WizardMenu.vue"),
  },
  {
    path: "/restaurant",
    name: "restaurant",
    component: () => import("@/views/RestaurantPage.vue"),
  },
  {
    path: "/admin",
    name: "admin",
    component: () => import("@/views/Admin.vue"),
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: { name: "start" },
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes: routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

export const STEP_ROUTE_NAMES: Record<number, string> = {
  1: "legal",
  2: "banking",
  3: "menu",
  4: "restaurant",
};
