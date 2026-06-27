import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import CookieBanner from "@/components/CookieBanner.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountBanner() {
  return mount(CookieBanner, { global: { plugins: [i18n] } });
}

describe("CookieBanner", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("shows the cookie notice when consent has not been given", () => {
    const wrapper = mountBanner();
    expect(wrapper.find("[role='region']").exists()).toBe(true);
    expect(wrapper.text()).toContain(fr.cookies.message);
  });

  it("hides the notice and remembers the choice on accept", async () => {
    const wrapper = mountBanner();
    await wrapper.get("button").trigger("click");
    expect(wrapper.find("[role='region']").exists()).toBe(false);
    expect(localStorage.getItem("cookie_consent")).toBe("1");
  });

  it("stays hidden when consent was already given", () => {
    localStorage.setItem("cookie_consent", "1");
    const wrapper = mountBanner();
    expect(wrapper.find("[role='region']").exists()).toBe(false);
  });
});
