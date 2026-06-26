import { describe, expect, it } from "vitest";
import { bicValid, ibanValidation, sirenValid, siretValid } from "@/domain/validators";

describe("SIREN validation (Luhn)", () => {
  it("accepts a valid SIREN", () => {
    expect(sirenValid("552 100 554")).toBe(true);
  });

  it("rejects a SIREN that fails the Luhn checksum", () => {
    expect(sirenValid("552 100 555")).toBe(false);
  });

  it("rejects a SIREN of the wrong length", () => {
    expect(sirenValid("12345")).toBe(false);
  });

  it("rejects null", () => {
    expect(sirenValid(null)).toBe(false);
  });
});

describe("SIRET validation (Luhn)", () => {
  it("accepts a valid SIRET", () => {
    expect(siretValid("552 100 554 00021")).toBe(true);
  });

  it("rejects a malformed SIRET", () => {
    expect(siretValid("552 100 554 00022")).toBe(false);
  });
});

describe("IBAN validation (mod-97)", () => {
  it("accepts a valid French IBAN", () => {
    const result = ibanValidation("FR14 2004 1010 0505 0001 3M02 606");
    expect(result.valid).toBe(true);
    expect(result.suspectIndexes).toEqual([]);
  });

  it("rejects an IBAN with a broken checksum", () => {
    expect(ibanValidation("FR14 2004 1010 0505 0001 3M02 607").valid).toBe(false);
  });

  it("flags suspect characters", () => {
    const result = ibanValidation("FR14-2004");
    expect(result.valid).toBe(false);
    expect(result.suspectIndexes.length).toBeGreaterThan(0);
  });
});

describe("BIC validation", () => {
  it("accepts an 8-character BIC", () => {
    expect(bicValid("BNPAFRPP")).toBe(true);
  });

  it("accepts an 11-character BIC", () => {
    expect(bicValid("BNPAFRPPXXX")).toBe(true);
  });

  it("rejects a too-short BIC", () => {
    expect(bicValid("BNPA")).toBe(false);
  });
});
