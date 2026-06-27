import { describe, expect, it } from "vitest";
import { bicValid, ibanValidation, sirenReason, sirenValid, siretReason, siretValid } from "@/domain/validators";

const ZERO_WIDTH_SPACE = "​";

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

describe("validation reason distinguishes length from checksum", () => {
  it("reports the SIREN failure reason", () => {
    expect(sirenReason("552 100 554")).toBe(null);
    expect(sirenReason("12345")).toBe("length");
    expect(sirenReason("552 100 555")).toBe("checksum");
  });

  it("flags a full-length but mistyped SIRET as a checksum failure, not a length one", () => {
    expect(siretReason("552 100 554 00021")).toBe(null);
    expect(siretReason("123")).toBe("length");
    expect(siretReason("552 100 554 00022")).toBe("checksum");
  });

  it("reports the IBAN failure reason", () => {
    expect(ibanValidation("FR14 2004 1010 0505 0001 3M02 606").reason).toBe(null);
    expect(ibanValidation("FR1").reason).toBe("length");
    expect(ibanValidation("FR14 2004 1010 0505 0001 3M02 607").reason).toBe("checksum");
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

  it("ignores stray separators and invisible characters", () => {
    expect(ibanValidation("FR14-2004-1010-0505-0001-3M02-606").valid).toBe(true);
    expect(ibanValidation(`FR1420041010050500013M02${ZERO_WIDTH_SPACE}606`).valid).toBe(true);
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

  it("ignores stray separators and invisible characters", () => {
    expect(bicValid("BNPA-FR-PP")).toBe(true);
    expect(bicValid(`BNPAFRPP${ZERO_WIDTH_SPACE}XXX`)).toBe(true);
  });
});
