import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountDialog(open: boolean, onConfirm: () => void, onCancel: () => void) {
  return mount(ConfirmDialog, {
    props: { open: open, message: "Supprimer cet article du menu ?", onConfirm: onConfirm, onCancel: onCancel },
    global: { plugins: [i18n] },
  });
}

describe("ConfirmDialog", () => {
  it("renders nothing when closed", () => {
    const wrapper = mountDialog(false, vi.fn(), vi.fn());
    expect(wrapper.find("[role='dialog']").exists()).toBe(false);
  });

  it("shows the message when open", () => {
    const wrapper = mountDialog(true, vi.fn(), vi.fn());
    expect(wrapper.find("[role='dialog']").exists()).toBe(true);
    expect(wrapper.text()).toContain("Supprimer cet article du menu ?");
  });

  it("calls onConfirm when the confirm button is clicked", async () => {
    const onConfirm = vi.fn();
    const wrapper = mountDialog(true, onConfirm, vi.fn());
    const buttons = wrapper.findAll("button");
    await buttons[buttons.length - 1]!.trigger("click");
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when the cancel button is clicked", async () => {
    const onCancel = vi.fn();
    const wrapper = mountDialog(true, vi.fn(), onCancel);
    const buttons = wrapper.findAll("button");
    await buttons[0]!.trigger("click");
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
