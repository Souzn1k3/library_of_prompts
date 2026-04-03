from __future__ import annotations

import uuid
from datetime import datetime, time, timedelta, timezone

import pytest
from sqlalchemy import select

from app.infrastructure.db.models import (
    AnalyticsEvent,
    CurrencyTransaction,
    CurrencyTransactionType,
    EconomyDailyKpi,
    PurchaseStatus,
    StoreItem,
    StoreItemKind,
    User,
    UserRole,
    UserCurrencyBalance,
    UserPurchase,
)
from app.infrastructure.db.session import async_session_maker
from app.modules.economy.repository.kpi_repository import EconomyKpiRepository
from app.modules.economy.service.kpi_service import EconomyKpiService
from tests.helpers.db_users import set_user_role


@pytest.mark.asyncio
async def test_economy_kpi_aggregation_summary_and_export(async_client, unique_email: str):
    admin_email = unique_email
    member_email = f"member_{uuid.uuid4().hex[:10]}@example.com"

    reg_admin = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": admin_email,
            "password": "password123",
            "display_name": "Admin",
        },
    )
    assert reg_admin.status_code == 201

    reg_member = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": member_email,
            "password": "password123",
            "display_name": "Member",
        },
    )
    assert reg_member.status_code == 201

    await set_user_role(email=admin_email, role=UserRole.admin)

    login_admin = await async_client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "password123"},
    )
    assert login_admin.status_code == 200
    admin_token = login_admin.json()["access_token"]

    now = datetime.now(timezone.utc)
    today = now.date()
    day_start = datetime.combine(today, time.min, tzinfo=timezone.utc)
    created_at = day_start + timedelta(hours=1)
    tx_earned_at = day_start + timedelta(hours=2)
    first_purchase_at = day_start + timedelta(hours=4)
    second_purchase_at = day_start + timedelta(hours=7)

    async with async_session_maker() as session:
        member = (
            await session.execute(select(User).where(User.email == member_email.lower()))
        ).scalar_one()
        member.created_at = created_at

        store_item = StoreItem(
            slug=f"pytest-kpi-item-{uuid.uuid4().hex[:8]}",
            title="Pytest KPI Item",
            description="Item for KPI integration test",
            price=5,
            kind=StoreItemKind.starter,
            is_active=True,
            sort_order=1,
        )
        session.add(store_item)
        await session.flush()

        session.add(
            UserCurrencyBalance(
                user_id=member.id,
                balance=7,
                total_earned=12,
                total_spent=5,
            )
        )
        session.add(
            CurrencyTransaction(
                user_id=member.id,
                amount=12,
                balance_after=12,
                reason=CurrencyTransactionType.mission_reward,
                context="pytest:earned",
                created_at=tx_earned_at,
            )
        )
        session.add(
            CurrencyTransaction(
                user_id=member.id,
                amount=-5,
                balance_after=7,
                reason=CurrencyTransactionType.store_purchase,
                context="pytest:spent",
                source_id=store_item.id,
                created_at=first_purchase_at,
            )
        )
        session.add(
            UserPurchase(
                user_id=member.id,
                store_item_id=store_item.id,
                price_paid=5,
                status=PurchaseStatus.completed,
                created_at=first_purchase_at,
            )
        )
        session.add(
            UserPurchase(
                user_id=member.id,
                store_item_id=store_item.id,
                price_paid=3,
                status=PurchaseStatus.completed,
                created_at=second_purchase_at,
            )
        )
        session.add(
            AnalyticsEvent(
                event_id=f"pytest_assign_{uuid.uuid4().hex[:16]}",
                event_name="economy_experiment_assigned",
                user_id=member.id,
                session_id="pytest-session",
                source="server",
                context_page="/api/v1/store",
                context_feature="ab_assignment",
                metadata_json={
                    "experiment_name": "economy_loop_v2",
                    "experiment_variant": "control",
                    "payer_status": "non_payer",
                },
                occurred_at=tx_earned_at,
            )
        )
        session.add(
            AnalyticsEvent(
                event_id=f"pytest_store_view_{uuid.uuid4().hex[:16]}",
                event_name="store_offer_viewed",
                user_id=member.id,
                session_id="pytest-session",
                source="server",
                context_page="/api/v1/store",
                context_feature="offer_impression",
                metadata_json={"experiment_name": "economy_loop_v2", "experiment_variant": "control"},
                occurred_at=tx_earned_at + timedelta(minutes=1),
            )
        )
        session.add(
            AnalyticsEvent(
                event_id=f"pytest_wallet_view_{uuid.uuid4().hex[:16]}",
                event_name="page_viewed",
                user_id=member.id,
                session_id="pytest-session",
                source="web",
                context_page="/wallet",
                context_feature="navigation",
                metadata_json={},
                occurred_at=tx_earned_at + timedelta(minutes=2),
            )
        )
        session.add(
            AnalyticsEvent(
                event_id=f"pytest_mission_completed_{uuid.uuid4().hex[:16]}",
                event_name="mission_completed",
                user_id=member.id,
                session_id="pytest-session",
                source="server",
                context_page="/api/v1/missions/events",
                context_feature="mission_progress",
                metadata_json={"experiment_name": "economy_loop_v2", "experiment_variant": "control"},
                occurred_at=tx_earned_at + timedelta(minutes=3),
            )
        )
        await session.commit()

    async with async_session_maker() as session:
        svc = EconomyKpiService(EconomyKpiRepository(session))
        affected = await svc.aggregate_date_range(start_date=today, end_date=today)
        await session.commit()
        assert affected >= 2

        kpi_rows = (
            await session.execute(select(EconomyDailyKpi).where(EconomyDailyKpi.date == today))
        ).scalars().all()
        assert len(kpi_rows) >= 2
        assert {"control", "treatment"}.issubset({row.cohort for row in kpi_rows})
        assert sum(int(row.first_purchase_users) for row in kpi_rows) >= 1
        assert sum(int(row.second_purchase_48h_users) for row in kpi_rows) >= 1

    summary_response = await async_client.get(
        "/api/v1/admin/economy/kpis/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert "today" in summary_payload
    assert "yesterday" in summary_payload
    assert "last_7_days" in summary_payload
    assert "control_vs_variant" in summary_payload

    export_response = await async_client.get(
        "/api/v1/admin/economy/kpis/export?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert export_response.status_code == 200
    assert export_response.headers.get("content-type", "").startswith("text/csv")
    assert export_response.content.startswith(b"\xef\xbb\xbf")
    csv_text = export_response.content.decode("utf-8-sig")
    csv_lines = csv_text.splitlines()
    assert csv_lines[0] == "sep=,"
    assert "date,experiment_name,cohort,active_users,new_users" in csv_lines[1]
