import uuid

from app.infrastructure.db.models import StoreItem, StoreItemKind


def extract_prompt_ids(meta: dict | None) -> set[str]:
    if not meta:
        return set()
    raw_ids: list[str] = []
    prompt_id = meta.get("prompt_id")
    if prompt_id:
        raw_ids.append(str(prompt_id))
    prompt_ids = meta.get("prompt_ids")
    if isinstance(prompt_ids, list):
        raw_ids.extend(str(item) for item in prompt_ids if item)
    return {item for item in raw_ids if item}


def item_unlocks_prompt(item: StoreItem, prompt_id: uuid.UUID) -> bool:
    prompt_id_str = str(prompt_id)
    prompt_ids = extract_prompt_ids(item.meta)
    if item.kind == StoreItemKind.premium_prompt_unlock:
        return prompt_id_str in prompt_ids
    if item.kind == StoreItemKind.prompt_bundle:
        return prompt_id_str in prompt_ids
    return False
