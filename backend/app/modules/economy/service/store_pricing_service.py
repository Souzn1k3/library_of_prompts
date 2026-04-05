from app.infrastructure.db.models import StoreItem, StoreItemKind
from app.modules.economy.config.tuning import PRICE_BAND_THRESHOLDS
from app.modules.economy.model.store import StoreItemRead


class StorePricingService:
    def price_band(self, price: int) -> str:
        for threshold, label in PRICE_BAND_THRESHOLDS:
            if price <= threshold:
                return label
        return "premium"

    def item_tags(self, item: StoreItem) -> list[str]:
        tags: list[str] = []
        if item.kind == StoreItemKind.starter:
            tags.append("starter")
        if item.kind == StoreItemKind.boost:
            tags.append("boost")
        if item.meta and isinstance(item.meta.get("tags"), list):
            tags.extend(str(tag) for tag in item.meta.get("tags", []) if tag)
        if item.kind == StoreItemKind.prompt_bundle and "best_value" not in tags:
            tags.append("best_value")

        unique_tags: list[str] = []
        for tag in tags:
            if tag not in unique_tags:
                unique_tags.append(tag)
        return unique_tags

    def pick_best_item(self, items: list[StoreItemRead]) -> StoreItemRead | None:
        purchasable = [
            item
            for item in items
            if item.is_active and not item.owned and (item.availability is None or item.availability > 0)
        ]
        if not purchasable:
            return None

        affordable = [item for item in purchasable if item.is_affordable]
        if affordable:
            return sorted(
                affordable,
                key=lambda item: ("starter" not in item.tags, item.price, item.title.lower()),
            )[0]
        return sorted(
            purchasable,
            key=lambda item: (item.remaining_lumens, item.price, item.title.lower()),
        )[0]
