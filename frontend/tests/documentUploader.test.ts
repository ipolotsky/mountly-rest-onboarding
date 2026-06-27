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

function fileList(files: File[]): FileList {
  return { length: files.length, item: (index: number) => files[index] ?? null } as unknown as FileList;
}

function mountWithReject(onFiles = vi.fn(), onReject = vi.fn()) {
  return mount(DocumentUploader, {
    props: { onFiles: onFiles, prompt: "Upload", onReject: onReject },
    global: { plugins: [i18n] },
  });
}

describe("DocumentUploader rejects everything but images and PDF", () => {
  it("rejects an unsupported file, shows a message, and does not call onFiles", async () => {
    const onFiles = vi.fn();
    const onReject = vi.fn();
    const wrapper = mountWithReject(onFiles, onReject);
    const txt = new File(["x"], "notes.txt", { type: "text/plain" });
    await wrapper.get('[aria-disabled="false"]').trigger("drop", { dataTransfer: { files: fileList([txt]) } });
    expect(onFiles).not.toHaveBeenCalled();
    expect(onReject).toHaveBeenCalledWith("unsupported_type");
    expect(wrapper.text()).toContain(fr.uploader.unsupportedType);
  });

  it("accepts a supported image and clears any error", async () => {
    const onFiles = vi.fn();
    const onReject = vi.fn();
    const wrapper = mountWithReject(onFiles, onReject);
    const image = new File(["x"], "photo.png", { type: "image/png" });
    await wrapper.get('[aria-disabled="false"]').trigger("drop", { dataTransfer: { files: fileList([image]) } });
    expect(onReject).not.toHaveBeenCalled();
    expect(onFiles).toHaveBeenCalledTimes(1);
    expect(onFiles.mock.calls[0]![0]).toHaveLength(1);
    expect(wrapper.text()).not.toContain(fr.uploader.unsupportedType);
  });
});
