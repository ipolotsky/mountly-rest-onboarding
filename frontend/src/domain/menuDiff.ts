import type { MenuBlock, MenuItem } from "@/types/contract";

export type ItemHighlight = "new" | "changed";

function itemSignature(item: MenuItem): string {
  const prices = item.prices.map((x) => `${x.label ?? ""}:${x.amount ?? ""}`).join("|");
  return `${item.name.value ?? ""}::${item.description.value ?? ""}::${prices}`;
}

function collectItems(menu: MenuBlock): Map<string, MenuItem> {
  const map = new Map<string, MenuItem>();
  for (const group of menu.groups) {
    for (const item of group.items) {
      map.set(item.id, item);
    }
  }
  return map;
}

// Diff a menu before vs after a parse: ids that are brand new vs ids whose content changed.
export function diffMenu(before: MenuBlock, after: MenuBlock): Map<string, ItemHighlight> {
  const highlights = new Map<string, ItemHighlight>();
  const beforeItems = collectItems(before);

  for (const [id, afterItem] of collectItems(after)) {
    const beforeItem = beforeItems.get(id);
    if (beforeItem == null) {
      highlights.set(id, "new");
    } else if (itemSignature(beforeItem) !== itemSignature(afterItem)) {
      highlights.set(id, "changed");
    }
  }
  return highlights;
}
