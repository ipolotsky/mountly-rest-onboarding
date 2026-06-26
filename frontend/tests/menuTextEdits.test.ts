import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import MenuSection from "@/components/MenuSection.vue";
import ReviewQueue from "@/components/ReviewQueue.vue";
import { fr } from "@/i18n/fr";
import { emptyMenuGroup, emptyMenuItem } from "@/domain/factory";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

describe("MenuSection commits the section title on blur, not per keystroke", () => {
  it("does not call onRename while typing, commits the final value on blur", async () => {
    const onRename = vi.fn();
    const group = emptyMenuGroup("Entrées");
    const wrapper = mount(MenuSection, {
      props: {
        group: group,
        onRename: onRename,
        onRemoveGroup: vi.fn(),
        onAddItem: vi.fn(),
        onRemoveItem: vi.fn(),
        onItemName: vi.fn(),
        onItemDescription: vi.fn(),
        onItemPrices: vi.fn(),
      },
      global: { plugins: [i18n] },
    });
    const input = wrapper.get('input[type="text"]');
    await input.setValue("Entrées chaudes");
    expect(onRename).not.toHaveBeenCalled();
    await input.trigger("blur");
    expect(onRename).toHaveBeenCalledTimes(1);
    expect(onRename).toHaveBeenCalledWith("Entrées chaudes");
  });
});

describe("ReviewQueue commits the item name on blur, not per keystroke", () => {
  it("does not call onName while typing, commits the final value on blur", async () => {
    const onName = vi.fn();
    const group = emptyMenuGroup("Plats");
    const item = emptyMenuItem();
    item.name.value = "Steak";
    item.name.status = "low_confidence";
    item.provenance = "parser";
    group.items.push(item);
    const wrapper = mount(ReviewQueue, {
      props: {
        groups: [group],
        onKeep: vi.fn(),
        onRemove: vi.fn(),
        onName: onName,
        onPrices: vi.fn(),
        onClose: vi.fn(),
      },
      global: { plugins: [i18n] },
    });
    const input = wrapper.get('input[type="text"]');
    await input.setValue("Steak frites");
    expect(onName).not.toHaveBeenCalled();
    await input.trigger("blur");
    expect(onName).toHaveBeenCalledTimes(1);
    expect(onName).toHaveBeenCalledWith(group.id, item.id, "Steak frites");
  });
});
