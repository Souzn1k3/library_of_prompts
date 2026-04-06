from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ServiceBinding:
    name: str
    container_attr: str


SERVICE_BINDINGS: tuple[ServiceBinding, ...] = (
    ServiceBinding(name="analytics", container_attr="analytics_service"),
    ServiceBinding(name="growth_ops", container_attr="growth_ops_service"),
    ServiceBinding(name="revenue_ops", container_attr="revenue_ops_service"),
    ServiceBinding(name="gtm_ops", container_attr="gtm_ops_service"),
    ServiceBinding(name="auth", container_attr="auth_service"),
    ServiceBinding(name="billing", container_attr="billing_service"),
    ServiceBinding(name="category", container_attr="category_service"),
    ServiceBinding(name="contributor", container_attr="contributor_service"),
    ServiceBinding(name="economy_insights", container_attr="economy_insights_service"),
    ServiceBinding(name="economy_kpi", container_attr="economy_kpi_service"),
    ServiceBinding(name="learning", container_attr="learning_service"),
    ServiceBinding(name="lesson", container_attr="lesson_service"),
    ServiceBinding(name="marketplace", container_attr="marketplace_service"),
    ServiceBinding(name="mission", container_attr="mission_service"),
    ServiceBinding(name="moderation", container_attr="moderation_service"),
    ServiceBinding(name="onboarding", container_attr="onboarding_service"),
    ServiceBinding(name="prompt_engagement", container_attr="prompt_engagement_service"),
    ServiceBinding(name="prompt", container_attr="prompt_service"),
    ServiceBinding(name="recommendation", container_attr="recommendation_service"),
    ServiceBinding(name="scenario", container_attr="scenario_service"),
    ServiceBinding(name="scenario_demo_run", container_attr="scenario_demo_run_service"),
    ServiceBinding(name="scenario_game", container_attr="scenario_game_service"),
    ServiceBinding(name="scenario_platform", container_attr="scenario_platform_service"),
    ServiceBinding(name="saved_prompt", container_attr="saved_prompt_service"),
    ServiceBinding(name="store", container_attr="store_service"),
    ServiceBinding(name="submission", container_attr="submission_service"),
    ServiceBinding(name="user", container_attr="user_service"),
    ServiceBinding(name="wallet", container_attr="wallet_service"),
)
