import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createI18n } from "vue-i18n";
import type { SourceFile } from "@/types/contract";
import SourcePreview from "@/components/SourcePreview.vue";
import { fr } from "@/i18n/fr";

const i18n = createI18n({ legacy: false, locale: "fr", fallbackLocale: "fr", messages: { fr } });

function source(kind: "pdf" | "image", id = "f1"): SourceFile {
  return { id: id, kind: kind, filename: `${id}.${kind === "pdf" ? "pdf" : "png"}`, url: `/api/onboarding/x/files/${id}` };
}

function mountPreview(files: SourceFile[]) {
  return mount(SourcePreview, { props: { files: files }, global: { plugins: [i18n] } });
}

describe("SourcePreview zoom controls follow the active file type", () => {
  it("shows the two zoom buttons for an image", () => {
    const wrapper = mountPreview([source("image")]);
    expect(wrapper.findAll("button").length).toBe(2);
    expect(wrapper.find("img").exists()).toBe(true);
    expect(wrapper.find("iframe").exists()).toBe(false);
  });

  it("hides the zoom buttons when the active file is a PDF", () => {
    const wrapper = mountPreview([source("pdf")]);
    expect(wrapper.findAll("button").length).toBe(0);
    expect(wrapper.find("iframe").exists()).toBe(true);
  });

  it("keeps the file selector but hides zoom on a PDF in a multi-file set", () => {
    const wrapper = mountPreview([source("pdf", "a"), source("image", "b")]);
    expect(wrapper.findAll("button").length).toBe(2);
    expect(wrapper.find("iframe").exists()).toBe(true);
  });

  it("reveals zoom after switching to an image in a multi-file set", async () => {
    const wrapper = mountPreview([source("pdf", "a"), source("image", "b")]);
    expect(wrapper.findAll("button").length).toBe(2);
    await wrapper.findAll("button")[1]!.trigger("click");
    expect(wrapper.findAll("button").length).toBe(4);
    expect(wrapper.find("img").exists()).toBe(true);
  });
});
