import type { PriceVariant } from "@/types/contract";

function withSymbol(amount: string): string {
  const trimmed = amount.trim();
  if (trimmed.includes("€") || /eur/i.test(trimmed)) {
    return trimmed;
  }
  return `${trimmed} €`;
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
