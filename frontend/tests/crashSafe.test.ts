import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import { createPinia } from "pinia";
import MenuDisplay from "@/components/MenuDisplay.vue";
import { fr } from "@/i18n/fr";
import { emptyMenuBlock, emptyMenuGroup, emptyMenuItem } from "@/domain/factory";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountDisplay(menu: ReturnType<typeof emptyMenuBlock>) {
  return mount(MenuDisplay, {
    props: { menu: menu },
    global: { plugins: [i18n, createPinia()] },
  });
}

describe("crash-safe rendering", () => {
  it("renders an empty menu without throwing and shows a placeholder", () => {
    const wrapper = mountDisplay(emptyMenuBlock());
    expect(wrapper.text()).toContain(fr.common.placeholder);
  });

  it("renders a price-less item as 'Prix sur place', never blank", () => {
    const menu = emptyMenuBlock();
    const group = emptyMenuGroup("Plats");
    const item = emptyMenuItem();
    item.name.value = "Plat du jour";
    item.name.status = "present";
    item.prices = [];
    group.items.push(item);
    menu.groups.push(group);
    menu.status = "ready";

    const wrapper = mountDisplay(menu);
    expect(wrapper.text()).toContain("Plat du jour");
    expect(wrapper.text()).toContain(fr.restaurant.priceOnSite);
  });

  it("renders variant prices with labels", () => {
    const menu = emptyMenuBlock();
    const group = emptyMenuGroup("Bières");
    const item = emptyMenuItem();
    item.name.value = "Pression";
    item.name.status = "present";
    item.prices = [
      { label: "25 cl", amount: "3,50" },
      { label: "50 cl", amount: "6" },
    ];
    group.items.push(item);
    menu.groups.push(group);
    menu.status = "ready";

    const wrapper = mountDisplay(menu);
    expect(wrapper.text()).toContain("25 cl");
    expect(wrapper.text()).toContain("3,50 €");
    expect(wrapper.text()).toContain("6 €");
  });
});
