import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import type { PriceVariant } from "@/types/contract";
import PriceField from "@/components/PriceField.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountField(value: PriceVariant[], onChange: (next: PriceVariant[]) => void) {
  return mount(PriceField, {
    props: { value: value, onChange: onChange },
    global: { plugins: [i18n] },
  });
}

describe("PriceField single-price normalization", () => {
  it("normalizes a comma decimal to a 2dp double on blur", async () => {
    const onChange = vi.fn();
    const wrapper = mountField([], onChange);
    const input = wrapper.get("input");
    await input.setValue("12,50");
    await input.trigger("blur");
    expect(onChange).toHaveBeenCalledWith([{ label: null, amount: "12.50" }]);
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
    expect(input.value).toBe("12.50");
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
