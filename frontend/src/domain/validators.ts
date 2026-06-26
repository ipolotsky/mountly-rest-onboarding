// Pure client-side validators. The backend is authoritative, but these gate the per-block
// confirm and give immediate inline feedback so the owner never submits a malformed identifier.

export interface ValidationResult {
  valid: boolean;
  suspectIndexes: number[];
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

export function luhnValid(raw: string): boolean {
  const digits = digitsOnly(raw);
  if (digits.length === 0) {
    return false;
  }
  let sum = 0;
  let double = false;
  for (let i = digits.length - 1; i >= 0; i -= 1) {
    let digit = digits.charCodeAt(i) - 48;
    if (double) {
      digit *= 2;
      if (digit > 9) {
        digit -= 9;
      }
    }
    sum += digit;
    double = !double;
  }
  return sum % 10 === 0;
}

export function sirenValid(raw: string | null): boolean {
  if (raw == null) {
    return false;
  }
  const digits = digitsOnly(raw);
  if (digits.length !== 9) {
    return false;
  }
  return luhnValid(digits);
}

export function siretValid(raw: string | null): boolean {
  if (raw == null) {
    return false;
  }
  const digits = digitsOnly(raw);
  if (digits.length !== 14) {
    return false;
  }
  return luhnValid(digits);
}

export function normalizeIban(raw: string): string {
  // Keep only [A-Z0-9]: drops spaces, dots, dashes and invisible characters (e.g. a
  // zero-width space) that would otherwise break the mod-97 check on an otherwise valid IBAN.
  return raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
}

// IBAN mod-97 (ISO 13616). Returns which characters look wrong so the field can highlight them.
export function ibanValidation(raw: string | null): ValidationResult {
  if (raw == null) {
    return { valid: false, suspectIndexes: [] };
  }
  const normalized = normalizeIban(raw);
  if (normalized.length < 5 || normalized.length > 34) {
    return { valid: false, suspectIndexes: [] };
  }

  const suspectIndexes: number[] = [];
  for (let i = 0; i < normalized.length; i += 1) {
    const code = normalized.charCodeAt(i);
    const isDigit = code >= 48 && code <= 57;
    const isLetter = code >= 65 && code <= 90;
    if (!isDigit && !isLetter) {
      suspectIndexes.push(i);
    }
  }
  if (suspectIndexes.length > 0) {
    return { valid: false, suspectIndexes: suspectIndexes };
  }

  const rearranged = normalized.slice(4) + normalized.slice(0, 4);
  let remainder = 0;
  for (let i = 0; i < rearranged.length; i += 1) {
    const code = rearranged.charCodeAt(i);
    const piece = code >= 65 ? (code - 55).toString() : String.fromCharCode(code);
    for (let j = 0; j < piece.length; j += 1) {
      remainder = (remainder * 10 + (piece.charCodeAt(j) - 48)) % 97;
    }
  }
  return { valid: remainder === 1, suspectIndexes: [] };
}

export function ibanValid(raw: string | null): boolean {
  return ibanValidation(raw).valid;
}

const BIC_PATTERN = /^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$/;

export function bicValid(raw: string | null): boolean {
  if (raw == null) {
    return false;
  }
  const normalized = raw.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();
  if (normalized.length === 0) {
    return false;
  }
  return BIC_PATTERN.test(normalized);
}
