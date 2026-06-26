import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import MenuItemRow from "@/components/MenuItemRow.vue";
import { fr } from "@/i18n/fr";
import { emptyMenuItem } from "@/domain/factory";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountRow(onName = vi.fn(), onDescription = vi.fn()) {
  const item = emptyMenuItem();
  item.name.value = "Soupe";
  item.name.status = "present";
  return mount(MenuItemRow, {
    props: {
      item: item,
      onName: onName,
      onDescription: onDescription,
      onPrices: vi.fn(),
      onRemove: vi.fn(),
    },
    global: { plugins: [i18n] },
  });
}

describe("MenuItemRow commits edits on blur, not per keystroke", () => {
  it("does not call onName while typing, commits the final value on blur", async () => {
    const onName = vi.fn();
    const wrapper = mountRow(onName);
    const input = wrapper.get('input[type="text"]');
    await input.setValue("Soupe du jour");
    expect(onName).not.toHaveBeenCalled();
    await input.trigger("blur");
    expect(onName).toHaveBeenCalledTimes(1);
    expect(onName).toHaveBeenCalledWith("Soupe du jour");
  });

  it("commits null when the name is cleared", async () => {
    const onName = vi.fn();
    const wrapper = mountRow(onName);
    const input = wrapper.get('input[type="text"]');
    await input.setValue("");
    await input.trigger("blur");
    expect(onName).toHaveBeenCalledWith(null);
  });

  it("does not re-commit when the value is unchanged", async () => {
    const onName = vi.fn();
    const wrapper = mountRow(onName);
    const input = wrapper.get('input[type="text"]');
    await input.trigger("focus");
    await input.trigger("blur");
    expect(onName).not.toHaveBeenCalled();
  });
});
