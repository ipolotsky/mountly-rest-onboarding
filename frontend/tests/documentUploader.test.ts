import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import DocumentUploader from "@/components/DocumentUploader.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function mountUploader(disabled: boolean, onFiles = vi.fn()) {
  return mount(DocumentUploader, {
    props: { onFiles: onFiles, prompt: "Upload", disabled: disabled },
    global: { plugins: [i18n] },
  });
}

describe("DocumentUploader disabled while processing", () => {
  it("disables every button when disabled", () => {
    const wrapper = mountUploader(true);
    const buttons = wrapper.findAll("button");
    expect(buttons.length).toBeGreaterThan(0);
    expect(buttons.every((x) => (x.element as HTMLButtonElement).disabled)).toBe(true);
  });

  it("disables the hidden file inputs when disabled", () => {
    const wrapper = mountUploader(true);
    const inputs = wrapper.findAll('input[type="file"]');
    expect(inputs.every((x) => (x.element as HTMLInputElement).disabled)).toBe(true);
  });

  it("leaves controls enabled when not disabled", () => {
    const wrapper = mountUploader(false);
    const inputs = wrapper.findAll('input[type="file"]');
    expect(inputs.some((x) => (x.element as HTMLInputElement).disabled)).toBe(false);
  });

  it("ignores a dropped file while disabled", async () => {
    const onFiles = vi.fn();
    const wrapper = mountUploader(true, onFiles);
    const file = new File(["x"], "k.png", { type: "image/png" });
    await wrapper.get('[aria-disabled="true"]').trigger("drop", { dataTransfer: { files: [file] } });
    expect(onFiles).not.toHaveBeenCalled();
  });
});
