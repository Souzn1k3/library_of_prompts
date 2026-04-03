from app.infrastructure.db.models import PlanTier, User, UserRole

_TIER_RANK: dict[PlanTier, int] = {
    PlanTier.free: 0,
    PlanTier.starter: 1,
    PlanTier.pro: 2,
    PlanTier.enterprise: 3,
}


def tier_rank(tier: PlanTier) -> int:
    return _TIER_RANK.get(tier, 0)


def is_staff(user: User) -> bool:
    return user.role in (UserRole.moderator, UserRole.admin)


def can_view_premium_content(user: User | None) -> bool:
    if user is None:
        return False
    if is_staff(user):
        return True
    return tier_rank(user.plan_tier) >= tier_rank(PlanTier.starter)


def can_view_restricted_category(user: User | None) -> bool:
    if user is None:
        return False
    if is_staff(user):
        return True
    return tier_rank(user.plan_tier) >= tier_rank(PlanTier.pro)


def can_view_lesson(user: User | None, min_tier: PlanTier) -> bool:
    if user is None:
        return tier_rank(min_tier) == 0
    if is_staff(user):
        return True
    return tier_rank(user.plan_tier) >= tier_rank(min_tier)


def mask_body_if_needed(*, body: str, locked: bool, preview_chars: int = 320) -> str:
    if not locked:
        return body
    if len(body) <= preview_chars:
        return body
    return body[:preview_chars].rstrip() + "\n\n…"
