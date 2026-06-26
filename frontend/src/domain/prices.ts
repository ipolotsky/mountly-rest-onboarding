import type { PriceVariant } from "@/types/contract";

// Strip currency symbols/spaces and turn a European decimal comma into a dot.
function stripToNumeric(raw: string): string {
  return raw
    .replace(/€/g, "")
    .replace(/eur/gi, "")
    .replace(/\s/g, "")
    .replace(",", ".")
    .trim();
}

// Normalize a user-entered amount to a plain double string with at most 2 decimals.
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
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(2);
}

// The value shown in a numeric input while editing: numeric only, no currency symbol.
export function amountForEdit(amount: string | null): string {
  if (amount == null) {
    return "";
  }
  return stripToNumeric(amount);
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
