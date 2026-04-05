from __future__ import annotations

from app.core.errors import NotFoundError
from app.core.tiers import can_view_restricted_category, mask_body_if_needed
from app.infrastructure.db.models import Prompt, User
from app.modules.catalog.model.prompt import PromptListItem, PromptRead, StoreUnlockOffer
from app.modules.marketplace.model.marketplace import PromptAccessRead, PromptPriceRead


def to_list_item(
    row: Prompt,
    *,
    access: PromptAccessRead | None = None,
) -> PromptListItem:
    contributor = row.author.contributor_profile if row.author and row.author.contributor_profile else None
    quality_score = row.quality_metrics.quality_score if row.quality_metrics is not None else 0
    price = (
        PromptPriceRead(
            price_rub=row.pricing.price_rub,
            price_lumens=row.pricing.price_lumens,
            commission_percent=row.pricing.commission_percent,
        )
        if row.pricing is not None and row.pricing.is_active
        else None
    )
    return PromptListItem(
        id=row.id,
        slug=row.slug,
        title=row.title,
        summary=row.summary,
        status=row.status,
        technique=row.technique,
        moderation_state=row.moderation_state,
        category_id=row.category_id,
        author_id=row.author_id,
        created_at=row.created_at,
        is_premium=row.is_premium,
        is_paid=bool(row.pricing and row.pricing.is_active),
        difficulty=row.difficulty,
        output_type=row.output_type,
        price=price,
        access=access,
        use_cases=[link.use_case.slug for link in row.use_case_links if link.use_case is not None],
        model_compatibility=[link.model.slug for link in row.model_links if link.model is not None],
        tags=[link.tag.slug for link in row.tag_links if link.tag is not None],
        save_count=row.stats.save_count if row.stats else 0,
        copy_count=row.stats.copy_count if row.stats else 0,
        quality_score=quality_score,
        contributor_slug=contributor.slug if contributor else None,
        contributor_tier=contributor.reputation_tier if contributor else None,
        contributor_reputation_score=contributor.reputation_score if contributor else None,
        author_display_name=row.author.display_name if row.author is not None else None,
    )


def apply_read_gating(
    row: Prompt,
    *,
    viewer: User | None,
    locked: bool,
    unlock_offer: StoreUnlockOffer | None = None,
    access: PromptAccessRead | None = None,
) -> PromptRead:
    if row.category and row.category.is_restricted and not can_view_restricted_category(viewer):
        raise NotFoundError("prompt", row.slug)

    body = mask_body_if_needed(body=row.body, locked=locked)
    base = to_list_item(row, access=access)
    return PromptRead(**base.model_dump(), body=body, body_locked=locked, unlock_offer=unlock_offer)
