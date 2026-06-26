import { describe, expect, it } from "vitest";
import { amountForEdit, formatVariant, normalizeAmount } from "@/domain/prices";

describe("normalizeAmount (double with <= 2 decimals)", () => {
  it("turns a European comma into a dot", () => {
    expect(normalizeAmount("12,50")).toBe("12.50");
  });

  it("strips the euro symbol and spaces", () => {
    expect(normalizeAmount("3 €")).toBe("3");
    expect(normalizeAmount("12,5 EUR")).toBe("12.50");
  });

  it("rounds to two decimals", () => {
    expect(normalizeAmount("12,505")).toBe("12.51");
    expect(normalizeAmount("9.999")).toBe("10");
  });

  it("returns empty string for non-numbers", () => {
    expect(normalizeAmount("abc")).toBe("");
    expect(normalizeAmount("")).toBe("");
    expect(normalizeAmount("  ")).toBe("");
  });
});

describe("amountForEdit (numeric, no currency symbol)", () => {
  it("shows the numeric value without the euro symbol", () => {
    expect(amountForEdit("12,50 €")).toBe("12.50");
    expect(amountForEdit("3 €")).toBe("3");
  });

  it("returns empty for null", () => {
    expect(amountForEdit(null)).toBe("");
  });
});

describe("formatVariant (display with static euro suffix)", () => {
  it("appends euro to a bare number", () => {
    expect(formatVariant({ label: null, amount: "12,50" })).toBe("12.50 €");
  });

  it("prefixes the label", () => {
    expect(formatVariant({ label: "25 cl", amount: "3" })).toBe("25 cl · 3 €");
  });

  it("returns null for a price-less variant", () => {
    expect(formatVariant({ label: "25 cl", amount: null })).toBeNull();
  });
});
