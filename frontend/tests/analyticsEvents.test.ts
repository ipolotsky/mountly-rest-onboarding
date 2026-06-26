import { describe, expect, it } from "vitest";
import type { BankingBlock, Field, LegalBlock, MenuBlock } from "@/types/contract";
import {
  buildBankingFieldEvents,
  buildLegalFieldEvents,
  buildMenuGroupEvents,
} from "@/domain/analyticsEvents";

function parserField(value: string | null, confidence: number | null = 0.9): Field {
  return {
    value: value,
    status: value == null ? "missing" : "present",
    confidence: confidence,
    provenance: "parser",
    valid: null,
  };
}

function editedField(value: string | null): Field {
  return {
    value: value,
    status: value == null ? "missing" : "present",
    confidence: null,
    provenance: "user_edited",
    valid: null,
  };
}

function legalBlock(fields: Partial<LegalBlock["fields"]>): LegalBlock {
  const base = {
    legal_name: parserField(null),
    siren: parserField(null),
    siret: parserField(null),
    legal_form: parserField(null),
    registered_address: parserField(null),
    legal_representative: parserField(null),
  };
  return { status: "ready", fields: { ...base, ...fields }, registry: null };
}

describe("buildLegalFieldEvents (auto-fill acceptance signal)", () => {
  it("emits one event per legal field with doc_type legal", () => {
    const parsed = legalBlock({ legal_name: parserField("Chez Pierre") });
    const events = buildLegalFieldEvents(parsed, parsed);
    expect(events.length).toBe(6);
    expect(events.every((x) => x.doc_type === "legal")).toBe(true);
    expect(events.every((x) => x.step === 1)).toBe(true);
  });

  it("marks an untouched present parsed field as accepted_as_is with parsed_value_present true", () => {
    const parsed = legalBlock({ legal_name: parserField("Chez Pierre", 0.8) });
    const events = buildLegalFieldEvents(parsed, parsed);
    const nameEvent = events.find((x) => x.field_name === "legal_name");
    expect(nameEvent?.resolution).toBe("accepted_as_is");
    expect(nameEvent?.parsed_value_present).toBe(true);
    expect(nameEvent?.confidence).toBe(0.8);
  });

  it("marks an edited field as edited and preserves parsed_value_present from the snapshot", () => {
    const parsed = legalBlock({ legal_name: parserField("Chez Pierr") });
    const current = legalBlock({ legal_name: editedField("Chez Pierre") });
    const events = buildLegalFieldEvents(parsed, current);
    const nameEvent = events.find((x) => x.field_name === "legal_name");
    expect(nameEvent?.resolution).toBe("edited");
    expect(nameEvent?.parsed_value_present).toBe(true);
  });

  it("marks a field the parser missed but the user filled as added_manually", () => {
    const parsed = legalBlock({ siret: parserField(null) });
    const current = legalBlock({
      siret: { value: "123", status: "present", confidence: null, provenance: "user_added", valid: null },
    });
    const events = buildLegalFieldEvents(parsed, current);
    const event = events.find((x) => x.field_name === "siret");
    expect(event?.resolution).toBe("added_manually");
    expect(event?.parsed_value_present).toBe(false);
  });

  it("marks a parsed field the user cleared as cleared", () => {
    const parsed = legalBlock({ legal_form: parserField("SARL") });
    const current = legalBlock({ legal_form: editedField(null) });
    const events = buildLegalFieldEvents(parsed, current);
    const event = events.find((x) => x.field_name === "legal_form");
    expect(event?.resolution).toBe("cleared");
  });
});

describe("buildBankingFieldEvents", () => {
  it("emits one event per banking field with doc_type banking and step 2", () => {
    const parsed: BankingBlock = {
      status: "ready",
      fields: {
        account_holder: parserField("SARL X"),
        bank_name: parserField("BNP"),
        iban: parserField("FR76..."),
        bic: parserField(null),
      },
      cross_doc_holder_match: null,
    };
    const events = buildBankingFieldEvents(parsed, parsed);
    expect(events.length).toBe(4);
    expect(events.every((x) => x.doc_type === "banking" && x.step === 2)).toBe(true);
    const bicEvent = events.find((x) => x.field_name === "bic");
    expect(bicEvent?.resolution).toBe("left_empty");
    expect(bicEvent?.parsed_value_present).toBe(false);
  });
});

describe("buildMenuGroupEvents", () => {
  function nameField(value: string, provenance: Field["provenance"], lowConfidence = false): Field {
    return {
      value: value,
      status: lowConfidence ? "low_confidence" : "present",
      confidence: provenance === "parser" ? 0.5 : null,
      provenance: provenance,
      valid: null,
    };
  }

  function block(groups: MenuBlock["groups"]): MenuBlock {
    return { status: "ready", groups: groups, source_files: [] };
  }

  it("computes parsed/final/added/edited/removed/low-confidence per group", () => {
    const parsed = block([
      {
        id: "g1",
        name: "Plats",
        provenance: "parser",
        source_file_ids: [],
        items: [
          { id: "i1", name: nameField("Steak", "parser"), description: parserField(null), prices: [], confidence: 0.9, provenance: "parser" },
          { id: "i2", name: nameField("Poulet", "parser"), description: parserField(null), prices: [], confidence: 0.9, provenance: "parser" },
        ],
      },
    ]);
    const current = block([
      {
        id: "g1",
        name: "Plats",
        provenance: "parser",
        source_file_ids: [],
        items: [
          { id: "i1", name: nameField("Steak frites", "user_edited"), description: parserField(null), prices: [], confidence: 0.9, provenance: "user_edited" },
          { id: "i3", name: nameField("Tartare", "user_added"), description: parserField(null), prices: [], confidence: null, provenance: "user_added" },
          { id: "i4", name: nameField("Tarte", "parser", true), description: parserField(null), prices: [], confidence: 0.4, provenance: "parser" },
        ],
      },
    ]);

    const events = buildMenuGroupEvents(parsed, current);
    expect(events.length).toBe(1);
    const event = events[0];
    expect(event?.group_name).toBe("Plats");
    expect(event?.items_parsed).toBe(2);
    expect(event?.items_final).toBe(3);
    expect(event?.items_added_manually).toBe(1);
    expect(event?.items_edited).toBe(1);
    expect(event?.items_removed).toBe(1);
    expect(event?.low_confidence_items).toBe(1);
  });
});
