from __future__ import annotations

import uuid
from typing import Any

from app.infrastructure.db.models import StoreItem, StoreItemKind


def build_default_store_items(
    premium_prompts: list[Any],
    *,
    stable_ids: bool = False,
) -> list[StoreItem]:
    def make_item(*, slug: str, **kwargs: Any) -> StoreItem:
        item_kwargs = {"slug": slug, "is_active": True, **kwargs}
        if stable_ids:
            item_kwargs["id"] = uuid.uuid5(uuid.NAMESPACE_URL, f"store:{slug}")
        return StoreItem(**item_kwargs)

    defaults: list[StoreItem] = [
        make_item(
            slug="starter-mini-prompt",
            title="Starter Mini Prompt",
            description="Unlock a compact prompt you can paste instantly for clearer AI answers.",
            price=5,
            kind=StoreItemKind.starter,
            meta={
                "starter_type": "mini_prompt",
                "reward_title": "Reply starter",
                "reward_body": "Act as an expert editor. Rewrite my draft in 3 clearer bullet points with one concrete next step.",
                "tags": ["starter", "popular"],
                "synergy_categories": ["prompt"],
                "upgrade_track": "starter-track",
                "upgrade_tier": 1,
                "max_tier": 3,
                "next_upgrade_cost": 6,
            },
            sort_order=1,
        ),
        make_item(
            slug="starter-structure-fragment",
            title="Starter Structure Fragment",
            description="Get a reusable response fragment that turns vague outputs into actionable structure.",
            price=6,
            kind=StoreItemKind.starter,
            meta={
                "starter_type": "fragment",
                "reward_title": "Output fragment",
                "reward_body": "Return the answer as: 1) core idea 2) risks 3) next action 4) one better version.",
                "tags": ["starter"],
                "synergy_categories": ["prompt", "progress"],
                "upgrade_track": "starter-track",
                "upgrade_tier": 2,
                "max_tier": 3,
                "next_upgrade_cost": 8,
            },
            sort_order=2,
        ),
        make_item(
            slug="starter-spark-discount",
            title="Starter Spark Discount",
            description="Turn your first Lumens into a small checkout discount code you can use right away.",
            price=8,
            kind=StoreItemKind.starter,
            meta={
                "starter_type": "discount",
                "discount_percent": 15,
                "code_prefix": "START",
                "reward_title": "15% checkout code",
                "reward_body": "A small discount for your next checkout, unlocked with starter-tier Lumens.",
                "tags": ["starter", "best_value"],
                "synergy_categories": ["spend"],
                "upgrade_track": "starter-track",
                "upgrade_tier": 3,
                "max_tier": 3,
            },
            sort_order=3,
        ),
        make_item(
            slug="booster-s",
            title="Booster S",
            description="Increase LMN rewards by 20% for your next 3 mission completions.",
            price=5,
            kind=StoreItemKind.boost,
            meta={
                "boost_pct": 20,
                "boost_missions": 3,
                "tags": ["entry", "boost"],
                "synergy_categories": ["progress", "spend"],
                "upgrade_track": "booster-core",
                "upgrade_tier": 1,
                "max_tier": 3,
                "next_upgrade_cost": 7,
                "target_segment": "inactive",
            },
            sort_order=4,
        ),
        make_item(
            slug="booster-m",
            title="Booster M",
            description="Increase LMN rewards by 25% for your next 5 mission completions.",
            price=7,
            kind=StoreItemKind.boost,
            meta={
                "boost_pct": 25,
                "boost_missions": 5,
                "tags": ["entry", "boost"],
                "synergy_categories": ["progress", "spend"],
                "upgrade_track": "booster-core",
                "upgrade_tier": 2,
                "max_tier": 3,
                "next_upgrade_cost": 8,
                "target_segment": "balanced",
            },
            sort_order=5,
        ),
        make_item(
            slug="booster-l",
            title="Booster L",
            description="Increase LMN rewards by 30% for your next 6 mission completions.",
            price=8,
            kind=StoreItemKind.boost,
            meta={
                "boost_pct": 30,
                "boost_missions": 6,
                "tags": ["entry", "best_value", "boost"],
                "synergy_categories": ["progress", "spend"],
                "upgrade_track": "booster-core",
                "upgrade_tier": 3,
                "max_tier": 3,
                "target_segment": "hoarder",
            },
            sort_order=6,
        ),
        make_item(
            slug="weekend-premium-pass",
            title="Premium Pass - 2 days",
            description="Unlock premium prompts for a short sprint and feel the value before a bigger spend.",
            price=12,
            kind=StoreItemKind.premium_pass,
            meta={"premium_days": 2, "tags": ["popular"], "synergy_categories": ["learning"]},
            sort_order=7,
        ),
        make_item(
            slug="starter-checkout-discount",
            title="20% off first paid month",
            description="A core-tier discount that keeps your next upgrade within reach.",
            price=14,
            kind=StoreItemKind.subscription_discount,
            meta={"discount_percent": 20, "code_prefix": "BOOST", "tags": ["best_value"], "synergy_categories": ["spend"]},
            sort_order=8,
        ),
        make_item(
            slug="pro-trial-pass",
            title="Pro Pass - 7 days",
            description="Unlock premium prompts for a full week without changing your subscription yet.",
            price=30,
            kind=StoreItemKind.premium_pass,
            meta={"premium_days": 7, "tags": ["popular"], "synergy_categories": ["learning"]},
            sort_order=9,
        ),
        make_item(
            slug="first-month-discount",
            title="40% off first paid month",
            description="Trade Lumens for a personal discount code you can use on your next checkout.",
            price=45,
            kind=StoreItemKind.subscription_discount,
            meta={"discount_percent": 40, "code_prefix": "SAVE", "tags": ["best_value"], "synergy_categories": ["spend"]},
            sort_order=12,
        ),
    ]

    for index, prompt in enumerate(premium_prompts[:2], start=10):
        defaults.append(
            make_item(
                slug=f"unlock-{prompt.slug}",
                title=f"Unlock: {prompt.title}",
                description="Permanent access to this premium prompt from your personal library.",
                price=18 + (index - 10) * 4,
                kind=StoreItemKind.premium_prompt_unlock,
                meta={
                    "prompt_id": str(prompt.id),
                    "prompt_slug": prompt.slug,
                    "prompt_title": prompt.title,
                    "synergy_categories": ["prompt"],
                },
                sort_order=index,
            )
        )

    if premium_prompts:
        defaults.append(
            make_item(
                slug="prompt-power-pack",
                title="Premium Prompt Pack",
                description="Unlock a curated pack of premium prompts and keep them in your workflow forever.",
                price=42,
                kind=StoreItemKind.prompt_bundle,
                meta={
                    "prompt_ids": [str(prompt.id) for prompt in premium_prompts],
                    "prompt_slugs": [prompt.slug for prompt in premium_prompts],
                    "prompt_titles": [prompt.title for prompt in premium_prompts],
                    "tags": ["best_value"],
                    "synergy_categories": ["prompt", "progress"],
                    "upgrade_track": "bundle-track",
                    "upgrade_tier": 1,
                    "max_tier": 2,
                },
                sort_order=13,
            )
        )

    return defaults
