import { describe, expect, it } from "vitest";
import { checkFiles } from "@/domain/upload";

function file(name: string, type: string, size = 1000): File {
  const handle = new File([new Uint8Array(1)], name, { type: type });
  Object.defineProperty(handle, "size", { value: size });
  return handle;
}

describe("checkFiles upload guard (only images + PDF)", () => {
  it("accepts a PDF and the supported image formats", () => {
    expect(checkFiles([file("doc.pdf", "application/pdf")]).rejection).toBeNull();
    expect(checkFiles([file("a.jpg", "image/jpeg")]).rejection).toBeNull();
    expect(checkFiles([file("b.png", "image/png")]).rejection).toBeNull();
    expect(checkFiles([file("c.webp", "image/webp")]).rejection).toBeNull();
    expect(checkFiles([file("d.gif", "image/gif")]).rejection).toBeNull();
  });

  it("falls back to the extension when the MIME is empty", () => {
    expect(checkFiles([file("scan.pdf", "")]).rejection).toBeNull();
    expect(checkFiles([file("photo.JPEG", "")]).rejection).toBeNull();
  });

  it("rejects a non-image, non-PDF file", () => {
    expect(checkFiles([file("notes.txt", "text/plain")]).rejection).toBe("unsupported_type");
    expect(checkFiles([file("archive.zip", "application/zip")]).rejection).toBe("unsupported_type");
    expect(checkFiles([file("clip.mp4", "video/mp4")]).rejection).toBe("unsupported_type");
  });

  it("rejects an image format the model cannot read", () => {
    expect(checkFiles([file("photo.heic", "image/heic")]).rejection).toBe("unsupported_type");
    expect(checkFiles([file("icon.svg", "image/svg+xml")]).rejection).toBe("unsupported_type");
  });

  it("accepts a file at the size limit and rejects one over it", () => {
    expect(checkFiles([file("ok.png", "image/png", 20 * 1024 * 1024)]).rejection).toBeNull();
    expect(checkFiles([file("huge.png", "image/png", 21 * 1024 * 1024)]).rejection).toBe("file_too_large");
  });

  it("rejects the whole batch if any file is unsupported", () => {
    const result = checkFiles([file("ok.png", "image/png"), file("bad.txt", "text/plain")]);
    expect(result.rejection).toBe("unsupported_type");
    expect(result.accepted).toEqual([]);
  });
});
