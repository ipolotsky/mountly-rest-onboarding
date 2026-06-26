import type { PriceVariant } from "@/types/contract";

// Strip currency symbols/spaces and turn a European decimal comma into a dot for parsing.
function stripToNumeric(raw: string): string {
  return raw
    .replace(/€/g, "")
    .replace(/eur/gi, "")
    .replace(/\s/g, "")
    .replace(",", ".")
    .trim();
}

// Keep only what a European price field allows: digits and a single decimal comma, with at
// most two decimals. Used to filter input so letters or stray symbols can never be entered.
export function sanitizePriceInput(raw: string): string {
  const digitsAndComma = raw.replace(/[^0-9,]/g, "");
  const firstComma = digitsAndComma.indexOf(",");
  if (firstComma === -1) {
    return digitsAndComma;
  }
  const head = digitsAndComma.slice(0, firstComma + 1);
  const decimals = digitsAndComma.slice(firstComma + 1).replace(/,/g, "").slice(0, 2);
  return head + decimals;
}

// Normalize a user-entered amount to a canonical European string (comma decimal, <= 2 decimals).
// Returns "" when the input is empty or not a number (so the field becomes price-less).
export function normalizeAmount(raw: string): string {
  const cleaned = stripToNumeric(raw);
  if (cleaned.length === 0) {
    return "";
  }
  const parsed = Number(cleaned);
  if (Number.isNaN(parsed)) {
    return "";
  }
  const rounded = Math.round(parsed * 100) / 100;
  const text = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2);
  return text.replace(".", ",");
}

// The value shown in a price input while editing: digits + comma only, no currency symbol.
export function amountForEdit(amount: string | null): string {
  if (amount == null) {
    return "";
  }
  return sanitizePriceInput(amount.replace(/\./g, ","));
}

function withSymbol(amount: string): string {
  const normalized = normalizeAmount(amount);
  if (normalized.length === 0) {
    return amount.trim();
  }
  return `${normalized} €`;
}

export function formatVariant(variant: PriceVariant): string | null {
  if (variant.amount == null || variant.amount.trim().length === 0) {
    return null;
  }
  const amount = withSymbol(variant.amount);
  if (variant.label != null && variant.label.trim().length > 0) {
    return `${variant.label} · ${amount}`;
  }
  return amount;
}

export function formatPrices(prices: PriceVariant[]): string[] {
  const formatted: string[] = [];
  for (const variant of prices) {
    const text = formatVariant(variant);
    if (text != null) {
      formatted.push(text);
    }
  }
  return formatted;
}

export function isPriceless(prices: PriceVariant[]): boolean {
  return formatPrices(prices).length === 0;
}
