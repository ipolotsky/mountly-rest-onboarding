import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import type { RegistryInfo } from "@/types/contract";
import RegistryBadge from "@/components/RegistryBadge.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountBadge(registry: RegistryInfo | null) {
  return mount(RegistryBadge, {
    props: { registry: registry },
    global: { plugins: [i18n] },
  });
}

describe("RegistryBadge states", () => {
  it("renders nothing when registry is null", () => {
    const wrapper = mountBadge(null);
    expect(wrapper.find("span").exists()).toBe(false);
  });

  it("shows the verified label and a tooltip trigger on match", () => {
    const wrapper = mountBadge({ status: "match", name_match: true });
    expect(wrapper.text()).toContain(fr.registry.verified);
    expect(wrapper.find("button[aria-label]").exists()).toBe(true);
  });

  it("opens the registry tooltip when the ? button is activated", async () => {
    const wrapper = mountBadge({ status: "match", name_match: true });
    expect(wrapper.find("[role='tooltip']").exists()).toBe(false);
    await wrapper.get("button[aria-label]").trigger("click");
    expect(wrapper.find("[role='tooltip']").exists()).toBe(true);
    expect(wrapper.find("[role='tooltip']").text()).toContain("recherche-entreprises.api.gouv.fr");
  });

  it("shows the no-match message and no tooltip trigger", () => {
    const wrapper = mountBadge({ status: "no_match", name_match: false });
    expect(wrapper.text()).toContain(fr.registry.noMatch);
    expect(wrapper.find("button[aria-label]").exists()).toBe(false);
  });

  it("shows the unavailable message", () => {
    const wrapper = mountBadge({ status: "unavailable", name_match: null });
    expect(wrapper.text()).toContain(fr.registry.unavailable);
  });
});
