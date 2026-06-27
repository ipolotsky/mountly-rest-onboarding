// Client-side upload guard. Mirrors what the backend rejects (see app/ingest._classify) so we
// surface a friendly message before wasting a parse round-trip. Only PDFs and the image formats
// the model can actually read (JPEG, PNG, WebP, GIF) are accepted.

const MAX_FILE_BYTES = 20 * 1024 * 1024;
const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];
const ACCEPTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png", ".webp", ".gif"];

export type UploadRejection = "unsupported_type" | "file_too_large";

export interface UploadCheck {
  accepted: File[];
  rejection: UploadRejection | null;
}

function hasAcceptedExtension(name: string): boolean {
  const lowered = name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((extension) => lowered.endsWith(extension));
}

function isAcceptedType(file: File): boolean {
  if (file.type === "application/pdf" || ACCEPTED_IMAGE_TYPES.includes(file.type)) {
    return true;
  }
  // The browser can report an empty or non-standard MIME (e.g. on drag-and-drop), so fall
  // back to the file extension, exactly like the backend does.
  return hasAcceptedExtension(file.name);
}

export function checkFiles(files: File[]): UploadCheck {
  for (const file of files) {
    if (!isAcceptedType(file)) {
      return { accepted: [], rejection: "unsupported_type" };
    }
    if (file.size > MAX_FILE_BYTES) {
      return { accepted: [], rejection: "file_too_large" };
    }
  }
  return { accepted: files, rejection: null };
}
