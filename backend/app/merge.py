import re

from app.schemas import MenuGroup, MenuItem

UNCATEGORIZED_GROUP_NAME = "Sans catégorie"
PRESERVED_PROVENANCE = ("user_edited", "user_added", "user_confirmed")


def _normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _item_key(item: MenuItem) -> str:
    return _normalize(item.name.value or "")


def merge_menu_groups(
    existing: list[MenuGroup], parsed: list[MenuGroup]
) -> list[MenuGroup]:
    merged: list[MenuGroup] = [group.model_copy(deep=True) for group in existing]
    index_by_name: dict[str, int] = {
        _normalize(group.name): position for position, group in enumerate(merged)
    }

    for parsed_group in parsed:
        normalized = _normalize(parsed_group.name)
        if normalized in index_by_name:
            target = merged[index_by_name[normalized]]
            _merge_items(target, parsed_group.items, parsed_group.source_file_ids)
        else:
            new_group = parsed_group.model_copy(deep=True)
            index_by_name[normalized] = len(merged)
            merged.append(new_group)

    _ensure_uncategorized(merged)
    return merged


def _merge_items(
    target: MenuGroup, parsed_items: list[MenuItem], source_file_ids: list[str]
) -> None:
    for file_id in source_file_ids:
        if file_id not in target.source_file_ids:
            target.source_file_ids.append(file_id)

    existing_keys = {_item_key(item) for item in target.items}
    for item in parsed_items:
        if _item_key(item) in existing_keys:
            # Re-parse must never overwrite a field the user touched; an item that already
            # exists (by normalized name) is kept as-is. Filling empties only is the minimum.
            continue
        target.items.append(item.model_copy(deep=True))
        existing_keys.add(_item_key(item))


def _ensure_uncategorized(groups: list[MenuGroup]) -> None:
    has_bucket = any(group.name == UNCATEGORIZED_GROUP_NAME for group in groups)
    if has_bucket:
        return
    if not groups:
        return
    groups.append(
        MenuGroup(
            id="group_uncategorized",
            name=UNCATEGORIZED_GROUP_NAME,
            items=[],
            provenance="parser",
            source_file_ids=[],
        )
    )
