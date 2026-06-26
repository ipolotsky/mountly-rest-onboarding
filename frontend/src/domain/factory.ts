// Factories for crash-safe empty state. Every view must render from these without throwing,
// so the shapes here are the canonical "all missing" baseline.

import type {
  BankingBlock,
  Device,
  Field,
  LegalBlock,
  Locale,
  MenuBlock,
  MenuGroup,
  MenuItem,
  Onboarding,
  Provenance,
} from "@/types/contract";

export const UNCATEGORIZED_GROUP_NAME = "Sans catégorie";

let idCounter = 0;

export function generateLocalId(prefix: string): string {
  idCounter += 1;
  const random = Math.random().toString(36).slice(2, 8);
  return `${prefix}_${Date.now().toString(36)}_${idCounter}_${random}`;
}

export function emptyField(): Field {
  return {
    value: null,
    status: "missing",
    confidence: null,
    provenance: "parser",
    valid: null,
  };
}

export function userField(value: string | null, provenance: Provenance = "user_edited"): Field {
  return {
    value: value,
    status: value != null && value.length > 0 ? "present" : "missing",
    confidence: null,
    provenance: provenance,
    valid: null,
  };
}

export function emptyLegalBlock(): LegalBlock {
  return {
    status: "empty",
    fields: {
      legal_name: emptyField(),
      siren: emptyField(),
      siret: emptyField(),
      legal_form: emptyField(),
      registered_address: emptyField(),
      legal_representative: emptyField(),
    },
    registry: null,
  };
}

export function emptyBankingBlock(): BankingBlock {
  return {
    status: "empty",
    fields: {
      account_holder: emptyField(),
      bank_name: emptyField(),
      iban: emptyField(),
      bic: emptyField(),
    },
    cross_doc_holder_match: null,
  };
}

export function emptyMenuBlock(): MenuBlock {
  return {
    status: "empty",
    groups: [],
    source_files: [],
  };
}

export function emptyMenuItem(): MenuItem {
  return {
    id: generateLocalId("item"),
    name: userField(null, "user_added"),
    description: userField(null, "user_added"),
    prices: [],
    confidence: null,
    provenance: "user_added",
  };
}

export function emptyMenuGroup(name: string): MenuGroup {
  return {
    id: generateLocalId("group"),
    name: name,
    items: [],
    provenance: "user_added",
    source_file_ids: [],
  };
}

export function emptyOnboarding(id: string, locale: Locale, device: Device): Onboarding {
  const now = new Date().toISOString();
  return {
    id: id,
    created_at: now,
    updated_at: now,
    locale: locale,
    device: device,
    step: 1,
    confirmed: { legal: false, banking: false, menu: false },
    legal: emptyLegalBlock(),
    banking: emptyBankingBlock(),
    menu: emptyMenuBlock(),
  };
}
