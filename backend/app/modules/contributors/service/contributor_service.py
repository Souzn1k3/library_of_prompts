from app.modules.contributors.repository.contributor_repository import ContributorRepository
from app.modules.contributors.service.contributor_guardrails_mixin import ContributorGuardrailsMixin
from app.modules.contributors.service.contributor_profile_mixin import ContributorProfileMixin
from app.modules.identity.repository.user_repository import UserRepository
from app.modules.marketplace.service.marketplace_service import MarketplaceService


class ContributorService(ContributorGuardrailsMixin, ContributorProfileMixin):
    def __init__(
        self,
        repo: ContributorRepository,
        users: UserRepository,
        marketplace: MarketplaceService | None = None,
    ) -> None:
        self._repo = repo
        self._users = users
        self._marketplace = marketplace
