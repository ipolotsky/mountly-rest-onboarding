import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import type { PriceVariant } from "@/types/contract";
import PriceField from "@/components/PriceField.vue";
import VariantTable from "@/components/VariantTable.vue";
import { fr } from "@/i18n/fr";

const ADD_VARIANT_LABEL = fr.menu.addVariant.replace("+ ", "");

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountField(value: PriceVariant[], onChange: (next: PriceVariant[]) => void) {
  return mount(PriceField, {
    props: { value: value, onChange: onChange },
    global: { plugins: [i18n] },
  });
}

describe("PriceField single-price normalization", () => {
  it("normalizes a comma decimal to a 2dp value on blur", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([], onChange);
    const input = wrapper.get("input");
    await input.setValue("12,50");
    await input.trigger("blur");
    expect(onChange).toHaveBeenCalledWith([{ label: null, amount: "12,50" }]);
  });

  it("filters out letters so a non-numeric entry cannot be typed", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([], onChange);
    const input = wrapper.get("input");
    await input.setValue("12a,b5");
    expect((input.element as HTMLInputElement).value).toBe("12,5");
  });

  it("clears to a price-less item when the input is non-numeric", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([{ label: null, amount: "9" }], onChange);
    const input = wrapper.get("input");
    await input.setValue("free");
    await input.trigger("blur");
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it("does not render a euro sign inside the input value", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([{ label: null, amount: "12,50 €" }], onChange);
    const input = wrapper.get("input").element as HTMLInputElement;
    expect(input.value).toBe("12,50");
    expect(input.value).not.toContain("€");
  });
});

describe("PriceField last-variant collapse (item 8)", () => {
  it("collapses to the single plain price input when variants drop to one, keeping a price", async () => {
    const onChange = vi.fn();
    const value: PriceVariant[] = [
      { label: "25 cl", amount: "3" },
      { label: "50 cl", amount: "6" },
    ];
    const wrapper = mountField(value, onChange);

    const removeButtons = wrapper.findAll("button[aria-label]");
    expect(removeButtons.length).toBeGreaterThan(0);
    await removeButtons[0]!.trigger("click");

    expect(onChange).toHaveBeenCalledWith([{ label: null, amount: "6" }]);
  });

  it("renders the single input (not the variant table) for a single unlabeled price", () => {
    const onChange = vi.fn();
    const wrapper = mountField([{ label: null, amount: "10" }], onChange);
    const input = wrapper.get("input").element as HTMLInputElement;
    expect(input.value).toBe("10");
  });
});

describe("PriceField expand-to-variants (item 7)", () => {
  it("clicking '+ Size / variant' on a single price expands to the variant table", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([{ label: null, amount: "10" }], onChange);
    expect(wrapper.findComponent(VariantTable).exists()).toBe(false);

    const expandButton = wrapper.findAll("button").find((x) => x.text().includes(ADD_VARIANT_LABEL));
    expect(expandButton).toBeTruthy();
    await expandButton!.trigger("click");

    expect(onChange).toHaveBeenCalledWith([{ label: null, amount: "10" }]);
    expect(wrapper.findComponent(VariantTable).exists()).toBe(true);
  });

  it("expanding a price-less single field seeds one empty variant row", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([], onChange);

    const expandButton = wrapper.findAll("button").find((x) => x.text().includes(ADD_VARIANT_LABEL));
    await expandButton!.trigger("click");

    expect(onChange).toHaveBeenCalledWith([{ label: null, amount: null }]);
    expect(wrapper.findComponent(VariantTable).exists()).toBe(true);
  });

  it("stays expanded even when the prop value still has length 1", async () => {
    const value: PriceVariant[] = [{ label: null, amount: "10" }];
    const onChange = vi.fn((next: PriceVariant[]) => {
      value.splice(0, value.length, ...next);
    });
    const wrapper = mountField(value, onChange);

    const expandButton = wrapper.findAll("button").find((x) => x.text().includes(ADD_VARIANT_LABEL));
    await expandButton!.trigger("click");
    await wrapper.setProps({ value: [...value] });

    expect(wrapper.findComponent(VariantTable).exists()).toBe(true);
  });
});
