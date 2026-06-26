// Builders for confirm-time analytics events. These compare the parsed snapshot (what the parser
// originally returned) against the current edited state, so the admin dashboard can compute
// auto-fill acceptance, hand-added share, and per-group resolution honestly.

import type {
  BankingBlock,
  BankingFieldName,
  Field,
  LegalBlock,
  LegalFieldName,
  MenuBlock,
  MenuGroup,
} from "@/types/contract";

export type DocType = "legal" | "banking" | "menu";
export type FieldResolution = "accepted_as_is" | "edited" | "cleared" | "added_manually" | "left_empty";

export interface FieldResolvedEvent {
  step: number;
  doc_type: DocType;
  field_name: string;
  parsed_value_present: boolean;
  confidence: number | null;
  resolution: FieldResolution;
}

export interface MenuGroupResolvedEvent {
  group_name: string;
  items_parsed: number;
  items_final: number;
  items_added_manually: number;
  items_edited: number;
  items_removed: number;
  low_confidence_items: number;
}

function hasValue(field: Field | undefined): boolean {
  return field != null && field.value != null && field.value.length > 0;
}

function resolveField(parsed: Field | undefined, current: Field): FieldResolution {
  const parsedPresent = hasValue(parsed);
  const currentPresent = hasValue(current);

  if (current.provenance === "user_added") {
    return "added_manually";
  }
  if (current.provenance === "user_edited" || current.provenance === "user_confirmed") {
    if (!currentPresent) {
      return parsedPresent ? "cleared" : "left_empty";
    }
    return "edited";
  }
  if (currentPresent) {
    return "accepted_as_is";
  }
  return parsedPresent ? "cleared" : "left_empty";
}

function buildFieldEvents<Name extends string>(
  step: number,
  docType: DocType,
  names: Name[],
  parsedFields: Record<Name, Field> | null,
  currentFields: Record<Name, Field>,
): FieldResolvedEvent[] {
  const events: FieldResolvedEvent[] = [];
  for (const name of names) {
    const parsed = parsedFields?.[name];
    const current = currentFields[name];
    events.push({
      step: step,
      doc_type: docType,
      field_name: name,
      parsed_value_present: hasValue(parsed),
      confidence: parsed?.confidence ?? current.confidence,
      resolution: resolveField(parsed, current),
    });
  }
  return events;
}

const LEGAL_FIELDS: LegalFieldName[] = [
  "legal_name",
  "siren",
  "siret",
  "legal_form",
  "registered_address",
  "legal_representative",
];

const BANKING_FIELDS: BankingFieldName[] = ["account_holder", "bank_name", "iban", "bic"];

export function buildLegalFieldEvents(parsed: LegalBlock | null, current: LegalBlock): FieldResolvedEvent[] {
  return buildFieldEvents(1, "legal", LEGAL_FIELDS, parsed?.fields ?? null, current.fields);
}

export function buildBankingFieldEvents(parsed: BankingBlock | null, current: BankingBlock): FieldResolvedEvent[] {
  return buildFieldEvents(2, "banking", BANKING_FIELDS, parsed?.fields ?? null, current.fields);
}

function isParserItem(provenance: MenuGroup["items"][number]["provenance"]): boolean {
  return provenance === "parser";
}

export function buildMenuGroupEvents(parsed: MenuBlock | null, current: MenuBlock): MenuGroupResolvedEvent[] {
  const events: MenuGroupResolvedEvent[] = [];
  for (const group of current.groups) {
    const parsedGroup = parsed?.groups.find((x) => x.id === group.id || x.name === group.name) ?? null;
    const parsedItemIds = new Set((parsedGroup?.items ?? []).map((x) => x.id));

    let itemsAddedManually = 0;
    let itemsEdited = 0;
    let lowConfidenceItems = 0;
    for (const item of group.items) {
      if (item.provenance === "user_added") {
        itemsAddedManually += 1;
      } else if (item.provenance === "user_edited" || item.provenance === "user_confirmed") {
        itemsEdited += 1;
      }
      if (item.name.status === "low_confidence" || item.description.status === "low_confidence") {
        lowConfidenceItems += 1;
      }
    }

    const itemsParsed = (parsedGroup?.items ?? []).filter((x) => isParserItem(x.provenance)).length;
    const survivingParsedIds = group.items.filter((x) => parsedItemIds.has(x.id)).length;
    const itemsRemoved = Math.max(itemsParsed - survivingParsedIds, 0);

    events.push({
      group_name: group.name,
      items_parsed: itemsParsed,
      items_final: group.items.length,
      items_added_manually: itemsAddedManually,
      items_edited: itemsEdited,
      items_removed: itemsRemoved,
      low_confidence_items: lowConfidenceItems,
    });
  }
  return events;
}
