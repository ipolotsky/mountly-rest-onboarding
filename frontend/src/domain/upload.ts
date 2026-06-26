// Client-side upload guard. Mirrors what the backend will reject so we can surface an
// error_shown event and a friendly message before wasting a parse round-trip.

const MAX_FILE_BYTES = 15 * 1024 * 1024;
const ACCEPTED_PREFIXES = ["image/"];
const ACCEPTED_TYPES = ["application/pdf"];

export type UploadRejection = "unsupported_type" | "file_too_large";

export interface UploadCheck {
  accepted: File[];
  rejection: UploadRejection | null;
}

function isAcceptedType(file: File): boolean {
  if (ACCEPTED_TYPES.includes(file.type)) {
    return true;
  }
  return ACCEPTED_PREFIXES.some((prefix) => file.type.startsWith(prefix));
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
