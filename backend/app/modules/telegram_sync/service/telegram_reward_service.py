from __future__ import annotations

import hmac
from datetime import datetime, timedelta, timezone
from hashlib import sha256

from app.config import Settings
from app.core.errors import AppError
from app.infrastructure.db.models import CurrencyTransactionType, TelegramRewardClaim
from app.modules.economy.service.wallet_service import WalletService
from app.modules.telegram_sync.model.telegram import TelegramRewardClaimRead, TelegramRewardClaimWrite
from app.modules.telegram_sync.repository.telegram_repository import TelegramSyncRepository


class TelegramRewardService:
    def __init__(
        self,
        repo: TelegramSyncRepository,
        wallet: WalletService,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._wallet = wallet
        self._settings = settings

    async def claim_reward(self, body: TelegramRewardClaimWrite) -> TelegramRewardClaimRead:
        existing = await self._repo.get_reward_claim_by_claim_id(body.claim_id)
        if existing is not None:
            return self._to_read(existing)

        now = datetime.now(timezone.utc)
        occurred_at = self._normalize_occurred_at(body.occurred_at)
        verification_error = self._validate_claim(body, occurred_at=occurred_at)

        claim = TelegramRewardClaim(
            claim_id=body.claim_id,
            telegram_user_id=body.telegram_user_id,
            reward_tokens=body.reward_tokens,
            reason=body.reason,
            challenge_key=body.challenge_key,
            occurred_at=occurred_at,
            signature=body.signature,
            verified=False,
            verification_error=verification_error,
            created_at=now,
            meta={"source": "telegram_game"},
        )

        user = await self._repo.get_user_by_telegram_user_id(body.telegram_user_id)
        if user is None:
            claim.verification_error = claim.verification_error or "telegram_user_not_found"
            await self._repo.create_reward_claim(claim)
            return self._to_read(claim)

        claim.user_id = user.id

        if claim.verification_error is not None:
            await self._repo.create_reward_claim(claim)
            return self._to_read(claim)

        await self._wallet.ensure_wallet(user.id)
        await self._wallet.adjust(
            user_id=user.id,
            amount=body.reward_tokens,
            reason=CurrencyTransactionType.surprise_reward,
            context=f"tg_reward_claim:{body.claim_id}",
            metadata={
                "telegram_user_id": body.telegram_user_id,
                "challenge_key": body.challenge_key,
                "reason": body.reason,
                "claim_id": body.claim_id,
            },
            now=now,
        )
        wallet = await self._wallet.get_wallet(user, limit=1)

        claim.verified = True
        claim.applied_at = now
        claim.meta = {
            "source": "telegram_game",
            "balance_after": wallet.balance,
            "applied": True,
        }
        await self._repo.create_reward_claim(claim)
        return self._to_read(claim)

    def _validate_claim(self, body: TelegramRewardClaimWrite, *, occurred_at: datetime) -> str | None:
        secret = self._settings.telegram_reward_signing_secret
        if not secret:
            raise AppError(
                code="telegram_reward_not_configured",
                message="Telegram reward verification is not configured.",
                status_code=503,
            )

        if body.reward_tokens > self._settings.telegram_reward_max_tokens:
            return "reward_exceeds_max_tokens"

        max_age = timedelta(hours=self._settings.telegram_reward_max_age_hours)
        now = datetime.now(timezone.utc)
        if now - occurred_at > max_age:
            return "reward_claim_expired"

        payload = self._signature_payload(body, occurred_at=occurred_at)
        expected_signature = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), sha256).hexdigest()
        if not hmac.compare_digest(expected_signature, body.signature.lower()):
            return "invalid_signature"

        return None

    @staticmethod
    def _normalize_occurred_at(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _signature_payload(body: TelegramRewardClaimWrite, *, occurred_at: datetime) -> str:
        challenge_key = body.challenge_key or ""
        return "|".join(
            [
                body.claim_id,
                str(body.telegram_user_id),
                str(body.reward_tokens),
                body.reason,
                challenge_key,
                occurred_at.isoformat(),
            ]
        )

    @staticmethod
    def _to_read(claim: TelegramRewardClaim) -> TelegramRewardClaimRead:
        meta = claim.meta or {}
        balance_after = meta.get("balance_after") if isinstance(meta, dict) else None
        if not isinstance(balance_after, int):
            balance_after = None

        return TelegramRewardClaimRead(
            claim_id=claim.claim_id,
            telegram_user_id=int(claim.telegram_user_id),
            reward_tokens=int(claim.reward_tokens),
            verified=bool(claim.verified),
            applied=claim.applied_at is not None,
            verification_error=claim.verification_error,
            applied_at=claim.applied_at,
            balance_after=balance_after,
        )
