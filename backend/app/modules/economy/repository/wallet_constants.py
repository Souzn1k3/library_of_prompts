from app.infrastructure.db.models import CurrencyTransactionType

MISSION_EARNING_REASONS = (
    CurrencyTransactionType.mission_reward,
    CurrencyTransactionType.surprise_reward,
    CurrencyTransactionType.spend_streak_bonus,
    CurrencyTransactionType.rank_bonus,
)

SEGMENT_SPEND_REASONS = (
    CurrencyTransactionType.store_purchase,
    CurrencyTransactionType.boost_purchase,
    CurrencyTransactionType.upgrade_purchase,
    CurrencyTransactionType.marketplace_purchase,
)
