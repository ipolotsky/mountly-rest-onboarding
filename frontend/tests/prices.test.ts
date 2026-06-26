import { describe, expect, it } from "vitest";
import { amountForEdit, formatVariant, normalizeAmount, sanitizePriceInput } from "@/domain/prices";

describe("normalizeAmount (European comma decimal, <= 2 decimals)", () => {
  it("keeps a European comma as the decimal separator", () => {
    expect(normalizeAmount("12,50")).toBe("12,50");
  });

  it("strips the euro symbol and spaces", () => {
    expect(normalizeAmount("3 €")).toBe("3");
    expect(normalizeAmount("12,5 EUR")).toBe("12,50");
  });

  it("rounds to two decimals", () => {
    expect(normalizeAmount("12,505")).toBe("12,51");
    expect(normalizeAmount("9.999")).toBe("10");
  });

  it("returns empty string for non-numbers", () => {
    expect(normalizeAmount("abc")).toBe("");
    expect(normalizeAmount("")).toBe("");
    expect(normalizeAmount("  ")).toBe("");
  });
});

describe("sanitizePriceInput (digits + a single comma only)", () => {
  it("drops letters and currency symbols", () => {
    expect(sanitizePriceInput("12a,5b0 €")).toBe("12,50");
    expect(sanitizePriceInput("free")).toBe("");
  });

  it("keeps only the first comma", () => {
    expect(sanitizePriceInput("1,2,3")).toBe("1,23");
  });

  it("caps the decimals at two", () => {
    expect(sanitizePriceInput("12,5099")).toBe("12,50");
  });

  it("leaves a plain integer untouched", () => {
    expect(sanitizePriceInput("10")).toBe("10");
  });
});

describe("amountForEdit (digits + comma, no currency symbol)", () => {
  it("shows the value with a comma and without the euro symbol", () => {
    expect(amountForEdit("12,50 €")).toBe("12,50");
    expect(amountForEdit("12.50")).toBe("12,50");
    expect(amountForEdit("3 €")).toBe("3");
  });

  it("returns empty for null", () => {
    expect(amountForEdit(null)).toBe("");
  });
});

describe("formatVariant (display with static euro suffix)", () => {
  it("appends euro to a bare number", () => {
    expect(formatVariant({ label: null, amount: "12,50" })).toBe("12,50 €");
  });

  it("prefixes the label", () => {
    expect(formatVariant({ label: "25 cl", amount: "3" })).toBe("25 cl · 3 €");
  });

  it("returns null for a price-less variant", () => {
    expect(formatVariant({ label: "25 cl", amount: null })).toBeNull();
  });
});
