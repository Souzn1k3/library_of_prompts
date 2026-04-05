from __future__ import annotations

import uuid

from app.core.errors import AppError, NotFoundError
from app.infrastructure.db.models import MarketplacePayoutStatus
from app.modules.marketplace.model.marketplace import MarketplacePayoutRead


class MarketplacePayoutStatusMixin:
    async def mark_payout_processing(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            return self.payout_to_read(payout)
        if payout.status in {MarketplacePayoutStatus.failed, MarketplacePayoutStatus.canceled}:
            raise AppError(
                code="payout_not_processable",
                message="This payout can no longer be processed.",
                status_code=409,
            )
        payout = await self.sync_reserved_payout(payout)
        if payout.purchase_count <= 0:
            raise AppError(
                code="payout_empty",
                message="This payout no longer has eligible earnings attached.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.processing
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)

    async def fail_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be failed.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.failed
        await self.release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)

    async def cancel_payout(self, *, payout_id: uuid.UUID) -> MarketplacePayoutRead:
        payout = await self._repo.get_payout_by_id(payout_id, for_update=True)
        if payout is None:
            raise NotFoundError("marketplace_payout", str(payout_id))
        if payout.status == MarketplacePayoutStatus.paid:
            raise AppError(
                code="payout_already_paid",
                message="A paid payout cannot be canceled.",
                status_code=409,
            )
        payout.status = MarketplacePayoutStatus.canceled
        await self.release_payout_reservations(payout)
        await self._repo.save_payout(payout)
        return self.payout_to_read(payout)
