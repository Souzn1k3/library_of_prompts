from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.repository.prompt_repository_base_mixin import PromptRepositoryBaseMixin
from app.modules.catalog.repository.prompt_repository_read_mixin import PromptRepositoryReadMixin
from app.modules.catalog.repository.prompt_repository_taxonomy_mixin import PromptRepositoryTaxonomyMixin
from app.modules.catalog.repository.prompt_repository_write_mixin import PromptRepositoryWriteMixin


class PromptRepository(
    PromptRepositoryWriteMixin,
    PromptRepositoryTaxonomyMixin,
    PromptRepositoryReadMixin,
    PromptRepositoryBaseMixin,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
