import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import AddItemGhostRow from "@/components/AddItemGhostRow.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountRow(onAdd: (name: string) => void) {
  return mount(AddItemGhostRow, {
    props: { onAdd: onAdd },
    global: { plugins: [i18n] },
    attachTo: document.body,
  });
}

describe("AddItemGhostRow self-respawning behavior", () => {
  it("commits on Enter, clears the input, and keeps focus for rapid multi-add", async () => {
    const onAdd = vi.fn();
    const wrapper = mountRow(onAdd);
    const input = wrapper.get("input");

    await input.setValue("Margherita");
    await input.trigger("keydown", { key: "Enter" });

    expect(onAdd).toHaveBeenCalledTimes(1);
    expect(onAdd).toHaveBeenCalledWith("Margherita");
    expect((input.element as HTMLInputElement).value).toBe("");
    expect(document.activeElement).toBe(input.element);

    await input.setValue("Calzone");
    await input.trigger("keydown", { key: "Enter" });
    expect(onAdd).toHaveBeenCalledTimes(2);
    expect(onAdd).toHaveBeenLastCalledWith("Calzone");

    wrapper.unmount();
  });

  it("commits on blur when there is a pending value", async () => {
    const onAdd = vi.fn();
    const wrapper = mountRow(onAdd);
    const input = wrapper.get("input");

    await input.setValue("Tiramisu");
    await input.trigger("blur");

    expect(onAdd).toHaveBeenCalledTimes(1);
    expect(onAdd).toHaveBeenCalledWith("Tiramisu");

    wrapper.unmount();
  });

  it("does not commit an empty or whitespace-only value", async () => {
    const onAdd = vi.fn();
    const wrapper = mountRow(onAdd);
    const input = wrapper.get("input");

    await input.setValue("   ");
    await input.trigger("keydown", { key: "Enter" });
    expect(onAdd).not.toHaveBeenCalled();

    await input.trigger("blur");
    expect(onAdd).not.toHaveBeenCalled();

    wrapper.unmount();
  });
});
