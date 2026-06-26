import { createI18n } from "vue-i18n";
import type { Locale } from "@/types/contract";
import { fr } from "@/i18n/fr";
import { en } from "@/i18n/en";

const LOCALE_STORAGE_KEY = "onboarding_locale";

function detectInitialLocale(): Locale {
  const stored = localStorage.getItem(LOCALE_STORAGE_KEY);
  if (stored === "fr" || stored === "en") {
    return stored;
  }
  const navigatorLanguage = navigator.language?.toLowerCase() ?? "fr";
  return navigatorLanguage.startsWith("en") ? "en" : "fr";
}

export const i18n = createI18n({
  legacy: false,
  locale: detectInitialLocale(),
  fallbackLocale: "fr",
  messages: { fr, en },
});

export function setLocale(locale: Locale): void {
  i18n.global.locale.value = locale;
  localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  document.documentElement.setAttribute("lang", locale);
}

export function currentLocale(): Locale {
  return i18n.global.locale.value as Locale;
}
