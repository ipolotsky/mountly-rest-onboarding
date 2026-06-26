import { describe, expect, it } from "vitest";
import type { Field, MenuBlock, MenuItem } from "@/types/contract";
import { diffMenu } from "@/domain/menuDiff";

function field(value: string | null): Field {
  return { value: value, status: value == null ? "missing" : "present", confidence: null, provenance: "parser", valid: null };
}

function item(id: string, name: string, amount: string | null = null): MenuItem {
  return {
    id: id,
    name: field(name),
    description: field(null),
    prices: amount == null ? [] : [{ label: null, amount: amount }],
    confidence: null,
    provenance: "parser",
  };
}

function block(items: MenuItem[]): MenuBlock {
  return { status: "ready", groups: [{ id: "g1", name: "Plats", items: items, provenance: "parser", source_file_ids: [] }], source_files: [] };
}

describe("diffMenu (fading highlight diff)", () => {
  it("marks brand-new items as new", () => {
    const before = block([item("i1", "Steak")]);
    const after = block([item("i1", "Steak"), item("i2", "Tartare")]);
    const highlights = diffMenu(before, after);
    expect(highlights.get("i2")).toBe("new");
    expect(highlights.has("i1")).toBe(false);
  });

  it("marks changed items as changed", () => {
    const before = block([item("i1", "Steak", "10")]);
    const after = block([item("i1", "Steak", "12")]);
    const highlights = diffMenu(before, after);
    expect(highlights.get("i1")).toBe("changed");
  });

  it("does not flag unchanged items", () => {
    const before = block([item("i1", "Steak", "10")]);
    const after = block([item("i1", "Steak", "10")]);
    const highlights = diffMenu(before, after);
    expect(highlights.size).toBe(0);
  });
});
