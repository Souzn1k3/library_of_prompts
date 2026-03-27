import uuid

from app.core.tiers import tier_rank
from app.infrastructure.db.models import PlanTier, SubscriptionStatus
from app.modules.billing.repository.billing_repository import BillingRepository
from app.modules.identity.repository.user_repository import UserRepository


class EntitlementService:
    def __init__(self, billing_repo: BillingRepository, user_repo: UserRepository) -> None:
        self._billing_repo = billing_repo
        self._user_repo = user_repo

    async def recalculate_user_tier(self, user_id: uuid.UUID) -> PlanTier:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            return PlanTier.free

        eligible_subscriptions = await self._billing_repo.list_entitled_subscriptions_for_user(
            user_id,
            statuses=(
                SubscriptionStatus.active,
                SubscriptionStatus.trialing,
                SubscriptionStatus.past_due,
            ),
        )

        if eligible_subscriptions:
            target_tier = max(
                (sub.plan.tier for sub in eligible_subscriptions if sub.plan is not None),
                key=tier_rank,
                default=PlanTier.free,
            )
        else:
            has_customer = await self._billing_repo.has_billing_customer(user_id)
            target_tier = PlanTier.free if has_customer else user.plan_tier

        if user.plan_tier != target_tier:
            user.plan_tier = target_tier
            await self._user_repo.save(user)

        return target_tier
